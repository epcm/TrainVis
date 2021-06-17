# 要添加一个新单元，输入 '# %%'
# 要添加一个新的标记单元，输入 '# %% [markdown]'
# %%
import itertools
from itertools import groupby
import pandas as pd
from pymongo import MongoClient
import json


# %%
class Node(object):
    def __init__(self):
        self.distance = 0
        self.time = 0
        self.lines = 0


# %%
class DataProcessor(object):
    def __init__(self):
        self.client = MongoClient('localhost', port=27017)
        self.db = self.client.train
        self.train = self.db.Train
        self.station = self.db.Station 

        self.train_df = pd.DataFrame(self.train.find({}, {'_id': 0}))
        self.train_df = self.train_df.drop_duplicates(subset='No', keep='first', inplace=False)

        self.station_df = pd.DataFrame(self.station.find({}, {'_id': 0}))
        self.station_df = self.station_df.drop_duplicates(subset='name', keep='first', inplace=False)

        self.mergedTrainLs = [] 
        self.adjacency_df = []
        self.type_dict = {'高速动车组': 'G', '普通动车组': 'D', '城际动车组': 'C', '快速': 'K',
                          '普快': '9', '直达特快': 'Z', '特快': 'T', '其他': 'O'}
                          
    def addTrainsOfStation(self):
        """
        将各个站点的经停列车加入Station表单
        :return: None
        """
        station = self.train_df.key.tolist()
        passby = list(zip(self.train_df.code, self.train_df.key))
        # 添加经过车站的列车
        trainsOfStation = {}
        for (code, names) in passby:
            for name in names:
                if name in trainsOfStation:
                    trainsOfStation[name].append(code)
                elif name != "":
                    trainsOfStation[name] = []
        for (name, codes) in trainsOfStation.items():
            #print(name, codes)              
            query = {"name":name}
            newvalues = { "$set": { "trains": codes } }
            self.station.update_one(query, newvalues)

    def generateMergedTrain(self):
        # 起止站作为第一特征，以距离作为第二特征量
        documentsDict = {}
        #counter = 0
        deleteLs = []
        for index,document in self.train_df.iterrows():
            start_s = document["start_s"]
            end_s = document["end_s"]
            km = document["km"]
            key1 = f"{start_s}-{end_s}-{km}"
            key2 = f"{end_s}-{start_s}-{km}"
            # counter += 1
            # if counter > 10:
            #     break
            # 起止有问题的不要
            if start_s == "" or end_s == "":
                #deleteLs.append(key1)
                continue
            # 分正向与反向两种情况讨论
            if key1 in documentsDict:
                documentsDict[key1]["forward"].append(document["code"])
            elif key2 in documentsDict:
                documentsDict[key2]["backward"].append(document["code"])
            else:
                documentsDict[key1] = {"start_s":start_s, "end_s":end_s, "type":document["type"],"distance":[], "time":[], "stations":[], "forward": [document["code"]], "backward":[]}

                prev = [0, 0, 0, 0, 0, 0, "0:00"]
                for item in document["info"]:
                    if item[1] == "": #筛去空站
                        continue
                    prev_t = prev[6].split(':')
                    prev_t = int(prev_t[0])*60+int(prev_t[1])
                    cur_t = item[6].split(':')
                    cur_t = int(cur_t[0])*60+int(cur_t[1])
                    # 出现时光倒流的不要
                    if cur_t < prev_t or int(item[5])-int(prev[5]) < 0:
                        documentsDict.pop(key1)
                        deleteLs.append(key1)
                        break
                    documentsDict[key1]["stations"].append(item[1])
                    documentsDict[key1]["distance"].append(int(item[5])-int(prev[5]))
                    documentsDict[key1]["time"].append(cur_t-prev_t)
                    prev = item
        self.mergedTrainLs = list(documentsDict.values())
        print("舍弃的列车:", len(deleteLs))
        print(deleteLs)


    # 构建邻接表
    def generateAdjacencyList(self):
        stationLs = self.station_df.name.tolist()
        #print(stationLs[:10])
        d = {col:pd.Series([[1e10, "", 1e10, "", 0]]*len(stationLs), index=stationLs) for col in stationLs}
        self.adjacency_df = pd.DataFrame(d)
        print("start")
        #print(pd.DataFrame(d))

    def test(self):
        stationLs = self.station_df.name.tolist()
        for item in self.mergedTrainLs:
            #print()
            stations = item["stations"]
            pre_time = []  #时间前缀和
            pre_dis =[]    #距离前缀和
            pre = 0
            for it in item["time"]:
                pre_time.append(it+pre)
                pre = it+pre
            pre = 0
            for it in item["distance"]:
                pre_dis.append(it+pre)
                pre = it+pre
            # 更新任意两站间的关系
            for i in range(len(stations)):
                if not (stations[i] in stationLs):
                    continue
                for j in range(i+1, len(stations)):
                    if not (stations[j] in stationLs):
                        continue
                    ls = self.adjacency_df[stations[i]][stations[j]].copy()
                    # 更新时间依据
                    if ls[0] > pre_time[j]-pre_time[i]:
                        ls[0] = pre_time[j]-pre_time[i]
                        ls[1] = item["type"]
                    # 更新空间依据
                    if ls[2] > pre_dis[j]-pre_dis[i]:
                        ls[2] = pre_dis[j]-pre_dis[i]
                        ls[3] = item["type"]
                    ls[4] += (len(item["forward"])+len(item["backward"]))
                    self.adjacency_df[stations[i]][stations[j]] = ls.copy()
                    self.adjacency_df[stations[j]][stations[i]] = ls.copy()
            print(item["start_s"]+item["end_s"]+"ok")
        
# 实例化数据处理器
processor = DataProcessor()


# %%
# 将同一线路的列车合并
processor.generateMergedTrain()


# %%
processor.generateAdjacencyList()


# %%
print(processor.mergedTrainLs[2])


# %%
processor.test()


# %%
print(processor.adjacency_df["北京南"]["上海虹桥"])



# %%



