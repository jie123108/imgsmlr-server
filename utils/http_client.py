# -*- coding: utf-8 -*-


import json
from urllib.parse import urlencode
from loguru import logger
import httpx


def headerstr(headers):
    if not headers:
        return ""

    lines = []
    for key in headers:
        if key != "User-Agent":
            value = headers[key]
            lines.append("-H'" + str(key) + ": " + str(value) + "'")

    return ' '.join(lines)


def GetDebugStr(method, url, args, headers, body):
    if headers == None:
        headers = {}
    if type(body) == dict:
        body = json.dumps(body)
    req_debug = ""
    if args:
        query = urlencode(args).encode(encoding='utf-8', errors='ignore')
        url = "%s?%s" % (url, query.decode("utf-8"))
    if method == "PUT" or method == "POST" or method == "DELETE":
        debug_body = ''
        content_type = headers.get("Content-Type")
        if content_type == None or content_type.startswith("text") or content_type == 'application/json':
            if len(body) < 2000:
                debug_body = body
            else:
                debug_body = body[0:1023]
        else:
            debug_body = "[[not text body: " + str(content_type) + "]]"
        req_debug = "curl -v -k -X " + method + " " + headerstr(
            headers) + " '" + url + "' -d '" + debug_body + "' -o /dev/null"
    else:
        req_debug = "curl -v -k -X " + method + " " + headerstr(headers) + " '" + url + "'"

    return req_debug

async def async_http_post(url, body, headers=None, timeout=None):
    req_debug = GetDebugStr('POST', url, None, headers, body)
    if timeout is None:
        timeout = 6
    try:
        if type(body) == dict:
            body = json.dumps(body)
        async with httpx.AsyncClient() as client:
            resp = await client.request('POST', url, data=body, headers=headers, timeout=timeout)
            text = resp.text
            setattr(resp, "reason", "OK")
    except httpx.RequestError as ex:
        text = 'httpx error'
        if isinstance(ex, httpx.TimeoutException):
            text = 'timeout'
        else:
            text = str(ex)
        resp = httpx.Response(500, ext={"ex": ex})
        setattr(resp, "reason", text)

    if resp.status_code != 200:
        logger.info("request [%s] failed! status: %s, resp: %s" % (req_debug, resp.status_code, text))
    else:
        logger.info("request [%s] success! status: %s, resp: %s" % (req_debug, resp.status_code, text))
    return resp, req_debug


async def async_http_get(url, headers=None, timeout=None):
    req_debug = GetDebugStr('GET', url, None, headers, None)
    if timeout is None:
        timeout = 6
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.request('GET', url, headers=headers, timeout=timeout)
        errmsg = "OK"
    except httpx.RequestError as ex:
        errmsg = 'httpx error'
        if isinstance(ex, httpx.TimeoutException):
            errmsg = 'timeout'
        else:
            errmsg = str(ex)
        resp = httpx.Response(500)

    if resp.status_code != 200:
        logger.info("request [%s] failed! status: %s, errmsg: %s" % (req_debug, resp.status_code, errmsg))
    else:
        pass
        # logger.info("request [%s] success! status: %s" % (req_debug, resp.status_code))
    return resp, req_debug
