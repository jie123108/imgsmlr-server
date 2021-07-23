
# imgsmlr-server

Image search service based on `imgsmlr` extension of `PostgreSQL`. Support image search by image.

This is a sample application of `imgsmlr`. It can be extended as appropriate and applied to the following scenarios:

* Image and video work similarity detection
* Illegal image filtering service.
* Searching original video by video clip, video gif, video screenshot.


# Reference

* [https://github.com/postgrespro/imgsmlr](https://github.com/postgrespro/imgsmlr)
* [https://github.com/jie123108/libimgsmlr](https://github.com/jie123108/libimgsmlr)
* 中文: [https://github.com/digoal/blog/blob/master/201607/20160726_01.md](#https://github.com/digoal/blog/blob/master/201607/20160726_01.md)

# Run

### Download source code

```
git clone https://github.com/jie123108/imgsmlr-server
cd imgsmlr-server
```

### Init database

###### Start by docker-compose

```shell
docker-compose up -d
```

If you want to install and start the database yourself, please follow the online tutorial to install the `imgsmlr` extension. And use `scripts/imgsmlr_init.sql` to initialize the database.

###### access the database

```
docker exec -ti imgsmlr-server_postgres_1 psql -U imgsmlr -d imgsmlr
```

### Start the server

```
pip install -r requirements.txt
python img-smlr-server.py
```

If the default configuration does not start properly. Please modify the configuration in `config.py` according to the actual situation.

# Test

### Add images

Adding images, currently only image URLs are supported. The more images the better. You can add them with the following command:

```curl
curl http://127.0.0.1:8140/imgsmlr/mgr/add -d '{"url": "http://host:port/image-file.jpg"}'
```

Tip: If you have already downloaded the image locally, you can start an `nginx` or `python` (`python3 -m http.server`) to turn the image into a URL.

### Search by image

###### Request

```curl
curl 'http://127.0.0.1:8140/imgsmlr/search' \
  -H 'Content-Type: application/json;charset=UTF-8' \
  -d '{"url":"http://host:port/search-image.jpg"}'
```

###### Response

```json
{
    "code": 200,
    "data": {
        "images": [
            {
                "dataId": null,
                "id": 212,
                "md5": "a230afeb27358888606f3105bfd05195",
                "meta": null,
                "remark": null,
                "simr": 0,
                "url": "http://host:port/image1.jpg"
            },
            {
                "dataId": null,
                "id": 205,
                "md5": "ce1321185d4b1318835775d04783c0c2",
                "meta": null,
                "remark": null,
                "simr": 1.06304,
                "url": "http://host:port/image2.jpg"
            },
            {
                "dataId": null,
                "id": 556,
                "md5": "f1e2c4f1cad7ef80fb16fe87623d4f82",
                "meta": null,
                "remark": null,
                "simr": 1.881019,
                "url": "http://host:port/image3.jpg"
            },
            ...
        ]
    },
    "msg": "OK"
}
````

### Test Page

You can test the image search function by visiting `http://127.0.0.1:8140/imgsmlr/`.

###### Screenshot of test page


| ![./docs/imgs/demo-p1.png](./docs/imgs/demo-p1.png) |
|:--:|
| *demo-p1* |

| ![./docs/imgs/demo-p2.png](./docs/imgs/demo-p2.png) |
|:--:|
| *demo-p2* |

| ![./docs/imgs/demo-p3.png](./docs/imgs/demo-p3.png) |
|:--:|
| *demo-p3* |

## LICENSE

[MIT](./LICENSE)
