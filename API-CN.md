# ImgSmlr 图像相似度检索服务 API 文档

# 目录

- [目录](#目录)
  - [协议说明](#协议说明)
  - [数据模型](#数据模型)
  - [数据集管理](#数据集管理)
  - [图像管理](#图像管理)

## 协议说明

* ImgSmlr 接口使用 `HTTP` + `JSON` 进行通信
* `POST`, `PUT`, `DELETE` 请求均使用 `Request Body` 传递参数，格式为 JSON
* 请求和响应的 `Content-Type` 均为 `application/json`
* 响应体包含统一的结构，后续文档只列出 `code`, `msg` 和 `data` 部分

### 响应体通用结构示例

```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    // 成功时返回的数据
  }
}
```

### 响应字段通用说明

字段 | 类型 | 必需 | 描述
-------|-------|------|-----
code | integer | 是 | 响应状态码，200表示成功，400表示客户端错误，500表示服务器错误
msg | string | 是 | 响应消息，"OK"表示成功，错误时为具体错误信息
data | object | 否 | 成功时返回的具体数据

### 常见错误码

* `400` - 请求参数错误或业务逻辑错误
* `404` - 资源不存在
* `500` - 服务器内部错误

## 数据模型

### DatasetInfo - 数据集信息

字段 | 类型 | 必需 | 描述
-------|-------|------|-----
id | integer | 是 | 数据集ID
name | string | 是 | 数据集名称
description | string | 否 | 数据集描述
meta | object | 否 | 数据集元数据
createdAt | datetime | 否 | 创建时间
updatedAt | datetime | 否 | 更新时间

### ImageInfo - 图像信息

字段 | 类型 | 必需 | 描述
-------|-------|------|-----
id | integer | 是 | 图像记录ID
url | string | 是 | 图像URL地址
md5 | string | 否 | 图像MD5哈希值
dataId | string | 否 | 用户自定义数据ID
datasetId | integer | 是 | 所属数据集ID
remark | string | 否 | 备注信息
meta | object | 否 | 元数据信息
tags | string[] | 否 | 标签列表
pattern | float[][] | 否 | 图像模式特征
signature | float[] | 否 | 图像签名特征
phash | float[] | 否 | 感知哈希特征
clip | float[] | 否 | CLIP模型特征向量
siglip | float[] | 否 | SigLIP模型特征向量
createdAt | datetime | 否 | 创建时间
updatedAt | datetime | 否 | 更新时间

### ImageResult - 搜索结果图像

字段 | 类型 | 必需 | 描述
-------|-------|------|-----
id | integer | 否 | 图像记录ID
url | string | 是 | 图像URL地址
dataId | string | 否 | 用户自定义数据ID
datasetId | integer | 否 | 所属数据集ID
md5 | string | 否 | 图像MD5哈希值
remark | string | 否 | 备注信息
meta | object | 否 | 元数据信息
simr | float | 否 | 相似度分数

## 数据集管理

### 添加数据集

#### 方法: POST
#### URL: `/imgsmlr/dataset/add`
#### 请求参数

字段 | 类型 | 必需 | 描述
-------|-------|------|-----
name | string | 是 | 数据集名称，不能重复
description | string | 否 | 数据集描述信息
meta | object | 否 | 数据集元数据

#### 响应数据

* data:

字段 | 类型 | 必需 | 描述
-------|-------|------|-----
id | integer | 是 | 新创建的数据集ID

* 错误信息:
  * `Dataset name already exists` - 数据集名称已存在

#### 示例

* 请求

```bash
curl -X POST http://127.0.0.1:8140/imgsmlr/dataset/add \
-H "Content-Type: application/json" \
-d '{
  "name": "test_dataset",
  "description": "测试数据集",
  "meta": {"version": "1.0"}
}'
```

* 响应

```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "id": 1
  }
}
```

### 更新数据集

#### 方法: POST
#### URL: `/imgsmlr/dataset/update`
#### 请求参数

字段 | 类型 | 必需 | 描述
-------|-------|------|-----
id | integer | 是 | 数据集ID
name | string | 否 | 数据集名称
description | string | 否 | 数据集描述信息
meta | object | 否 | 数据集元数据

#### 响应数据

更新成功时返回空的data字段

* 错误信息:
  * `Dataset not found` - 数据集不存在

#### 示例

* 请求

```bash
curl -X POST http://127.0.0.1:8140/imgsmlr/dataset/update \
-H "Content-Type: application/json" \
-d '{
  "id": 1,
  "description": "更新后的数据集描述"
}'
```

* 响应

```json
{
  "code": 200,
  "msg": "OK"
}
```

### 删除数据集

#### 方法: POST
#### URL: `/imgsmlr/dataset/delete`
#### 请求参数

字段 | 类型 | 必需 | 描述
-------|-------|------|-----
id | integer | 是 | 要删除的数据集ID

#### 响应数据

删除成功时返回空的data字段

* 错误信息:
  * `Dataset not found` - 数据集不存在

#### 示例

* 请求

```bash
curl -X POST http://127.0.0.1:8140/imgsmlr/dataset/delete \
-H "Content-Type: application/json" \
-d '{
  "id": 1
}'
```

* 响应

```json
{
  "code": 200,
  "msg": "OK"
}
```

### 获取数据集列表

#### 方法: GET
#### URL: `/imgsmlr/dataset/list`
#### 请求参数

无

#### 响应数据

* data:

字段 | 类型 | 必需 | 描述
-------|-------|------|-----
datasets | [DatasetInfo](#datasetinfo---数据集信息)[] | 是 | 数据集信息列表

#### 示例

* 请求

```bash
curl -X GET http://127.0.0.1:8140/imgsmlr/dataset/list
```

* 响应

```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "datasets": [
      {
        "id": 1,
        "name": "test_dataset",
        "description": "测试数据集",
        "meta": {"version": "1.0"},
        "createdAt": "2024-01-01T10:00:00",
        "updatedAt": "2024-01-01T10:00:00"
      }
    ]
  }
}
```

## 图像管理

### 添加图像

向指定数据集添加图像，系统会自动提取图像特征并建立索引。

#### 方法: POST
#### URL: `/imgsmlr/image/add`
#### 请求参数

字段 | 类型 | 必需 | 描述
-------|-------|------|-----
url | string | 是 | 图像URL地址，必须以http://或https://开头
datasetId | integer | 是 | 目标数据集ID
dataId | string | 否 | 用户自定义数据ID
remark | string | 否 | 备注信息
meta | object | 否 | 元数据信息
tags | string[] | 否 | 标签列表

#### 响应数据

* data:

字段 | 类型 | 必需 | 描述
-------|-------|------|-----
id | integer | 否 | 新添加的图像记录ID

* 错误信息:
  * `Invalid URL format. URL must start with http:// or https://` - URL格式错误
  * `fetch url failed, status: xxx` - 获取图像失败
  * `not a valid file` - 不是有效的图像文件
  * `image file already exists` - 图像文件已存在（基于MD5判断）
  * `model not ready` - 模型未初始化完成

#### 示例

* 请求

```bash
curl -X POST http://127.0.0.1:8140/imgsmlr/image/add \
-H "Content-Type: application/json" \
-d '{
  "url": "https://example.com/image.jpg",
  "datasetId": 1,
  "dataId": "img_001",
  "remark": "测试图像",
  "meta": {"category": "demo"},
  "tags": ["test", "demo"]
}'
```

* 响应

```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "id": 101
  }
}
```

### 搜索相似图像

根据输入图像或文本搜索相似的图像。

#### 方法: POST
#### URL: `/imgsmlr/image/search`
#### 请求参数

字段 | 类型 | 必需 | 描述
-------|-------|------|-----
url | string | 是 | 查询图像URL或文本内容（根据matchType决定）
matchType | string | 否 | 匹配类型：`imgsmlr`、`clip`、`siglip`、`cliptext`、`dataId`，默认为`clip`
threshold | float | 否 | 相似度阈值，默认使用配置值
datasetIds | integer[] | 否 | 限制搜索的数据集ID列表，空表示搜索所有数据集
limit | integer | 否 | 返回结果数量限制，默认使用配置值

#### 匹配类型说明

* `imgsmlr` - 基于imgsmlr算法的图像特征匹配
* `clip` - 基于CLIP模型的图像特征匹配
* `siglip` - 基于SigLIP模型的图像特征匹配  
* `cliptext` - 基于CLIP模型的文本到图像匹配（url字段传入文本内容）
* `dataId` - 基于dataId的精确匹配（url字段传入dataId）

#### 响应数据

* data:

字段 | 类型 | 必需 | 描述
-------|-------|------|-----
images | [ImageResult](#imageresult---搜索结果图像)[] | 是 | 相似图像列表，按相似度降序排列
threshold | float | 是 | 实际使用的相似度阈值

* 错误信息:
  * `fetch url failed, status: xxx` - 获取查询图像失败  
  * `not a valid file` - 不是有效的图像文件
  * `xxx model not initialized` - 指定模型未初始化

#### 示例

* 请求

```bash
curl -X POST http://127.0.0.1:8140/imgsmlr/image/search \
-H "Content-Type: application/json" \
-d '{
  "url": "https://example.com/query.jpg",
  "matchType": "clip",
  "threshold": 0.8,
  "datasetIds": [1, 2],
  "limit": 10
}'
```

* 响应

```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "images": [
      {
        "id": 101,
        "url": "https://example.com/similar1.jpg",
        "dataId": "img_001",
        "datasetId": 1,
        "md5": "abc123def456",
        "remark": "相似图像1",
        "meta": {"category": "demo"},
        "simr": 0.95
      },
      {
        "id": 102,
        "url": "https://example.com/similar2.jpg",
        "dataId": "img_002", 
        "datasetId": 1,
        "md5": "def456ghi789",
        "remark": "相似图像2",
        "meta": {"category": "demo"},
        "simr": 0.88
      }
    ],
    "threshold": 0.8
  }
}
```

### 查询图像信息

根据dataId查询图像的详细信息。

#### 方法: GET  
#### URL: `/imgsmlr/image/info`
#### 请求参数

参数 | 类型 | 必需 | 描述
-------|-------|------|-----
dataId | string | 是 | 用户自定义数据ID
tag | string | 否 | 标签过滤（当前版本暂未实现）

#### 响应数据

* data:

字段 | 类型 | 必需 | 描述
-------|-------|------|-----
images | [ImageInfo](#imageinfo---图像信息)[] | 是 | 匹配的图像信息列表

#### 示例

* 请求 

```bash
curl -X GET "http://127.0.0.1:8140/imgsmlr/image/info?dataId=img_001"
```

* 响应

```json
{
  "code": 200,
  "msg": "OK", 
  "data": {
    "images": [
      {
        "id": 101,
        "url": "https://example.com/image.jpg",
        "md5": "abc123def456",
        "dataId": "img_001",
        "datasetId": 1,
        "remark": "测试图像",
        "meta": {"category": "demo"},
        "tags": ["test", "demo"],
        "pattern": [[0.1, 0.2], [0.3, 0.4]],
        "signature": [0.5, 0.6, 0.7],
        "clip": [0.1, 0.2, 0.3],
        "siglip": [0.4, 0.5, 0.6],
        "createdAt": "2024-01-01T10:00:00",
        "updatedAt": "2024-01-01T10:00:00"
      }
    ]
  }
}
```

---

## 使用建议

1. **数据集管理**: 建议按业务场景创建不同的数据集，便于管理和搜索范围控制
2. **图像添加**: 确保图像URL可访问，系统会自动去重（基于MD5）
3. **相似度搜索**: 
   - `clip` 模式适用于一般图像相似度搜索
   - `imgsmlr` 模式适用于快速的基础特征匹配
   - `cliptext` 模式支持文本描述搜索图像
4. **性能优化**: 合理设置threshold和limit参数，避免返回过多结果影响性能
5. **错误处理**: 请注意检查响应的code字段，并根据msg字段进行错误处理

[回到目录](#目录)
