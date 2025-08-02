from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from db.dao import (
    dataset_insert, dataset_update, dataset_delete, dataset_get_by_id, dataset_get_by_name, dataset_list
)

class DatasetAddRequest(BaseModel):
    name: str
    description: Optional[str] = None
    meta: Optional[dict] = None

class DatasetAddResponseData(BaseModel):
    id: int

class DatasetAddResponse(BaseModel):
    code: int = 200
    msg: str = "OK"
    data: Optional[DatasetAddResponseData] = None

class DatasetUpdateRequest(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    meta: Optional[dict] = None

class DatasetUpdateResponse(BaseModel):
    code: int = 200
    msg: str = "OK"

class DatasetDeleteRequest(BaseModel):
    id: int

class DatasetDeleteResponse(BaseModel):
    code: int = 200
    msg: str = "OK"

class DatasetInfo(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    meta: Optional[dict] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

class DatasetListResponseData(BaseModel):
    datasets: List[DatasetInfo]

class DatasetListResponse(BaseModel):
    code: int = 200
    msg: str = "OK"
    data: Optional[DatasetListResponseData] = None

dataset_router = APIRouter()

@dataset_router.post("/dataset/add", response_model=DatasetAddResponse)
async def add_dataset(req: DatasetAddRequest):
    exist = await dataset_get_by_name(req.name)
    if exist:
        return DatasetAddResponse(code=400, msg="Dataset name already exists")
    new_dataset = await dataset_insert({
        "name": req.name,
        "description": req.description,
        "meta": req.meta
    })
    id = new_dataset["id"]
    return DatasetAddResponse(data=DatasetAddResponseData(id=id))

@dataset_router.post("/dataset/update", response_model=DatasetUpdateResponse)
async def update_dataset(req: DatasetUpdateRequest):
    dataset = await dataset_get_by_id(req.id)
    if not dataset:
        return DatasetUpdateResponse(code=404, msg="Dataset not found")
    update_dict = {}
    if req.name:
        update_dict["name"] = req.name
    if req.description:
        update_dict["description"] = req.description
    if req.meta:
        update_dict["meta"] = req.meta
    await dataset_update(req.id, update_dict)
    return DatasetUpdateResponse()

@dataset_router.post("/dataset/delete", response_model=DatasetDeleteResponse)
async def delete_dataset(req: DatasetDeleteRequest):
    dataset = await dataset_get_by_id(req.id)
    if not dataset:
        return DatasetDeleteResponse(code=404, msg="Dataset not found")
    await dataset_delete(req.id)
    return DatasetDeleteResponse()

@dataset_router.get("/dataset/list", response_model=DatasetListResponse)
async def list_datasets():
    datasets = await dataset_list()
    result = []
    for ds in datasets:
        result.append(DatasetInfo(
            id=ds["id"],
            name=ds["name"],
            description=ds.get("description"),
            meta=ds.get("meta"),
            createdAt=ds.get("createdAt"),
            updatedAt=ds.get("updated_at")
        ))
    return DatasetListResponse(data=DatasetListResponseData(datasets=result)) 