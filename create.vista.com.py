#!/usr/bin/env python3

import os
import sys
import time
import json
import codecs
import urllib
# import response
import requests
import threading  # 导入线程库
from bs4 import BeautifulSoup


class Trans:
    # ----------------------------类变量的定义--------------------------#
    header1 = {
        'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10'}
    header2 = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36 Core/1.53.3176.400 QQBrowser/9.6.11520.400'}
    headers = header1

    url_bilingual = '''https://create.vista.com/videos/galaxy-seamless-loop/?page='''  # 中英请求地址

    # -------------------------------初始文件路径------------------------------#
    filePath = ''  # 文件夹路径
    fwname = 'vista_OutFile'  # 输出文件夹
    recordname = 'vista_RecordFile.txt'  # 记录点文件
    errorname = 'vista_ErrorFile.txt'  # 错误文件

    img_url = []
    img_name = []

    # -------------------------线程信号量--------------------------#
    cond1 = threading.Lock()  # 信号量1
    cond2 = threading.Lock()  # 信号量2
    cond3 = threading.Lock()  # 信号量3
    cond4 = threading.Lock()  # 信号量4

    begin_pos = 0  # 初始化并且获取词典开始位置
    index = 0  # 目前计数指针

    def __init__(self, name):
        self.se = requests  # 为每个对象分配session对象
        self.result = 0
        self.name = name  # 设置单前对象名称
        self.now_index = 0  # 当前类所获取的行数标号
        self.error_time = 0  # 错误计数值
        self.page = 0  # 当前单词所搜索到的总页数
        self.now_page = 0  # 程序当前解析的页码编号

    @classmethod
    def get_link_list(self, page_max):
        print("正在获取前%d页的图片链接" % page_max)
        for page in range(page_max):
            try:
                re = requests.post(url=Trans.url_bilingual + str(page), headers=Trans.headers)  #
                re.encoding = 'utf-8'  # 编码格式
                soup = BeautifulSoup(re.text, 'html.parser')
                links = soup.find_all('div', attrs={"class": 'wrapper-1D3Pt'})
                titles = soup.find_all('div', attrs={"class": 'descriptionContainer-1t1uM'})

                # print(titles)

                img_url = []
                for link in links:
                    img = link.find('img')
                    img_url.append(img["src"])
                    # print(img["src"])

                img_name = []
                for title in titles:
                    p = title.find('p')
                    img_name.append(p.string)
                    # print(p.string)

                print("Link size", len(img_url))
                print("Title size", len(img_name))

                if len(img_url) == len(img_name):
                    Trans.img_url = Trans.img_url + img_url
                    Trans.img_name = Trans.img_name + img_name
            except Exception as err:
                print(err)
        for name in Trans.img_name:
            print(name)

    def analysis_data(self, url, path):
        """
        分析数据 并将数据写入到指定文件
        """
        self.result = 0
        try:
            for link, title in zip(url, path):
                response = requests.get(url)
                # 将图片数据写入本地文件
                with open(path, 'wb') as file:
                    file.write(response.content)

            self.result = 1

        except requests.exceptions.ReadTimeout:  # 时间超限
            print("time_out")
            if self.error_time == 5:
                return -3
            else:
                time.sleep(2)  # 程序睡眠5秒
                self.error_time += 1  # 错误时间+1
                return 0
        except requests.exceptions.ConnectionError:  # 链接错误
            print("connect_error")
            if self.error_time == 5:
                return -4
            else:
                self.error_time += 1
                return 0
        except Exception as err:
            print(err)

    @classmethod
    def check_initial_parameter(self):
        """
        检查程序初始参数并初始化文件路径
        """
        if len(sys.argv) > 1:  # 检测是否带参数传进来了
            Trans.filePath = sys.argva[1]  # 文件夹路径
            Trans.fwname = sys.argv[3]  # 输出文件

        Trans.fwname = Trans.filePath + Trans.fwname
        Trans.recordname = Trans.filePath + Trans.recordname
        Trans.errorname = Trans.filePath + Trans.errorname

        # ----------------------------初始化-----------------------------#

    @classmethod
    def init(self):
        Trans.check_initial_parameter()  # 检查程序初始参数并初始化文件路径
        Trans.begin_pos = 1
        
        # 启用断点下载
        # if os.path.exists(Trans.recordname):
        #     frecord = codecs.open(Trans.recordname, 'r', 'utf-8')
        #     recordDatas = frecord.readlines()
        #     try:
        #         Trans.begin_pos = int(recordDatas[-1])
        #     except Exception:
        #         if len(recordDatas) > 1:
        #             Trans.begin_pos = int(recordDatas[-2])
        #     frecord.close()
        # else:  # 记录文件不存在 就要从头开始读字典
        #     Trans.begin_pos = 1

        try:
            os.mkdir(Trans.fwname)
        except Exception:
            pass

    def save_record(self, recordfilepath, dat):
        """
        数据点保存记录
        设置记录保存点文件为追加模式.为了避免在写记录文件的时,程序意外终止或电脑关机造成的记录点被破坏
        """
        frecord = codecs.open(recordfilepath, 'a', 'utf-8')
        frecord.write(str(dat + 1) + "\n")
        frecord.close()

    def write_error(self, errorfilepath, info):
        """
        写入错误
        """
        file_error = codecs.open(errorfilepath, 'a', 'utf-8')
        file_error.write(str(info) + '\n')
        file_error.close()

    def run(self):
        while True:
            print("%s线程开始下载新图片" % self.name)
            # -------------此处记得加上线程锁--------------------#
            Trans.cond1.acquire()  # 获得锁
            Trans.index += 1  # 记录当前词典读词的位置
            self.now_index = Trans.index

            if Trans.index % 10 < 5:  # 消除服务器检测到程序
                Trans.headers = Trans.header1
            else:
                Trans.headers = Trans.header2

            if Trans.index < Trans.begin_pos:  # 还未到达记录点
                Trans.cond1.release()  # 不加会导致死锁
                continue  # 跳过所有查询
            Trans.cond1.release()  # 释放锁

            if self.now_index > len(Trans.img_url):  # 所有词典都以读完处理
                print('爬取结束\n')
                print("\n" + self.name + "  ========>  is finish\n")
                break

            # if self.now_index % 10 == 0:        #爬久了服务器会限制速度 所以要重新获取新的session对象
            #     self.se = requests                    #session对象
            self.analysis_data(Trans.img_url[self.now_index],
                               Trans.fwname + "/" + str(self.now_index) + "-" + Trans.img_name[self.now_index] + ".jpg")

            # -------------此处记得加上线程锁--------------------#
            if self.result == 1:
                Trans.cond3.acquire()  # 获得锁
                self.save_record(Trans.recordname, self.now_index)  # 将数据点保存在记录文件中
                Trans.cond3.release()  # 释放锁
            else:  # 写入数据时未发生错误
                Trans.cond4.acquire()  # 获得锁
                self.write_error(Trans.errorname, self.now_index)  # 处理写入错误
                Trans.cond4.release()  # 释放锁


if __name__ == "__main__":
    """
    主函数
    """
    os.system("create.vista.com/videos/galaxy-seamless-loop")
    Trans.init()  # 初始化并且获取词典开始位置
    Trans.get_link_list(5)
    thread_num = 30
    Translist = []
    for i in range(0, thread_num, 1):
        Translist.append(Trans('T' + str(i)))

    thread_object = []
    for i in range(0, thread_num, 1):  # 创建多线程,并将添加线程对象添加进列表对象thread_object中
        thread_object.append(threading.Thread(target=Translist[i].run))
    for i in range(0, thread_num, 1):
        thread_object[i].start()  # 启动所有线程对象
    for i in range(0, thread_num, 1):
        thread_object[i].join()  # 将会阻塞主进程的运行,直到子线程运行完

    print("\n\n\n\n\n\n\n-----------------Main is finish-----------------\n\n")
