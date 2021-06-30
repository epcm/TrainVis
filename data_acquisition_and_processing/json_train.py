#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# import pdb
import json
import pandas as pd


# noinspection PyPep8Naming
class TrainInfo(object):
    def __init__(self):
        self.in_filename = "data/trains_base.json"       # 原始数据文件名
        self.out_filename = "data/trains.json"          # 输出存储车次数据的文件名

    def jsonTotxt(self):
        with open(self.in_filename, 'r', encoding='utf-8') as f:
            json_data = f.read()
        trains_data = json.loads(json_data)
        trains_list = []
        for n in trains_data:        # 用两个循环，把原数据中的各项数据分离提取出来，生成df格式
            for item in trains_data[n]:
                train_no = item['train_no']
                train_code = item['station_train_code'].split('(')[0]
                station_name = item['station_train_code'].split('(')[1].replace(')', '')
                trains_list.append([n, train_no, train_code, station_name])
        columns = ['type', 'train_no', 'train_code', 'station']
        trains_df = pd.DataFrame(columns=columns, data=trains_list)
        """
        下面这段：
        1、用duplicated判断重复项，再对查询到的所有重复行排序
        2、从全部数据中过滤所有重复的数据，生成重复和不重复的两段数据
        3、用groupby()，apply()对重复车次进行清洗合并，然后再与原不重复的数据进行合并
        很复杂，用了一下午，但还不是最优的写法
        """
        dup = trains_df[trains_df.duplicated('train_no', keep=False)].sort_values('train_no', ascending=True)
        no_dup = trains_df.append(dup).append(dup).drop_duplicates(subset=columns, keep=False)

        dup['train_code'] = dup['train_code'].apply(lambda x: '_' + x)
        dup = dup.groupby(by='train_no').sum()
        dup['train_code'] = dup['train_code'].apply(lambda x: x[1:])
        dup['type'] = dup['type'].apply(lambda x: x[: 1])
        dup['station'] = dup['station'].apply(lambda x: x.split('-')[0] + '-' + x.split('-')[-1])

        dup = dup.reset_index()
        trains_df = pd.merge(no_dup, dup, on=columns, how='outer')         # 查找两个集合的交集
        trains = trains_df[['train_no', 'train_code']]
        trains.to_json(self.out_filename)
        print('所有车次信息已保存到文件%s中。' % self.out_filename)


def main():
    train_info = TrainInfo()
    train_info.jsonTotxt()


if __name__ == '__main__':
    main()
