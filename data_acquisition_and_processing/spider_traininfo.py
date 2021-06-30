#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
在oklx中下载所有的车次信息（12306太慢了），由于需要不断调试，因此设置了日志文件
每次可以选择输入下载的数量，全部下载完毕后则不能下载，可以清空或设置log文件后重新下载
"""
import random
import time
import json
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient


# noinspection PyPep8Naming
class GetTrainInfo(object):
    def __init__(self, this_num, last_sum):
        self.client = MongoClient('localhost', port=27017)
        self.db = self.client.train
        self.collection = self.db.Train

        self.url = 'http://www.oklx.com/cn/train/traininfo/'
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                                      ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'}
        self.in_filename = "data/trains.json"
        self.log_filename = "data/logging_train.log"
        self.invalid = []

        self.this_num = this_num
        self.last_sum = last_sum

    @staticmethod
    def trainType(code):
        type_dict = {'D': '普通动车组', 'T': '特快', 'G': '高速动车组', 'C': '城际动车组',
                     'K': '快速', 'Z': '直达特快', 'O': ['普快', '普客'], }
        if code[0].isdigit():
            train_type = type_dict['O'][0] if int(code[0]) < 6000 else type_dict['O'][1]
        elif code[0] in ['D', 'T', 'G', 'C', 'K', 'Z', 'O']:
            train_type = type_dict[code[0]]
        else:
            train_type = '其他'
        return train_type

    def writeLog(self, count, code, invalid):
        time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        # log的顺序为时间，总下载数量，本次下载数量，下载的最后一个车次，错误的车次信息
        log = '{},{},{},{},{}\n'.format(time_now, self.last_sum+self.this_num, count, code, invalid)
        with open(self.log_filename, 'a', encoding='utf-8') as f:
            f.write(log)

    def getHTML(self, url, code):
        try:
            reps = requests.get(url=url, headers=self.headers, timeout=3)
            reps.encoding=reps.apparent_encoding
            reps = reps.text
            html = BeautifulSoup(reps, 'lxml')
            #print(code)
        except (Exception, requests.exceptions.RequestException):  # 捕获requests处理不确定的异常请求:
            self.invalid.append(code)
            return 0
        return html

    def analysisHTML(self, html, code):
        try:
            html_tr = html.find(class_='VistaTable').find_all('tr')
            info_list, key = [], []
            for tr in html_tr[1:]:
                html_td = tr.find_all('td')
                td_no = html_td[0].text.replace('\r\n', '').replace(' ', '')  # 站次
                td_name = html_td[1].text.replace('\n', '')  # 站名
                if "特价酒店预订" in html_td[2].text.replace('\r', '').replace('\n', '') or html_td[2].text == '\n':
                    td_date = html_td[3].text.replace('\r\n', '').replace(' ', '')  # 日期
                    td_stop = html_td[4].text  # 停车时间
                    td_start = html_td[5].text  # 开车时间
                    td_km = html_td[6].text[:-2]  # 里程
                    td_period = html_td[7].text.replace('\r\n', '').replace(' ', '')  # 运行时间
                else:
                    td_date = html_td[2].text.replace('\r\n', '').replace(' ', '')  # 日期
                    td_stop = html_td[3].text  # 停车时间
                    td_start = html_td[4].text  # 开车时间
                    td_km = html_td[5].text[:-2]  # 里程
                    td_period = html_td[6].text.replace('\r\n', '').replace(' ', '')  # 运行时间
                info_list.append([td_no, td_name, td_date, td_stop, td_start, td_km, td_period])
                key.append(td_name)
            info = [info_list, key]
        except (Exception, ValueError):  # 捕获映射或序列上使用的键或索引无效时引发的异常的基类:
            self.invalid.append(code)
            return
        return info

    def saveToMongoDB(self):
        with open(self.in_filename, 'r', encoding='utf-8') as f:
            trains_data = f.read()
        trains_data = json.loads(trains_data)
        train_no_dict = trains_data['train_no']
        train_code_dict = trains_data['train_code']
        print('-> 载入车次代码库成功，开始下载车次信息.....')
        count = 0
        for n in range(self.last_sum, self.last_sum+self.this_num):      # len(train_code_dict)
            if self.last_sum+self.this_num > len(train_no_dict):
                print('已下载到车次代码库末尾，没有车次可以下载。')
                return
            no = train_no_dict[str(n)]           # 列车编号
            code = train_code_dict[str(n)]       # 车次
            form = self.trainType(code)     # 列车类型

            url = self.url + code.split('_')[0] + '.html'
            html = self.getHTML(url, code.split('_')[0])       # 调用函数
            try:
                """
                if html == 0:
                    for i in range(4):
                        time.sleep(random.randint(0, 2))
                        html = self.getHTML(url, code.split('_')[0])
                        if html != 0:
                            while code.split('_')[0] in self.invalid:
                                self.invalid.remove(code.split('_')[0])
                            break
                """
                if html == 0:
                    continue
                else:
                    info = self.analysisHTML(html, code.split('_')[0])       # 调用函数
                    start_s = info[0][0][1]
                    end_s = info[0][-1][1]
                    start_t = info[0][0][4]
                    end_t = info[0][-1][3]
                    km = info[0][-1][5]
                    period = info[0][-1][6]
                    item = {'No': no, 'code': code, 'type': form, 'start_s': start_s,
                            'end_s': end_s, 'start_t': start_t, 'end_t': end_t,
                            'km': km, 'period': period, 'info': info[0], 'key': info[1]}
                    self.collection.insert_one(item)
                    print('   {:04d}: 下载【{}  {} - {}】次列车信息完成...'.format(n, code, start_s, end_s))
                    count += 1
                    # time.sleep(random.randint(0, 2))
            except (Exception, TypeError):
                self.invalid.append(code.split('_')[0])
                continue
        self.invalid = list(set(self.invalid))  #去重
        if len(self.invalid) == 0:
            print('-> 本次下载完成，本次共下载了%d次列车的信息。' % count)
        else:
            print('-> 本次下载完成，本次共下载了{}次列车的信息，还有如下车次没能完成下载。\n{}'.format(count, self.invalid))

        self.writeLog(count, train_code_dict[str(self.last_sum+self.this_num-1)], self.invalid)
        return

    def patchInvalid(self):
        with open(self.log_filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        code_list = []
        """
        下面这段是将logging文件中的车次提取出来，很费劲，早知不用txt存储了
        """
        for line in lines[2:]:
            begin = line.find('[')
            end = line.rfind(']')
            ss = line[begin + 1: end].replace("'", "").replace(" ", "")
            if len(ss) == 0:
                continue
            else:
                ss = ss.split(',')
            code_list = code_list + ss
        print('-> 载入车次代码库成功，开始下载车次信息.....')
        count = 0
        with open(self.in_filename, 'r', encoding='utf-8') as f:
            trains_data = f.read()
        trains_data = json.loads(trains_data)
        train_no_dict = trains_data['train_no']
        train_code_dict = trains_data['train_code']
        code_list = list(set(code_list))

        for code_n in code_list:
            try:
                num = list(filter(lambda k: train_code_dict[k] == code_n, train_code_dict))[0]
            except (Exception, IndexError):
                self.invalid.append(code_n)
                continue
            no = train_no_dict[num]  # 列车编号
            code = train_code_dict[num]  # 车次
            form = self.trainType(code)  # 列车类型
            url = self.url + code_n + '.html'
            html = self.getHTML(url, code_n)  # 调用函数
            try:
                if html == 0:
                    continue
                else:
                    info = self.analysisHTML(html, code_n)  # 调用函数
                    start_s = info[0][0][1]
                    end_s = info[0][-1][1]
                    start_t = info[0][0][4]
                    end_t = info[0][-1][3]
                    km = info[0][-1][5]
                    period = info[0][-1][6]
                    item = {'No': no, 'code': code, 'type': form, 'start_s': start_s,
                            'end_s': end_s, 'start_t': start_t, 'end_t': end_t,
                            'km': km, 'period': period, 'info': info[0], 'key': info[1]}
                    self.collection.insert_one(item)
                    print('   {:04d}: 下载【{}  {} - {}】次列车信息完成...'.format(int(num), code, start_s, end_s))
                    count += 1
                    # time.sleep(random.randint(0, 2))
            except (Exception, TypeError):
                self.invalid.append(code.split('_')[0])
                continue
        if len(self.invalid) == 0:
            print('-> 本次下载完成，本次共下载了%d次列车的信息。' % count)
        else:
            print('-> 本次下载完成，本次共下载了{}次列车的信息，还有如下车次没能完成下载。\n{}'.format(count, self.invalid))


def main():
    """
    with open("data/logging.log", 'r', encoding='utf-8') as f:
        lines = f.readlines()
    last_line = lines[-1].split(',')
    this_num = int(input('-> {}下载到{}，下载的最后一个车次是{}\n-> '
                         '请输入本次要下载的数量（如果运行的是patch，可以随便输入数字）：'
                         .format(last_line[0], int(last_line[1]) - 1, last_line[3])))
    last_sum = int(last_line[1])        # 获取已下载的总数量
    """
    get_train_info = GetTrainInfo(8314, 0)
    get_train_info.saveToMongoDB()
    get_train_info.patchInvalid()


if __name__ == '__main__':
    main()
