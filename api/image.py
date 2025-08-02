# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Request
from typing import Optional, List
from pydantic import BaseModel
from db.dao import *
from utils.http_client import async_http_get
from libimgsmlr import img2pattern, pattern2signature, shuffle_pattern
from utils.url_replace import url_replace
from PIL import Image
import filetype
import config
import time
import io
from datetime import datetime, timezone
from api.model import is_model_ready, encode_image, encode_image_all, encode_text
from loguru import logger

def emb_result_wrapper(embedding):
    embedding = [round(value, 6) for value in embedding]
    return embedding

class SmlrMgrAddRequest(BaseModel): 
    url: str
    datasetId: int
    dataId: Optional[str]
    remark: Optional[str]
    meta: Optional[dict]
    tags: Optional[List[str]]

class MgrAddResponseData(BaseModel):
    id: Optional[int]

class SmlrMgrAddResponse(BaseModel):
    code: int = 200
    msg: str = "OK"
    data: Optional[MgrAddResponseData]

class SearchRequest(BaseModel):
    url: str
    matchType: Optional[str]
    threshold: Optional[float]
    datasetIds: Optional[List[int]]
    limit: Optional[int]

class ImageResult(BaseModel):
    id: Optional[int]
    url: str
    dataId: Optional[str]
    datasetId: Optional[int]
    md5: Optional[str]
    remark: Optional[str]
    meta: Optional[dict]
    simr: Optional[float] # 相似度

class SearchResponseData(BaseModel):
    images: Optional[List[ImageResult]]
    threshold: Optional[float]

class SearchResponse(BaseModel):
    code: int = 200
    msg: str = "OK"
    data: Optional[SearchResponseData]

class ImageInfo(BaseModel):
    id: int
    url: str
    md5: Optional[str]
    pattern: Optional[List[List[float]]]
    signature: Optional[List[float]]
    phash: Optional[List[float]]
    clip: Optional[List[float]]
    siglip: Optional[List[float]]
    remark: Optional[str]
    dataId: Optional[str]
    datasetId: Optional[int]
    createdAt: Optional[datetime]
    updatedAt: Optional[datetime]
    tags: Optional[List[str]]
    meta: Optional[dict]

class QueryImageInfoResponseData(BaseModel):
    images: Optional[List[ImageInfo]]

class QueryImageInfoResponse(BaseModel):
    code: int = 200
    msg: str = "OK"
    data: Optional[QueryImageInfoResponseData]

image_router = APIRouter()

@image_router.post("/image/add", response_model=SmlrMgrAddResponse)
async def mgr_add(req: SmlrMgrAddRequest):
    response = SmlrMgrAddResponse()
    if not is_model_ready():
        response.code = 400
        response.msg = "model not ready"
        return response
    if not req.url or not (req.url.startswith("http://") or req.url.startswith("https://")):
        response.code = 400
        response.msg = "Invalid URL format. URL must start with http:// or https://"
        return response
    resp, req_debug = await async_http_get(req.url)
    if resp.status_code != 200:
        response.code = 400
        response.msg = "fetch url failed, status: %s" % (resp.status_code)
        return response
    img_data = resp.content
    kind = filetype.guess(img_data)
    if not kind:
        response.code = 400
        response.msg = "not a valid file"
        return response
    import hashlib
    md5 = hashlib.md5(img_data).hexdigest()
    datasetId = req.datasetId
    image = await image_get_by_md5(md5, datasetId)
    if image:
        response.code = 400
        response.msg = "image file already exists"
        return response


    try:
        pattern = img2pattern(img_data)
    except ValueError as err:
        response.code = 400
        response.msg = str(err)
        return response

    signature = pattern2signature(pattern)
    pattern2 = shuffle_pattern(pattern)

    with io.BytesIO(img_data) as bio:
        img = Image.open(bio)
        if img.mode not in ['RGB', 'RGBA']:
            img = img.convert('RGB')
        elif img.mode == 'RGBA':
            img = img.convert('RGB')
        encodings = encode_image_all(img)
    image = {
        "url": req.url,
        "dataId": req.dataId,
        "datasetId": datasetId,
        "md5": md5,
        'pattern': pattern2.as_array(),
        'signature': signature,
        "clip": encodings.get("clip"),
        "siglip": encodings.get("siglip"),
        "tags": req.tags,
        "remark": req.remark,
        "meta": req.meta,
        "createdAt": datetime.now(timezone.utc).replace(tzinfo=None),
        "updatedAt": datetime.now(timezone.utc).replace(tzinfo=None),
    }
    await image_insert(image)
    response.code = 200
    response.msg = "OK"
    return response

@image_router.post("/image/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    response = SearchResponse()
    limit = req.limit or config.SEARCH_LIMIT
    matchType = req.matchType or 'clip'
    datasetIds = getattr(req, "datasetIds", None) or []
    datasetId = getattr(req, "datasetId", None)
    if datasetId and datasetId not in datasetIds:
        datasetIds.append(datasetId)
    if matchType in ["cliptext", "dataId"]:
        search_data = req.url
    else:
        resp, req_debug = await async_http_get(req.url)
        if resp.status_code != 200:
            response.code = 400
            response.msg = "fetch url failed, status: %s" % (resp.status_code)
            return response
        img_data = resp.content
        kind = filetype.guess(img_data)
        if not kind:
            response.code = 400
            response.msg = "not a valid file"
            return response
    ts = time.time()
    if matchType == 'imgsmlr':
        pattern = img2pattern(img_data)
        signature = pattern2signature(pattern)
        pattern2 = shuffle_pattern(pattern)
        te_embedding = time.time()
        simr_threshold = req.threshold or config.SEARCH_SIMR_THRESHOLD
        images = await image_search_by_imgsmlr(pattern2.as_array(), signature, datasetIds=datasetIds, limit=limit, simr_threshold=simr_threshold)
    elif matchType in ['clip', 'siglip']:
        if not is_model_ready(matchType):
            response.code = 400
            response.msg = f"{matchType} model not initialized"
            return response
        with io.BytesIO(img_data) as bio:
            img = Image.open(bio)
            if img.mode not in ['RGB', 'RGBA']:
                img = img.convert('RGB')
            elif img.mode == 'RGBA':
                img = img.convert('RGB')
            embedding = encode_image(img, matchType)
            te_embedding = time.time()
            simr_threshold = req.threshold or config.SEARCH_SIMR_THRESHOLD
            if matchType == 'clip':
                images = await image_search_by_clip(embedding, limit=limit, simr_threshold=simr_threshold, datasetIds=datasetIds)
            else:
                images = await image_search_by_siglip(embedding, limit=limit, simr_threshold=simr_threshold, datasetIds=datasetIds)
    elif matchType == 'cliptext':
        clip = emb_result_wrapper(encode_text(search_data))
        te_embedding = time.time()
        simr_threshold = req.threshold or config.SEARCH_SIMR_THRESHOLD
        images = await image_search_by_clip(clip, limit=limit, simr_threshold=simr_threshold, datasetIds=datasetIds)
    elif matchType == 'dataId':
        te_embedding = time.time()
        simr_threshold = 0
        images = await image_search_by_dataId(search_data, datasetIds=datasetIds)
    te = time.time()
    duration = te - ts
    duration_embedding = te_embedding - ts
    duration_search = te - te_embedding
    logger.info("img search by '%s' duration %.3f embedding: %.3f search: %.3f. '%s' found %d images" % (
            matchType, duration, duration_embedding, duration_search, req.url, len(images)))
    url_replace(images)
    data = SearchResponseData.parse_obj({"images": images, "threshold": simr_threshold})
    response.code = 200
    response.msg = "OK"
    response.data = data
    return response

@image_router.get("/image/info", response_model=QueryImageInfoResponse)
async def image_info(dataId: str, tag: Optional[str]=""):
    response = QueryImageInfoResponse()
    images = await image_search_by_dataId(dataId)
    response.code = 200
    response.msg = "OK"
    response.data = QueryImageInfoResponseData.parse_obj({"images": images})
    return response