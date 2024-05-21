# -*- coding: utf-8 -*-

import uvicorn
import hashlib
import filetype
import os.path
import config
import time
import io
from loguru import logger
from typing import Optional, List
from pydantic import BaseModel, validator
from db.dao import image_insert, image_get_by_md5,\
        image_search_by_imgsmlr, image_search_by_clip
from utils.http_client import async_http_get
from fastapi import FastAPI, APIRouter, HTTPException, Request
from libimgsmlr import img2pattern, pattern2signature, shuffle_pattern
from similarities import ClipModule

from fastapi.responses import HTMLResponse
from PIL import Image

logger.info("------------------------- init clip model ---------------------")
clipModel = ClipModule("OFA-Sys/chinese-clip-vit-base-patch16")
logger.info("--------------------------init clip model finished ------------")

def emb_result_wrapper(embedding):
    # embedding = list(embedding[0])
    embedding = [round(value, 6) for value in embedding]
    return embedding

class SmlrMgrAddRequest(BaseModel):
    url: str
    dataId: Optional[str]
    remark: Optional[str]
    meta: Optional[dict]

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
    limit: Optional[int]

class ImageResult(BaseModel):
    id: Optional[int]
    url: str
    dataId: Optional[str]
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


api_router = APIRouter()

@api_router.get("/")
async def index():
    fullfilename = "%s/tmpl/index.html" % (os.path.dirname(os.path.abspath(__file__)))
    html_content = open(fullfilename, "r").read()
    return HTMLResponse(content=html_content, status_code=200)

# curl http://127.0.0.1:8140/imgsmlr/mgr/add -d '{"url": "http://192.168.31.100:8080/DSCF1386.JPG"}'
@api_router.post("/mgr/add", response_model=SmlrMgrAddResponse)
async def mgr_add(req: SmlrMgrAddRequest):
    response = SmlrMgrAddResponse()
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

    md5 = hashlib.md5(img_data).hexdigest()
    image = await image_get_by_md5(md5)
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
        clip = emb_result_wrapper(clipModel.encode(img, normalize_embeddings=True))

        image = {
            "url": req.url,
            "dataId": req.dataId,
            "md5": md5,
            "pattern": pattern2.as_array(),
            "signature": signature,
            "phash": None,
            "clip": clip,
            "remark": req.remark,
            "meta": req.meta,
        }
        await image_insert(image)
    response.code = 200
    response.msg = "OK"

    return response

# curl http://127.0.0.1:8140/imgsmlr/search -d '{"url": "http://192.168.31.100:8080/DSCF1386.JPG"}'
@api_router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    response = SearchResponse()
    limit = req.limit or config.SEARCH_LIMIT
    matchType = req.matchType or 'clip'
    img_data = None
    search_data = None
    if matchType == "cliptext":
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
        try:
            pattern = img2pattern(img_data)
        except ValueError as err:
            response.code = 400
            response.msg = str(err)
            return response
        signature = pattern2signature(pattern)
        pattern2 = shuffle_pattern(pattern)
        te_embedding = time.time()
        simr_threshold = req.threshold or config.SEARCH_SIMR_THRESHOLD
        images = await image_search_by_imgsmlr(pattern2.as_array(), signature, limit=limit, simr_threshold=simr_threshold)
    elif matchType == 'clip':
        with io.BytesIO(img_data) as bio:
            img = Image.open(bio)
            clip = emb_result_wrapper(clipModel.encode(img, normalize_embeddings=True))
            te_embedding = time.time()
            simr_threshold = req.threshold or config.SEARCH_SIMR_THRESHOLD
            images = await image_search_by_clip(clip, limit=limit, simr_threshold=simr_threshold)
    elif matchType == 'cliptext':
        clip = emb_result_wrapper(clipModel.encode(search_data, normalize_embeddings=True))
        te_embedding = time.time()
        simr_threshold = req.threshold or config.SEARCH_SIMR_THRESHOLD
        images = await image_search_by_clip(clip, limit=limit, simr_threshold=simr_threshold)
    te = time.time()
    duration = te - ts
    duration_embedding = te_embedding - ts
    duration_search = te - te_embedding
    logger.info("img search by '%s' duration %.3f embedding: %.3f search: %.3f. '%s' found %d images" % (
            matchType, duration, duration_embedding, duration_search, req.url, len(images)))

    data = SearchResponseData.parse_obj({"images": images, "threshold": simr_threshold})
    response.code = 200
    response.msg = "OK"
    response.data = data
    return response


app = FastAPI()

app.include_router(api_router, prefix="/imgsmlr")



@app.on_event("startup")
async def on_startup():
    pass

def main():
    uvicorn.run(app, loop="uvloop", host=config.HOST, port=config.PORT)

if __name__ == "__main__":
    main()
