# -*- coding: utf-8 -*-

import uvicorn
import hashlib
import filetype
import os.path
import config
from loguru import logger
from typing import Optional, List
from pydantic import BaseModel, validator
from db.dao import image_insert, image_get_by_md5,\
        image_search
from utils.http_client import async_http_get
from fastapi import FastAPI, APIRouter, HTTPException, Request
from libimgsmlr import img2pattern, pattern2signature, shuffle_pattern
from fastapi.responses import HTMLResponse

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

    img = resp.content
    kind = filetype.guess(img)
    if not kind:
        response.code = 400
        response.msg = "not a valid file"
        return response

    md5 = hashlib.md5(img).hexdigest()
    image = await image_get_by_md5(md5)
    if image:
        response.code = 400
        response.msg = "image file already exists"
        return response

    try:
        pattern = img2pattern(img)
    except ValueError as err:
        response.code = 400
        response.msg = str(err)
        return response

    signature = pattern2signature(pattern)
    pattern2 = shuffle_pattern(pattern)

    image = {
        "url": req.url,
        "dataId": req.dataId,
        "md5": md5,
        "pattern": pattern2.as_array(),
        "signature": signature,
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
    resp, req_debug = await async_http_get(req.url)
    if resp.status_code != 200:
        response.code = 400
        response.msg = "fetch url failed, status: %s" % (resp.status_code)
        return response

    img = resp.content
    kind = filetype.guess(img)
    if not kind:
        response.code = 400
        response.msg = "not a valid file"
        return response

    try:
        pattern = img2pattern(img)
    except ValueError as err:
        response.code = 400
        response.msg = str(err)
        return response

    signature = pattern2signature(pattern)
    pattern2 = shuffle_pattern(pattern)

    limit = req.limit or config.SEARCH_LIMIT
    simr_threshold = req.threshold or config.SEARCH_SIMR_THRESHOLD
    images = await image_search(pattern2.as_array(), signature, limit=limit, simr_threshold=simr_threshold)
    data = SearchResponseData.parse_obj({"images": images, "threshold": simr_threshold})
    response.code = 200
    response.msg = "OK"
    response.data = data
    return response


app = FastAPI()

app.include_router(api_router, prefix="/imgsmlr")

def main():
    uvicorn.run(app, host=config.HOST, port=config.PORT)


if __name__ == "__main__":
    main()
