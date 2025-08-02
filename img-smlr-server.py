# -*- coding: utf-8 -*-

import uvicorn
import config
import os
import asyncio
from fastapi import FastAPI, APIRouter
from fastapi.responses import HTMLResponse
from api.dataset import dataset_router
from api.image import image_router
from api.model import init_model

app = FastAPI()

index_router = APIRouter()

@index_router.get("/", response_class=HTMLResponse)
async def index():
    fullfilename = "%s/tmpl/index.html" % (os.path.dirname(os.path.abspath(__file__)))
    html_content = open(fullfilename, "r").read()
    return HTMLResponse(content=html_content, status_code=200)

app.include_router(index_router, prefix="/imgsmlr")
app.include_router(image_router, prefix="/imgsmlr")
app.include_router(dataset_router, prefix="/imgsmlr")

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(init_model())

def main():
    uvicorn.run(app, loop="uvloop", host=config.HOST, port=config.PORT)

if __name__ == "__main__":
    main()
