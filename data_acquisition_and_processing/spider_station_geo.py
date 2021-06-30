'''
Author: your name
Date: 2021-06-02 18:45:47
LastEditTime: 2021-06-16 21:21:19
LastEditors: your name
Description: In User Settings Edit
FilePath: /PY_workspace/train-master/create_station_geo.py
'''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-




import json
import requests
import pandas as pd
from tqdm.std import trange
from pymongo import MongoClient


# noinspection PyPep8Naming
class CreateStationGeo(object):
    def __init__(self):
        self.client = MongoClient('localhost', port=27017)
        self.db = self.client.train
        self.station = self.db.StationTelecode
        self.geo = self.db.StationGeo

        self.key = '06b57dabf9f50fb058a599614798d0c3'  # 高德地图API的key
        self.file_logging = "data/logging_geo.log"        # 输出的的日志文件

        self.error = []

    def amapLocation(self, name, string):
        """
        -- 根据车站名称调用高德地图API查询省、市和经纬度
        :param name: str,车站名称
        :param string: list,['站', '火车站']
        :return: list:[省, 市, 经度, 纬度]
        """
        url = 'https://restapi.amap.com/v3/geocode/geo?address=' + name + string + '&key=' + self.key
        reps = requests.get(url)
        geo_data = json.loads(reps.text)

        if geo_data['count'] == '0':  # 不能生成地理位置坐标的数据，返回'Error'
            location_amap = 'Error'
        else:
            pos = geo_data['geocodes'][0]['location'].split(',')    # 分隔经纬度
            province = geo_data['geocodes'][0]['province']
            city = geo_data['geocodes'][0]['city']
            if len(city) == 0:      # 如果city返回空值，则取下面的district值
                city = geo_data['geocodes'][0]['district']
            location_amap = [province, city, pos[0], pos[1]]     # 返回省、市（区）、经纬度
        return location_amap

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
        根据车站名称调用高德地图API获得省、市、经纬度信息，保存到数据库中
        """
        stations_df = pd.DataFrame(self.station.find({}, {'_id': 0}))
        string = ['站', '火车站']
        for n in trange(stations_df.shape[0]):
            name = stations_df.iat[n, 0]
            telecode = stations_df.iat[n, 3]
            pinyin = stations_df.iat[n, 4]
            bureau = stations_df.iat[n, 1]
            location = self.amapLocation(name, string[0])
            if location == 'Error':
                location_1 = self.amapLocation(name, string[1])
                if location_1 == 'Error':
                    self.writeLog(name)
                else:
                    item = {'name': name, 'telecode': telecode, 'pinyin': pinyin, 'province': location_1[0],
                            'city': location_1[1], 'bureau': bureau, 'lon': location_1[2], 'lat': location_1[3]}
                    self.geo.insert_one(item)
            else:
                item = {
                    'name': name, 'telecode': telecode, 'pinyin': pinyin, 'province': location[0],
                    'city': location[1], 'bureau': bureau, 'lon': location[2], 'lat': location[3]}
                self.geo.insert_one(item)
        return


def main():
    geo = CreateStationGeo()
    geo.saveData()


if __name__ == '__main__':
    main()
