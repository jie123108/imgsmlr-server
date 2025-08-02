# ImgSmlr Image Similarity Search Service API Documentation

# Table of Contents

- [Table of Contents](#table-of-contents)
  - [Protocol Description](#protocol-description)
  - [Data Models](#data-models)
  - [Dataset Management](#dataset-management)
  - [Image Management](#image-management)

## Protocol Description

* ImgSmlr interfaces use `HTTP` + `JSON` for communication
* `POST`, `PUT`, `DELETE` requests all use `Request Body` to pass parameters in JSON format
* Request and response `Content-Type` are both `application/json`
* Response body contains a unified structure, subsequent documentation only lists `code`, `msg` and `data` parts

### Response Body Common Structure Example

```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    // Data returned on success
  }
}
```

### Response Fields Common Description

Field | Type | Required | Description
-------|-------|------|-----
code | integer | Yes | Response status code, 200 indicates success, 400 indicates client error, 500 indicates server error
msg | string | Yes | Response message, "OK" indicates success, specific error message when error occurs
data | object | No | Specific data returned on success

### Common Error Codes

* `400` - Request parameter error or business logic error
* `404` - Resource not found
* `500` - Internal server error

## Data Models

### DatasetInfo - Dataset Information

Field | Type | Required | Description
-------|-------|------|-----
id | integer | Yes | Dataset ID
name | string | Yes | Dataset name
description | string | No | Dataset description
meta | object | No | Dataset metadata
createdAt | datetime | No | Creation time
updatedAt | datetime | No | Update time

### ImageInfo - Image Information

Field | Type | Required | Description
-------|-------|------|-----
id | integer | Yes | Image record ID
url | string | Yes | Image URL address
md5 | string | No | Image MD5 hash value
dataId | string | No | User-defined data ID
datasetId | integer | Yes | Dataset ID to which it belongs
remark | string | No | Remark information
meta | object | No | Metadata information
tags | string[] | No | Tag list
pattern | float[][] | No | Image pattern features
signature | float[] | No | Image signature features
phash | float[] | No | Perceptual hash features
clip | float[] | No | CLIP model feature vector
siglip | float[] | No | SigLIP model feature vector
createdAt | datetime | No | Creation time
updatedAt | datetime | No | Update time

### ImageResult - Search Result Image

Field | Type | Required | Description
-------|-------|------|-----
id | integer | No | Image record ID
url | string | Yes | Image URL address
dataId | string | No | User-defined data ID
datasetId | integer | No | Dataset ID to which it belongs
md5 | string | No | Image MD5 hash value
remark | string | No | Remark information
meta | object | No | Metadata information
simr | float | No | Similarity score

## Dataset Management

### Add Dataset

#### Method: POST
#### URL: `/imgsmlr/dataset/add`
#### Request Parameters

Field | Type | Required | Description
-------|-------|------|-----
name | string | Yes | Dataset name, must be unique
description | string | No | Dataset description information
meta | object | No | Dataset metadata

#### Response Data

* data:

Field | Type | Required | Description
-------|-------|------|-----
id | integer | Yes | ID of the newly created dataset

* Error Messages:
  * `Dataset name already exists` - Dataset name already exists

#### Example

* Request

```bash
curl -X POST http://127.0.0.1:8140/imgsmlr/dataset/add \
-H "Content-Type: application/json" \
-d '{
  "name": "test_dataset",
  "description": "Test dataset",
  "meta": {"version": "1.0"}
}'
```

* Response

```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "id": 1
  }
}
```

### Update Dataset

#### Method: POST
#### URL: `/imgsmlr/dataset/update`
#### Request Parameters

Field | Type | Required | Description
-------|-------|------|-----
id | integer | Yes | Dataset ID
name | string | No | Dataset name
description | string | No | Dataset description information
meta | object | No | Dataset metadata

#### Response Data

Returns empty data field on successful update

* Error Messages:
  * `Dataset not found` - Dataset not found

#### Example

* Request

```bash
curl -X POST http://127.0.0.1:8140/imgsmlr/dataset/update \
-H "Content-Type: application/json" \
-d '{
  "id": 1,
  "description": "Updated dataset description"
}'
```

* Response

```json
{
  "code": 200,
  "msg": "OK"
}
```

### Delete Dataset

#### Method: POST
#### URL: `/imgsmlr/dataset/delete`
#### Request Parameters

Field | Type | Required | Description
-------|-------|------|-----
id | integer | Yes | Dataset ID to delete

#### Response Data

Returns empty data field on successful deletion

* Error Messages:
  * `Dataset not found` - Dataset not found

#### Example

* Request

```bash
curl -X POST http://127.0.0.1:8140/imgsmlr/dataset/delete \
-H "Content-Type: application/json" \
-d '{
  "id": 1
}'
```

* Response

```json
{
  "code": 200,
  "msg": "OK"
}
```

### Get Dataset List

#### Method: GET
#### URL: `/imgsmlr/dataset/list`
#### Request Parameters

None

#### Response Data

* data:

Field | Type | Required | Description
-------|-------|------|-----
datasets | [DatasetInfo](#datasetinfo---dataset-information)[] | Yes | Dataset information list

#### Example

* Request

```bash
curl -X GET http://127.0.0.1:8140/imgsmlr/dataset/list
```

* Response

```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "datasets": [
      {
        "id": 1,
        "name": "test_dataset",
        "description": "Test dataset",
        "meta": {"version": "1.0"},
        "createdAt": "2024-01-01T10:00:00",
        "updatedAt": "2024-01-01T10:00:00"
      }
    ]
  }
}
```

## Image Management

### Add Image

Add an image to the specified dataset, the system will automatically extract image features and build index.

#### Method: POST
#### URL: `/imgsmlr/image/add`
#### Request Parameters

Field | Type | Required | Description
-------|-------|------|-----
url | string | Yes | Image URL address, must start with http:// or https://
datasetId | integer | Yes | Target dataset ID
dataId | string | No | User-defined data ID
remark | string | No | Remark information
meta | object | No | Metadata information
tags | string[] | No | Tag list

#### Response Data

* data:

Field | Type | Required | Description
-------|-------|------|-----
id | integer | No | ID of the newly added image record

* Error Messages:
  * `Invalid URL format. URL must start with http:// or https://` - Invalid URL format
  * `fetch url failed, status: xxx` - Failed to fetch image
  * `not a valid file` - Not a valid image file
  * `image file already exists` - Image file already exists (based on MD5 judgment)
  * `model not ready` - Model not initialized

#### Example

* Request

```bash
curl -X POST http://127.0.0.1:8140/imgsmlr/image/add \
-H "Content-Type: application/json" \
-d '{
  "url": "https://example.com/image.jpg",
  "datasetId": 1,
  "dataId": "img_001",
  "remark": "Test image",
  "meta": {"category": "demo"},
  "tags": ["test", "demo"]
}'
```

* Response

```json
{
  "code": 200,
  "msg": "OK",
  "data": {
    "id": 101
  }
}
```

### Search Similar Images

Search for similar images based on input image or text.

#### Method: POST
#### URL: `/imgsmlr/image/search`
#### Request Parameters

Field | Type | Required | Description
-------|-------|------|-----
url | string | Yes | Query image URL or text content (determined by matchType)
matchType | string | No | Match type: `imgsmlr`, `clip`, `siglip`, `cliptext`, `dataId`, default is `clip`
threshold | float | No | Similarity threshold, uses config value by default
datasetIds | integer[] | No | Dataset ID list to limit search scope, empty means search all datasets
limit | integer | No | Limit on number of results returned, uses config value by default

#### Match Type Description

* `imgsmlr` - Image feature matching based on imgsmlr algorithm
* `clip` - Image feature matching based on CLIP model
* `siglip` - Image feature matching based on SigLIP model  
* `cliptext` - Text-to-image matching based on CLIP model (pass text content in url field)
* `dataId` - Exact matching based on dataId (pass dataId in url field)

#### Response Data

* data:

Field | Type | Required | Description
-------|-------|------|-----
images | [ImageResult](#imageresult---search-result-image)[] | Yes | Similar image list, sorted by similarity in descending order
threshold | float | Yes | Actually used similarity threshold

* Error Messages:
  * `fetch url failed, status: xxx` - Failed to fetch query image  
  * `not a valid file` - Not a valid image file
  * `xxx model not initialized` - Specified model not initialized

#### Example

* Request

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

* Response

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
        "remark": "Similar image 1",
        "meta": {"category": "demo"},
        "simr": 0.95
      },
      {
        "id": 102,
        "url": "https://example.com/similar2.jpg",
        "dataId": "img_002", 
        "datasetId": 1,
        "md5": "def456ghi789",
        "remark": "Similar image 2",
        "meta": {"category": "demo"},
        "simr": 0.88
      }
    ],
    "threshold": 0.8
  }
}
```

### Query Image Information

Query detailed information of an image based on dataId.

#### Method: GET  
#### URL: `/imgsmlr/image/info`
#### Request Parameters

Parameter | Type | Required | Description
-------|-------|------|-----
dataId | string | Yes | User-defined data ID
tag | string | No | Tag filter (not implemented in current version)

#### Response Data

* data:

Field | Type | Required | Description
-------|-------|------|-----
images | [ImageInfo](#imageinfo---image-information)[] | Yes | List of matching image information

#### Example

* Request 

```bash
curl -X GET "http://127.0.0.1:8140/imgsmlr/image/info?dataId=img_001"
```

* Response

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
        "remark": "Test image",
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

## Usage Recommendations

1. **Dataset Management**: It is recommended to create different datasets according to business scenarios for easy management and search scope control
2. **Image Addition**: Ensure image URLs are accessible, the system will automatically deduplicate (based on MD5)
3. **Similarity Search**: 
   - `clip` mode is suitable for general image similarity search
   - `imgsmlr` mode is suitable for fast basic feature matching
   - `cliptext` mode supports text description to search images
4. **Performance Optimization**: Set threshold and limit parameters reasonably to avoid returning too many results that affect performance
5. **Error Handling**: Please pay attention to check the code field in the response and handle errors according to the msg field

[Back to Table of Contents](#table-of-contents)