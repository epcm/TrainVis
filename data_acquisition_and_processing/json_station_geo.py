#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
import pandas as pd
from pymongo import MongoClient


# noinspection PyPep8Naming
class CreateGeoJson(object):
    def __init__(self):
        self.client = MongoClient('localhost', port=27017)
        self.db = self.client.train
        self.station = self.db.StationGeo

        self.station_df = pd.DataFrame(self.station.find({}, {'_id': 0}))
        self.station_df = self.station_df.drop_duplicates(subset='name', keep='first', inplace=False)
        self.file_json = "data/station_geo.json"

    def outputJsonFile(self):
        name = self.station_df.name.tolist()
        lon = self.station_df.lon.tolist()
        lat = self.station_df.lat.tolist()
        geo = {}
        for n, value in enumerate(name):
            geo.update({value: [float(lon[n]), float(lat[n])]})
        geo_json = json.dumps(geo, ensure_ascii=False)
        with open(self.file_json, 'w', encoding='utf-8') as f:
            f.write(geo_json)
        print('车站地理位置坐标Json文件创建完成。')


def main():
    create_geo_json = CreateGeoJson()
    create_geo_json.outputJsonFile()


if __name__ == '__main__':
    main()
