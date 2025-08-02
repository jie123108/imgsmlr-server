
import asyncio
import logging
import config
from copy import deepcopy
from db.model import Image, Dataset, signature_preprocess, pattern_preprocess
from sqlalchemy import create_engine, text, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession



# https://docs.sqlalchemy.org/en/14/dialects/postgresql.html
SQL_URL = config.POSTGRESQL_URL
sql_debug = config.SQL_DEBUG
async_engine = create_async_engine(SQL_URL, echo=sql_debug, pool_size=10, max_overflow=10,  pool_recycle=1800)

## data access method

def query_one(session, model, args):
    obj = session.query(model).filter_by(**args).order_by(model.id.desc()).first()
    return obj

def query_many(session, model, args):
    objs = session.query(model).filter_by(**args).order_by(model.id.desc()).limit(50).all()
    return objs

def update_one(session, model, query, update):
    obj = session.query(model).filter_by(**query).order_by(model.id.desc()).first()
    if obj:
        for key, value in update.items():
            setattr(obj, key, value)

async def async_session_add(obj):
    async with AsyncSession(async_engine) as session:
        async with session.begin():
            session.add(obj)
            await session.flush()  # 刷新以获取数据库生成的字段
            await session.refresh(obj)  # 刷新对象以获取最新数据
            # 在会话关闭前获取对象的字典表示
            obj_dict = obj.as_dict()
        await session.commit()
        return obj_dict

async def async_session_update_one(Model, query, update):
    async with AsyncSession(async_engine) as session:
        async with session.begin():
            await session.run_sync(update_one, Model, query, update)
        await session.commit()

async def async_session_query_one(Model, query):
    async with AsyncSession(async_engine) as session:
        obj = await session.run_sync(query_one, Model, query)
        if obj:
            obj = obj.as_dict()
        return obj

async def async_session_query_many(Model, query):
    async with AsyncSession(async_engine) as session:
        objs = await session.run_sync(query_many, Model, query)
        if objs:
            objs = [obj.as_dict() for obj in objs]
        return objs



### dataset
async def dataset_insert(dataset_dict):
    # 移除时间戳设置，使用模型的默认值
    dataset = Dataset(**dataset_dict)
    result = await async_session_add(dataset)
    return result

async def dataset_get_by_id(id):
    obj = await async_session_query_one(Dataset, {"id": id})
    return obj

async def dataset_get_by_name(name):
    obj = await async_session_query_one(Dataset, {"name": name})
    return obj

async def dataset_list():
    obj = await async_session_query_many(Dataset, {})
    return obj

async def dataset_update(id, update_dict):
    # 移除时间戳设置，使用模型的onupdate默认值
    await async_session_update_one(Dataset, {"id": id}, update_dict)

async def dataset_delete(id):
    async with AsyncSession(async_engine) as session:
        async with session.begin():
            dataset = await session.run_sync(query_one, Dataset, {"id": id})
            if dataset:
                await session.run_sync(lambda sess: sess.delete(dataset))
        await session.commit()

### image
async def image_insert(image_dict):
    image = Image(**image_dict)
    await async_session_add(image)

async def image_get_by_id(id):
    obj = await async_session_query_one(Image, {"id": id})
    return obj

async def image_get_by_md5(md5, datasetId=None):
    query = {"md5": md5}
    if datasetId is not None:
        query["datasetId"] = datasetId
    obj = await async_session_query_one(Image, query)
    return obj


#### 使用pattern,signature搜索接口(操作符: <->)
async def image_search_by_imgsmlr(pattern, signature, datasetIds=None, limit=50, simr_threshold=4.0):
    async with AsyncSession(async_engine) as session:
        # 字段需要跟 ImageResult 对应上.
        base_sql = """
        SELECT * FROM (
            SELECT id, url, data_id, md5, remark, meta, tags, dataset_id, created_at, updated_at, pattern <-> :pattern AS simr
            FROM image
            {dataset_filter}
            ORDER BY signature <-> :signature
            LIMIT :limit3
        ) x
        WHERE x.simr < :simr_threshold
        ORDER BY x.simr ASC
        LIMIT :limit
        """
        params = {
            "pattern": pattern_preprocess(pattern),
            "signature": signature_preprocess(signature),
            "limit3": limit * 3,
            "simr_threshold": simr_threshold,
            "limit": limit
        }
        if datasetIds:
            dataset_filter = "WHERE dataset_id = ANY(:datasetIds)"
            params["datasetIds"] = list(datasetIds)
        else:
            dataset_filter = ""
        sql = base_sql.format(dataset_filter=dataset_filter)
        cursor = await session.execute(text(sql), params)
        objs = []
        for item in cursor:
            obj = {
                "id": item[0],
                "url": item[1],
                "dataId": item[2],
                "md5": item[3],
                "remark": item[4],
                "meta": item[5],
                "tags": item[6],
                "datasetId": item[7],
                "createdAt": item[8],
                "updatedAt": item[9],
                "simr": round(item[10], 6),
            }
            objs.append(obj)
        return objs

async def _image_search_by_embedding(embedding, field_name, limit=50, simr_threshold=4.0, datasetIds=None):
    """
    通用的向量搜索函数，支持不同的embedding字段
    :param embedding: 向量embedding
    :param field_name: 要搜索的字段名 (如 'clip' 或 'siglip')
    :param limit: 返回结果数量限制
    :param simr_threshold: 相似度阈值
    :param datasetIds: 数据集ID列表
    :return: 搜索结果列表
    """
    async with AsyncSession(async_engine) as session:
        if limit > 40:
            await session.execute(text("SET hnsw.ef_search = %d" % (limit)))
        # 字段需要跟 ImageResult 对应上.
        base_sql = """SELECT * FROM (SELECT id,url,data_id,md5,remark,meta, tags, dataset_id, created_at, updated_at, round((%s <=> '%s')::numeric, 4) AS simr
FROM image""" % (field_name, embedding)
        
        where_conditions = []
        # 添加embedding字段不为空的条件
        where_conditions.append("%s IS NOT NULL" % field_name)
        
        if datasetIds:
            where_conditions.append("dataset_id IN (%s)" % ','.join([str(x) for x in datasetIds]))
        
        if where_conditions:
            base_sql += " WHERE " + " AND ".join(where_conditions)
        
        sql = base_sql + " ORDER BY %s <=> '%s' LIMIT %d) x WHERE x.simr < %.3f" % (field_name, embedding, limit, simr_threshold)

        logging.warning("Searching SQL: %s" % sql.replace("\n", " "))
        cursor = await session.execute(text(sql))
        objs = []
        for item in cursor:
            obj = {
                "id": item[0],
                "url": item[1],
                "dataId": item[2],
                "md5": item[3],
                "remark": item[4],
                "meta": item[5],
                "tags": item[6],
                "datasetId": item[7],
                "createdAt": item[8],
                "updatedAt": item[9],
                "simr": round(item[10], 6),
            }
            objs.append(obj)
        return objs

async def image_search_by_clip(embedding, limit=50, simr_threshold=4.0, datasetIds=None):
    """使用CLIP embedding进行图像搜索"""
    return await _image_search_by_embedding(embedding, "clip", limit, simr_threshold, datasetIds)

async def image_search_by_siglip(embedding, limit=50, simr_threshold=4.0, datasetIds=None):
    """使用SigLIP embedding进行图像搜索"""
    return await _image_search_by_embedding(embedding, "siglip", limit, simr_threshold, datasetIds)


async def image_search_by_dataId(dataId, datasetIds=None):
    query = {"dataId": dataId}
    if datasetIds:
        query["dataset_id"] = datasetIds
    objs = await async_session_query_many(Image, query)
    return objs

async def async_test_main():
    import time
    import json
    import random

    url = "http://localhost:8850/test.jpeg"
    signature = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0,1.1,1.2,1.3,1.4,1.5,1.6]
    remark = "说明"
    meta = {"OK": "什么东西"}
    pattern = []
    for i in range(64):
        arr = []
        for j in range(64):
            arr.append(random.random())
        pattern.append(arr)

    image = {
        "url": url, "signature": signature, "pattern": pattern, "tags": ["test", "tag"],
        "remark": remark, "meta": meta, "dataId": "data.test." + str(time.time())
    }
    await image_insert(image)

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(async_test_main())
