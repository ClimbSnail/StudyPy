#!/usr/bin/env python
# -*- coding: utf-8 -*-
################################################################################
#
# Copyright (c) 2021 Baidu.com, Inc. All Rights Reserved
#
################################################################################
"""
Brief: 启动入口
Authors: 何琦(heqi04@baidu.com)
Date:    2021/03/09
"""
import json
import asyncio
# import time
# import threading
# import multiprocessing
# from tornado.web import Application
# import tornado.routing as routing
from tornado.web import RequestHandler, Application
from tornado.httpserver import HTTPServer
import sync_handler
from flask import Flask
from flask import request
from flask import Blueprint
# 而在某些特定的需求下，需要动态匹配一些有特殊要求的字符，这就可以考虑用正则表达式的方式传入
from werkzeug.routing import BaseConverter
from jupyter_server.extension.application import ExtensionApp
def url_path_join(*pieces):
    """Join components of url into a relative url
    Use to prevent double slash when joining subpath. This will leave the
    initial and final / in place
    """
    initial = pieces[0].startswith('/')
    final = pieces[-1].endswith('/')
    stripped = [s.strip('/') for s in pieces]
    result = '/'.join(s for s in stripped if s)
    if initial: result = '/' + result
    if final: result = result + '/'
    if result == '//': result = '/'
    return result
def form_route(base_url, endpoint):
    """
    :param web_app:
    :param endpoint:
    :return:
    """
    return url_path_join(base_url, 'jarvis', endpoint)


def request_parse(req):
    '''解析请求数据并以json形式返回'''
    data = None
    try:
        if req.method == 'POST':
            data = req.json
        elif req.method == 'GET':
            data = str(dict(req.args)).replace("'", '"')
        elif req.method == 'PUT':
            data = str(req.get_data(), encoding="utf8")
        else:
            data = dict()
    except Exception as err:
        sync_handler.print_err_lines(err)
    return data

class RegexConverter(BaseConverter):
    """
    编写正则转化的类  配合Flaskapp的route解析
    """
    def __init__(self, url_map,*items):
        super(RegexConverter,self).__init__(url_map)
        self.regex = items[0]
        
vtfs_sync_http_server = Flask(__name__)
#初始化转换器
vtfs_sync_http_server.url_map.converters['reg'] = RegexConverter
# 蓝图设置
#url_prefix = '/v1/vtfs/<reg("[a-zA-Z\d_]*"):vtfs_path>'
url_prefix = '/v1/vtfs'
vtfs_sync_blueprint = Blueprint(
    'vtfs_sync',
    __name__,
    url_prefix=url_prefix
)
# http://127.0.0.1:5001/v1/vtfs/vtfsid1234/sync_status?action=search&syncNum=100
# 加入路由信息
@vtfs_sync_blueprint.route("/")
def index():
    return f"Hello !!!"
    # 使用render_template，文件必须要同级目录的templates文件夹中
    # return render_template("login.html")
# http://127.0.0.1:5001/v1/vtfs/vtfsid1234/synchronization/auto
# {"vtfs_path":"path", "autoSyncAction":"on""off", "syncNum":"1000"}
@vtfs_sync_blueprint.route("/synchronization/auto", methods=["PUT"]) #, endpoint="r_info")
def auto_sync_route():
    dict_param = request_parse(request) # 获取 JSON 数据
    result = sync_handler.auto_sync(dict_param, None)
    return result
# http://127.0.0.1:5001/v1/vtfs/vtfsid1234/synchronization/single
# {"vtfs_path":"path", "singleSyncAction":"start""canle", "syncNum":"1000"}
@vtfs_sync_blueprint.route("/synchronization/single", methods=["PUT"])
def single_sync_route():
    dict_param = request_parse(request) # 获取 JSON 数据
    result = sync_handler.single_sync(dict_param, None)
    return result
# http://127.0.0.1:5001/v1/vtfs/vtfsid1234/sync_status?action=search&syncNum=100&vtfs_path=path
@vtfs_sync_blueprint.route("/sync_status", methods=["GET"])
def sync_status_route():
    dict_param = request_parse(request) # 获取 JSON 数据
    result = sync_handler.sync_status(dict_param, None)
    return result
# http://127.0.0.1:5001/v1/vtfs/vtfsid1234/sync/singlefile/progress?action=search&syncNum=100&fileName=path&mode=one_shot
@vtfs_sync_blueprint.route("/sync/singlefile/progress", methods=["GET"])
def singlefile_progress_route():
    dict_param = request_parse(request) # 获取 JSON 数据
    result = sync_handler.single_file_progress(dict_param, None)
    return result
# http://127.0.0.1:5001/v1/vtfs/vtfsid1234/sync/allfile/progress?action=search&syncNum=100&mode=one_shot
@vtfs_sync_blueprint.route("/sync/allfile/progress", methods=["GET"])
def allfile_progress_route():
    dict_param = request_parse(request) # 获取 JSON 数据
    result = sync_handler.all_file_progress(dict_param, None)
    return result
@vtfs_sync_blueprint.route("/download_to_local", methods=["GET"])
def download_to_local_route():
    dict_param = request_parse(request) # 获取 JSON 数据
    result = sync_handler.download_to_local(dict_param, None)
    return result
vtfs_sync_http_server.register_blueprint(vtfs_sync_blueprint)
def http_run(host, port, debug):
    global vtfs_sync_http_server
    vtfs_sync_http_server.run(host=host, port=port, debug=debug)
class MainHandler(RequestHandler):
    def get(self):
        self.write("Hello, world")
# http://127.0.0.1:5000/v1/vtfs/synchronization/auto
# {"vtfs_path":"path", "autoSyncAction":"on""off", "syncNum":"1000"}
class AutoSyncHandler(RequestHandler):
    def put(self):
        dict_param = request_parse(self) # 获取 JSON 数据
        result = sync_handler.auto_sync(dict_param, None)
        self.write(result)
class SingleSyncHandler(RequestHandler):
    def put(self):
        dict_param = request_parse(self) # 获取 JSON 数据
        result = sync_handler.single_sync(dict_param, None)
        self.write(result)
# http://127.0.0.1:5001/v1/vtfs/sync_status?action=search&syncNum=100&vtfs_path=path
class SyncStatusHandler(RequestHandler):
    def get(self):
        dict_param = request_parse(self) # 获取 JSON 数据
        result = sync_handler.sync_status(dict_param, None)
        self.write(result)
class SingleFileProgressHandler(RequestHandler):
    def get(self):
        dict_param = request_parse(self) # 获取 JSON 数据
        result = sync_handler.single_file_progress(dict_param, None)
        self.write(result)
class AllFileProgressHandler(RequestHandler):
    def get(self):
        dict_param = request_parse(self) # 获取 JSON 数据
        result = sync_handler.all_file_progress(dict_param, None)
        self.write(result)
class DownloadToLocalHandler(RequestHandler):
    def get(self):
        dict_param = request_parse(self) # 获取 JSON 数据
        result = sync_handler.download_to_local(dict_param, None)
        self.write(result)
base_uri = r'/v1/vtfs'
# 创建路由表
urls = [
    (r"/", MainHandler),
    (r"/index", MainHandler),
    (r"/v1/vtfs/synchronization/auto", AutoSyncHandler),
    (base_uri+r"/synchronization/auto", AutoSyncHandler),
    (base_uri+r"/synchronization/single", SingleSyncHandler),
    (base_uri+r"/sync_status", SyncStatusHandler),
    (base_uri+r"/sync/singlefile/progress", SingleFileProgressHandler),
    (base_uri+r"/sync/allfile/progress", AllFileProgressHandler),
    (base_uri+r"/download_to_local", DownloadToLocalHandler)
]

class HttpServerApp():
    def __init__(self):
        global logging
        # vtfs_sync_http_app.run(host='127.0.0.1', port=5001, debug=True)
        # http_run('127.0.0.1', 5001, True)
        """用于启动websocket插件应用"""
        # from websocket_ext import application
        #
        # application.main()
        logging.info("application.main()")
        app = Application(urls)
        #app.listen(8000)
        # 创建HTTP服务器实例
        server = HTTPServer(app)
        # 监听端口
        server.listen(5000)
        # IOLoop.current().start()