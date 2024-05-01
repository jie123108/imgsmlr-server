
import asyncio
import logging
import config
from copy import deepcopy
from db.model import Image, signature_preprocess, pattern_preprocess
from sqlalchemy import create_engine, text, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from retry import retry



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
        await session.commit()

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


### image
async def image_insert(image_dict):
    image = Image(**image_dict)
    await async_session_add(image)

async def image_get_by_id(id):
    obj = await async_session_query_one(Image, {"id": id})
    return obj

async def image_get_by_md5(md5):
    obj = await async_session_query_one(Image, {"md5": md5})
    return obj


#### 使用pattern,signature搜索接口(操作符: <->)
async def image_search_by_imgsmlr(pattern, signature, limit=50, simr_threshold=4.0):
    async with AsyncSession(async_engine) as session:
        # 字段需要跟 ImageResult 对应上.
        SQL_FORMAT = """SELECT * FROM (SELECT id,url,data_id,md5,remark,meta, pattern <-> '%s' AS simr 
FROM image ORDER BY signature <-> '%s' LIMIT %d) x WHERE x.simr < %.3f ORDER BY x.simr ASC LIMIT %d"""
        sql = SQL_FORMAT % (
            pattern_preprocess(pattern), signature_preprocess(signature),
            limit * 3, simr_threshold, limit)
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
                "simr": round(item[6], 6),
            }
            objs.append(obj)
        return objs

async def image_search_by_clip(embedding, limit=50, simr_threshold=4.0):
    async with AsyncSession(async_engine) as session:
        if limit > 40:
            await session.execute("SET hnsw.ef_search = %d" % (limit))
        # 字段需要跟 ImageResult 对应上.
        SQL_FORMAT = """SELECT * FROM (SELECT id,url,data_id,md5,remark,meta, round((clip <=> '%s')::numeric, 4) AS simr
FROM image ORDER BY clip <=> '%s' LIMIT %d) x WHERE x.simr < %.3f"""
        sql = SQL_FORMAT % ( embedding, embedding, limit, simr_threshold)

        # logging.warning("Searching SQL: %s" % sql.replace("\n", " "))
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
                "simr": round(item[6], 6),
            }
            objs.append(obj)
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
        "url": url, "signature": signature, "pattern": pattern,
        "remark": remark, "meta": meta, "dataId": "data.test." + str(time.time())
    }
    await image_insert(image)

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(async_test_main())