#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from pymongo import MongoClient
from selenium.common.exceptions import ElementNotVisibleException


# noinspection PyPep8Naming
class HuntTelecode(object):
    def __init__(self):
        self.client = MongoClient('localhost', port=27017)
        self.db = self.client.train
        self.telecode_db = self.db.StationTelecode
        self.station_db = self.db.Station

        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--headless')  # 使用headless无界面浏览器模式增加无界面选项
        self.chrome_options.add_argument('--disable-gpu')  # 如果不加这个选项，有时定位会出现问题
        self.browser = webdriver.Chrome(options=self.chrome_options)

        self.file_logging = "data/logging_telecode.log"
        self.file_base = "data/station_base.csv"
        self.downloaded = []
        self.error, self.invalid = [], []
        self.count = 0

    @staticmethod
    def utfToUnicode(name):
        """
        -- 将中文车站名称转换为Unicode
        :param name: str,车站名称
        :return:str:'Unicode格式的车站名称'
        """
        n_temp = name.encode("unicode_escape")
        n_temp = repr(n_temp).replace("'", "").split('\\')[1:]
        while '' in n_temp:
            n_temp.remove('')
        unicode_name = '%'.join(n_temp)
        return unicode_name

    def loadBaseData(self):
        """
        -- 载入车站名称的原始数据并去重后转换为列表
        :return: list:[车站名称]
        """
        station_df = pd.read_csv(self.file_base)
        station_df = station_df.drop_duplicates(subset='0', keep='first', inplace=False)
        stations = station_df['0'].values.tolist()
        return stations

    def getHTML(self, name, unicode_name):
        """
        使用selenium得到网页源码，用BeautifulSoup转换为html格式
        :param name:str,车站名称
        :param unicode_name:str,转换为unicode格式的车站名称
        :return:bs4.element.Tag:<网页源码>
        """
        url = 'https://moerail.ml/#%' + unicode_name
        try:
            self.browser.get(url)
            reps = self.browser.page_source
            html = BeautifulSoup(reps, 'lxml')
        except ElementNotVisibleException:
            html = self.writeLog(name)
            return html
        return html

    def analysisHTML(self, name, html):
        """
        -- 对网页进行拆解，提取条目信息，放弃重复获取的条目
        :param name: str,车站名称
        :param html: bs4.element.Tag,网页源码
        :return: dict:{包含条目数据的字典}
        """
        try:
            html_td = html.find('tbody').find_all('td')
            if html_td[4].text in self.downloaded:
                item = self.writeLog(name)
                return item
            else:
                item = {
                    'name': name,
                    'Bureau': html_td[2].find('span').string,
                    'province': html_td[3].text,
                    'telecode': html_td[4].text,
                    'pinyin': html_td[5].text,
                    'tmis': html_td[6].text
                }
        except (Exception, TypeError):
            item = self.writeLog(name)
            return item
        return item

    def writeLog(self, name):
        """
        -- 将捕获的错误车站名称加入列表，写入日志文件，返回'Error'
        :param name: str,车站名称
        :return: str:'Error'
        """
        self.error.append(name)
        with open(self.file_logging, 'a', encoding='utf-8') as f:
            f.write('%s,' % name)
        print('-> %s 获取信息出错，已保存到错误日志中...' % name)
        return 'Error'

    def saveData(self):
        """
        下载全部车站信息并保存到数据库，捕获错误信息
        """
        stations = self.loadBaseData()      # 载入原始数据
        for n in stations:
            unicode_name = self.utfToUnicode(n)     # 将中文车站名称转换为unicode
            html = self.getHTML(n, unicode_name)    # 用selenium获取网页代码
            if html == 'Error':
                continue
            else:
                item = self.analysisHTML(n, html)   # 分解网页代码
                if item == 'Error':
                    continue
                else:
                    self.telecode_db.insert_one(item)       # 保存数据
                    self.downloaded.append(item['telecode'])
                    self.count += 1
                    print('{1:{0}>8}: OK'.format(chr(12288), n))
        print('-> 下载完成，本次共下载了{}个车站的信息，还有{}个车次没能完成下载。\n{}'
              .format(self.count, len(self.error), self.error))
        return

    def findInMongoDB(self):
        """
        在原数据库中查找saveData返回错误的信息，获取code值保存到数据库
        """
        df = pd.DataFrame(self.telecode_db.find({}, {'_id': 0}))
        mongodb_count = 0
        for n in self.error:
            request = df[df['name'].isin([n])]
            if request.shape[0] == 0:
                self.invalid.append(n)
                continue
            else:
                item = {
                    'name': n,
                    'Bureau': '',
                    'province': '',
                    'telecode': '-' + request.iat[0, 1],
                    'pinyin': '',
                    'tmis': ''
                }
                self.telecode_db.insert_one(item)
                mongodb_count += 1
                print('{1:{0}>8}: mongoDB+ OK'.format(chr(12288), n))
        print('-> 在mongoDB中追加了{}个信息，如下{}个车站仍旧无法获取信息。\n{}'
              .format(mongodb_count, len(self.invalid), self.invalid))
        return

    def patchInvalid(self):
        """
        将不能下载，原数据库中也没有的车站名称加入数据库中
        """
        invalid_count = 0
        for n in self.invalid:
            item = {
                'name': n,
                'Bureau': '',
                'province': '',
                'telecode': '-',
                'pinyin': '',
                'tmis': ''
            }
            self.telecode_db.insert_one(item)
            invalid_count += 1
            print('{1:{0}>8}: invalid+ OK'.format(chr(12288), n))
        print('-> 已将{}个无效的信息添加到数据库中。'.format(invalid_count))


def main():
    hunter = HuntTelecode()
    hunter.saveData()
    hunter.findInMongoDB()
    hunter.patchInvalid()


if __name__ == '__main__':
    main()
