from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import json
import math
import copy

app = Flask(__name__)

# 利用起始位置和邻接矩阵计算最短路
def shortestPath(start_s, mgraph, sortby):
    stations = mgraph.index.tolist()
    start = 0
    for i in range(len(stations)):
        if start_s == stations[i]:
            start = i
    # 存储已知最小长度的节点编号 即是顺序
    passed = [start]
    nopass = [x for x in range(len(stations)) if x != start]

    dis = [item[sortby] for item in mgraph[start_s]]

    # 创建字典 为直接与start节点相邻的节点初始化路径
    dict_ = {}
    for i in range(len(dis)):
        if abs(dis[i] - 1e10) > 10:
            dict_[stations[i]] = [start_s]

    while len(nopass):
        idx = nopass[0]
        for i in nopass:
            if dis[i] < dis[idx]: idx = i

        nopass.remove(idx)
        passed.append(idx)

        for i in nopass:
            if dis[idx] + mgraph[stations[idx]][stations[i]][0] < dis[i]: 
                dis[i] = dis[idx] + mgraph[stations[idx]][stations[i]][0]
                dict_[stations[i]] = dict_[stations[idx]] + [stations[idx]]
    return dis,dict_

# 前端由此路由跳转到对应网页
@app.route("/StationVis", methods=['GET', 'POST'])
def StationVis():
    return app.send_static_file("StationVis.html")

@app.route("/TrainVis", methods=['GET', 'POST'])
def TrainVis():
    return app.send_static_file("TrainVis.html")

@app.route("/AccessVis", methods=['GET', 'POST'])
def AccessVis():
    return app.send_static_file("AccessVis.html")

@app.route("/ChartVis", methods=['GET', 'POST'])
def ChartVis():
    return app.send_static_file("ChartVis.html")

@app.route("/PathVis", methods=['GET', 'POST'])
def PathVis():
    return app.send_static_file("PathVis.html")

# 前端由此路由获取最短路信息的json串
@app.route("/GetPath", methods=['GET', 'POST'])
def GetPath():
    start = request.form.get('start')
    end = request.form.get('end')
    sortby = request.form.get('sortby')
    #print(start + end)
    df= pd.read_json("static/data/min_adjacency_table.json")
    dis = []
    dict_ = {}
    if sortby == "时间优先":
        dis,dict_ = shortestPath(start, df, 0)
    elif sortby == "距离优先":
        dis,dict_ = shortestPath(start, df, 1)
    stations = df.index.tolist()
    #print(stations)
    res = {}
    for i in range(len(stations)):
        if stations[i] == end:
            res['path'] = dict_[stations[i]]+[stations[i]]
            if sortby == "时间优先":
                res['time'] = str(dis[i])+" mins"
            elif sortby == "距离优先":
                res['time'] = str(dis[i])+" kms"
            return jsonify(res)
        #print(dict_[stations[i]], stations[i], dis[i])

@app.route("/", methods=['GET', 'POST'])
def root():
    return app.send_static_file("index.html")

if __name__=="__main__":
    app.run(debug=True)