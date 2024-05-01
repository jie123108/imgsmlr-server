import psycopg2

import logging
import time
import math
import json
import threading
from datetime import datetime
from threading import Lock
from urllib.parse import urlencode
import asyncio
import traceback
import httpx
import csv
import re
import math
log_format = "%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s"
logging.basicConfig(level="INFO", format=log_format)

g_stop = False

import asyncio
import threading
import logging

def unixtime_format(ts):
    tm = datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H%M')
    regex = r"([: ]00)+$"
    return re.sub(regex, "", tm)

class AsyncThread(threading.Thread):
    def __init__(self, loop=None):
        threading.Thread.__init__(self)
        isNewLoop = False
        if not loop:
            loop = asyncio.new_event_loop()
            isNewLoop = True
        self.loop = loop
        self.isNewLoop = isNewLoop

    async def async_run(self):
        raise NotImplementedError("Not implemented")

    async def destroy(self):
        pass

    def handle_exception(self, loop, context):
        # context["message"] will always be there; but context["exception"] may not
        msg = context.get("exception", context["message"])
        logging.error(f"Caught exception: {msg}")
        logging.info("Shutting down...")

    async def shutdown(self, loop, signal=None):
        """Cleanup tasks tied to the service's shutdown."""
        if signal:
            logging.info(f"Received exit signal {signal.name}...")

        logging.info("Closing connections")
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        logging.info(f"Cancelling {len(tasks)} outstanding tasks")
        await asyncio.gather(*tasks, return_exceptions=True)

        await self.destroy()
        loop.stop()

    def run(self):
        loop = self.loop
        # handle exceptions
        loop.set_exception_handler(self.handle_exception)
        try:
            loop.run_until_complete(self.async_run())
            # if self.isNewLoop:
            #     loop.run_forever()
        finally:
            if self.isNewLoop:
                loop.close()
            logging.info("AsyncThread shutdown successfully.")


import sys
import signal
def exit(signum, frame):
    logging.warning('You choose to stop me.')
    g_stop = True
    sys.exit(0)


class MemoryTicketBucketRateLimit:
    def __init__(self):
        self.cache = {}
        self.lock = Lock()

    def check_limit(self, key, rate, max_permits, permits=1):
        curr_mill_second = math.floor(time.time() * 1000)
        with self.lock:
            rate_limit_info = self.cache.get(key,{})
            if not rate_limit_info:
                self.cache[key] = rate_limit_info
            last_mill_second = rate_limit_info.get("last_mill_second")
            curr_permits = rate_limit_info.get("curr_permits", 0)
            # print("%s -> %s" % (key, rate_limit_info))
            local_curr_permits = max_permits
            # --- 令牌桶刚刚创建，上一次获取令牌的毫秒数为空
            # --- 根据和上一次向桶里添加令牌的时间和当前时间差，触发式往桶里添加令牌
            # --- 并且更新上一次向桶里添加令牌的时间
            # --- 如果向桶里添加的令牌数不足一个，则不更新上一次向桶里添加令牌的时间
            if last_mill_second is not None:
                reverse_permits = math.floor(((curr_mill_second - last_mill_second) / 1000) * rate)
                expect_curr_permits = reverse_permits + curr_permits;
                local_curr_permits = min(expect_curr_permits, max_permits);
                #--- 大于0表示不是第一次获取令牌，也没有向桶里添加令牌
                if reverse_permits > 0:
                    rate_limit_info["last_mill_second"] = curr_mill_second
            else:
                rate_limit_info["last_mill_second"] = curr_mill_second
            limited = False
            if local_curr_permits - permits >= 0:
                rate_limit_info["curr_permits"] = local_curr_permits - permits
            else:
                rate_limit_info["curr_permits"] = local_curr_permits
                limited = True
            return limited

rateLimiter = MemoryTicketBucketRateLimit()

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

limits = httpx.Limits(max_keepalive_connections=2000, max_connections=4000)
async_client = httpx.AsyncClient(limits=limits)

# 共用async_client, 支持keep alive
async def async_httpx_post(url, body, headers=None, timeout=None):
    req_debug = GetDebugStr('POST', url, None, headers, body)
    if timeout is None:
        timeout = 10
    try:
        if type(body) == dict:
            body = json.dumps(body)
        st = time.time()
        resp = await async_client.request('POST', url, data=body, headers=headers, timeout=timeout)
        text = resp.text
        setattr(resp, "reason", "OK")
        cost = time.time() - st
    except httpx.RequestError as ex:
        cost = time.time() - st
        text = 'httpx error'
        if isinstance(ex, httpx.TimeoutException):
            text = 'timeout'
        else:
            text = str(ex)
        resp = httpx.Response(500)
        setattr(resp, "reason", text)

    if resp.status_code != 200:
        logging.error("request [%s] failed! status: %s, cost: %.3f, resp: %s" % (req_debug, resp.status_code, cost, text))
    else:
        # logging.info("request [%s] success! status: %s, cost: %.3f, resp: %s" % (req_debug, resp.status_code, cost, text))
        pass
    return resp, req_debug

class ClientAsyncThread(AsyncThread):
    def __init__(self, psql_url, min_id, limit, rate=1, matchType="clip", threshold=0.3, searchLimit=10):

        AsyncThread.__init__(self)
        self.matchType = matchType
        self.threshold = threshold
        self.searchLimit = searchLimit
        self.psql_url = psql_url
        self.min_id = min_id
        self.limit = limit
        self.rate = rate
        self._lock = asyncio.Lock()
        self._total = 0
        now = int(time.time())
        tm = unixtime_format(now)
        self.csvfile = open("相似结果_%s.csv" % (tm), mode='w')
        self.csv_writer = csv.writer(self.csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        titles = ["原始链接"]
        for x in range(1, 10):
            x_distance = "距离%d" % (x)
            x_url = "图片URL%d" % (x)
            titles.append(x_distance)
            titles.append(x_url)
        self.csv_writer.writerow(titles)

    async def image_similarity(self, image_url):
        body = json.dumps({"url": image_url, "matchType": self.matchType, "threshold": self.threshold, "limit": self.searchLimit})
        res, req_debug = await async_httpx_post("http://127.0.0.1:8140/imgsmlr/search", body)
        if res.status_code != 200:
            logging.error("查询相似图片时出错. request [ %s ] status: %s", req_debug, res.status_code)
            return False, "request failed!"
        resp = res.json()
        return True, resp

    # 格式为: 图片URL
    async def process_item(self, record):
        try:
            id = record[0]
            url = record[1]
            data_id = record[2]
            md5 = record[3]

            ok, resp = await self.image_similarity(url)
            if ok:
                row = [url]
                if resp and resp["code"] == 200 and "data" in resp:
                    data = resp["data"]
                    images = data.get("images")
                    if images and len(images) > 0:
                        simr = images[0]["simr"]
                        if simr == 0: #是同一张图片
                            images.pop(0)
                    if images:
                        for imageInfo in images:
                            simr = imageInfo["simr"]
                            url = imageInfo["url"]
                            row.append("%.4f" % (simr))
                            row.append(url)
                        self.csv_writer.writerow(row)
            if id != 0 and id % 100 == 0:
                logging.info("已经处理 %d/%d 条记录", id, self._total)
                self.csvfile.flush()
        except Exception as ex:
            logging.error("process line=%d { %s } failed, ex: %s" % (id, record, traceback.format_exc()))

    async def async_run(self):

        logging.info("read datas from database '%s'", self.psql_url)

        # Connecting to the database
        psql_url = self.psql_url
        limit = self.limit
        min_id = self.min_id
        conn = psycopg2.connect(psql_url)
        cursor = conn.cursor()
        # Calculating number of pages
        num_pages = limit // 1000 if limit % 1000 == 0 else limit // 1000 + 1
        # Each iteration corresponds to a page
        for i in range(num_pages):
            current_limit = 1000 if i < num_pages - 1 else limit % 1000  # Check if it is the last page
            if current_limit == 0:  # If the limit is exactly a multiple of 1000, set the limit for the last page to 1000
                current_limit = 1000
            query = "SELECT id, url, data_id, md5 FROM image WHERE id > %s ORDER BY id ASC LIMIT %s"
            values = (min_id, current_limit)
            cursor.execute(query, values)
            limit_key = "limit"
            # Do something with the data, for example, print it out
            for record in cursor:
                id = record[0]
                url = record[1]
                data_id = record[2]
                md5 = record[3]
                min_id = id
                print(id, url)
                if self.rate > 0:
                    for x in range(10 * 30):
                        limited = rateLimiter.check_limit(limit_key, self.rate, self.rate * 2, permits=1)
                        if not limited or g_stop:
                            break
                        # limited
                        await asyncio.sleep(0.1)
                    asyncio.get_event_loop().create_task(self.process_item(record))
                else:
                    await self.process_item(record)

            # Update the min_id for the next page
        cursor.close()
        conn.close()
        await asyncio.sleep(3)
        await async_client.aclose()

        logging.info("---------- finished -------------")

signal.signal(signal.SIGINT, exit)
signal.signal(signal.SIGTERM, exit)

class ResultHtmlBuilder:
    def __init__(self, html_filename_fmt, max_rows_per_file = 500, column_count=5):
        self.html_filename_fmt = html_filename_fmt
        self.html_builder = []
        self.max_rows_per_file = max_rows_per_file
        self.rows = 0
        self.column_count = column_count
        self.file_map = {}

    def init_header(self):
        header = """
<html>
<head>
<meta charset="utf-8">
<title>图片相似度测试</title>
<style type="text/css">
body {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  margin: 0;
}

table {
    border-spacing: 8px;
}

.title {
    background-color: #ff0000;
    height: 30px;
    text-align: center;
    vertical-align: middle;
    font-size: 16px;
    font-weight: 600;
}

.title.title-td {
    background-color: #ff0000;
    border: 1px solid #1f1f1f;
    border-left-width: thin;
    box-shadow: 3px 3px 5px #736d6dbd;
}

.img-td {
    width: 200px;
    height: 300px;
}

.image-item {
    background-color: #fdeede;
    height: 100%;
    display: flex;
    flex-direction: column;
    border: 1px solid #1f1f1f;
    border-left-width: thin;
    box-shadow: 3px 3px 5px #736d6dbd;
}

.img-div {
    background-color: #e3e3e3;
    width: 200px;
    height: 270px;
    display: flex;
    align-items: center;
}

.img-x {
    background-color: #ff0000;
    width: 200px;
    max-height: 270px;
}

.img-sim-ok {
    background-color: #00b800;
    height: 30px;
    text-align: center;
}

.img-sim-nok {
    background-color: #FF0000;
    height: 30px;
    text-align: center;
}

</style>
</head>
<body>
        """
        self.html_builder.append(header)
    def close_html(self):
        self.html_builder.append("</body></html>")

    def open_table(self):
        self.html_builder.append("<table>")
        self.html_builder.append("<tr class=\"title\">")
        self.html_builder.append("<td class=\"title-td\">原始链接</td>")
        for x in range(1, self.column_count):
            self.html_builder.append("<td class=\"title-td\">图片%d</td>" % x)
        self.html_builder.append("</tr>")

    def close_table(self):
        self.html_builder.append("</table>")
    
    def get_file(self, filename):
        file = self.file_map.get(filename)
        if file:
            return file
        file = open(filename, "w")
        self.init_header()
        self.open_table()
        self.file_map[filename] = file
        return file

    def get_filename(self):
        file_index = math.ceil(self.rows / self.max_rows_per_file)
        filename = self.html_filename_fmt % (file_index)
        return filename

    def write_row(self, row):
        self.rows += 1
        filename = self.get_filename()
        file = self.get_file(filename)
        self.html_builder.append(row)
        if self.rows % self.max_rows_per_file == 0:
            self.close_table()
            self.close_html()
            file.write('\n'.join(self.html_builder))
            file.close()
            self.html_builder = []
    
    def finish(self):
        if self.html_builder:
            self.close_table()
            self.close_html()
            filename = self.get_filename()
            file = self.get_file(filename)
            file.write('\n'.join(self.html_builder))
            self.html_builder = []
            file.close()

def csv_to_html(filename, ok_threshold):
    file = open(filename, 'r')
    csvreader = csv.reader(file)
    titles = next(csvreader)
    print(titles)
    column_count = 5
    html_filename_fmt = filename.replace(".csv", "-%d.html")
    result_html_builder = ResultHtmlBuilder(html_filename_fmt, column_count=column_count)

    for x in range(200000):
        # CSV header: ['原始链接', '距离1', '图片URL1', '距离2', '图片URL2', '距离3', '图片URL3', '距离4', '图片URL4', '距离5', '图片URL5', '距离6', '图片URL6', '距离7', '图片URL7', '距离8', '图片URL8', '距离9', '图片URL9']
        try:
            row = next(csvreader)
            if not row:
                break
        except:
            break
        tr_arr = []
        tr_arr.append("<tr>")
        originUrl = row[0].strip()
        tr_arr.append("""<td class="img-td">
<div class="image-item">
<div class="img-div"><img src="%s" class="img-x"></img></div>
<div class="img-sim-ok">原始图片</div>
</div>
</td>""" % (originUrl))
        skip = False
        okColumns = 0
        for col in range(1, column_count*3):
            colIdx = col * 2 - 1
            if colIdx < len(row):
                sim = row[colIdx].strip()
                sim_url = row[colIdx + 1].strip()
                if sim_url:
                    sim = float(sim)
                    if okColumns == 0 and sim > ok_threshold:
                        skip = True
                        break
                    if sim < 0.01:
                        continue
                    simClass = "img-sim-nok"
                    if sim <= ok_threshold:
                        simClass = "img-sim-ok"
                    tr_arr.append("""
            <td class="img-td">
            <div class="image-item">
                <div class="img-div"><img src="%s" class="img-x"></img></div>
                <div class="%s">距离: %.3f</div>
            </div>
            </td>""" % (sim_url, simClass, sim))
                else:
                    tr_arr.append("<td></td><td></td>")
            else:
                tr_arr.append("<td></td><td></td>")
            okColumns = okColumns + 1
            if okColumns >= column_count:
                break
        tr_arr.append("</tr>")
        if skip:
            continue
        result_html_builder.write_row('\n'.join(tr_arr))
    result_html_builder.finish()

async def main():
    import sys
    import time
    now = int(time.time())
    import argparse
    DEF_PSQL_URl = "postgresql://imgsmlr:imgsmlr-123456@127.0.0.1:5400/imgsmlr"
    parser = argparse.ArgumentParser(description="敏感图阈值测试工具")
    parser.add_argument('--psql_url',help="psql连接", default=DEF_PSQL_URl, type=str)
    parser.add_argument('--minId',help='minId', default=0, type=int)
    parser.add_argument('--limit',help='limit', default=500, type=int)
    parser.add_argument('--rate',help='request rate', default=1, type=float)
    parser.add_argument('--threshold',help='threshold', default=0.3, type=float)
    parser.add_argument('--searchLimit',help='limit of search', default=10, type=int)
    parser.add_argument('--to_html',help="将csv转换成html文件", default="", type=str)
    parser.add_argument('--ok_threshold',help='threshold to html', default=0.1, type=float)

    args = parser.parse_args()
    if args.to_html:
        csv_to_html(args.to_html, args.ok_threshold)
    else:
        thread = ClientAsyncThread(args.psql_url, args.minId, args.limit, rate=args.rate, threshold=args.threshold, searchLimit=args.searchLimit)
        thread.start()

if __name__ == '__main__':
    import asyncio
    asyncio.get_event_loop().run_until_complete(main())
