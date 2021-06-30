# TrainVis 全国列车数据获取与可视化分析

本项目从不同网站爬取了全国3.3k车站和8.3k列车的信息，并使用echarts进行可视化，利用Flask+html将结果呈现在网页中

项目地址：https://github.com/epcm/TrainVis

注：图片使用github图床存储，若不能正常显示请尝试使用vpn越过Great Wall

## 效果展示

**StationVis**: 站点可视化，突出区域铁路交通中心

![image-20210630180135582](https://raw.githubusercontent.com/epcm/Pictures/master/Markdown/image-20210630180135582.png)

**TrainVis**: 列车线路可视化，突出铁路网络结构与交通流向

![](https://raw.githubusercontent.com/epcm/Pictures/master/Markdown/TrainVis.gif)

**AccessVis**: 区域可达性可视化，可达性取决于经停列车与直接相连城市

站点可达性=Σ可直接到达站点*站点权重 

![image-20210630180222740](https://raw.githubusercontent.com/epcm/Pictures/master/Markdown/image-20210630180222740.png)

**ChartVis**: 东部、中部、西北、东北地区大站间的连接关系

![image-20210630180248823](https://raw.githubusercontent.com/epcm/Pictures/master/Markdown/image-20210630180248823.png)

**PathVis**: 部分站点间的路径规划，可分别以时间与距离为依据

![image-20210630180323805](https://raw.githubusercontent.com/epcm/Pictures/master/Markdown/image-20210630180323805.png)

注：为了展示效果，图中仅截取了地图的一部分，南海、黑龙江省的可在网页中拖动查看

## 项目结构

.
├── README.md  
├── data_acquisition_and_processing  
│   ├── DataProcessor.ipynb  
│   ├── data  
│   │   ├── station_base.csv  
│   │   ├── station_geo.json  
│   │   ├── trains.json  
│   │   └── trains_base.json  
│   ├── json_station_geo.py  
│   ├── json_train.py  
│   ├── main.ipynb  
│   ├── spider_station_geo.py  
│   ├── spider_telecode.py  
│   └── spider_traininfo.py  
└── web_visualization  
    ├── main.py  
    └── static  
        ├── AccessVis.html  
        ├── ChartVis.html  
        ├── PathVis.html  
        ├── StationVis.html  
        ├── TrainVis.html  
        ├── data  
        │   ├── AccessInfo.json  
        │   ├── MapStyleConfig.json  
        │   ├── MergedTrainInfo.json  
        │   ├── RelationChartInfo.json  
        │   ├── StationGeo.json  
        │   ├── StationInfo.json  
        │   ├── TrainInfo.json  
        │   └── min_adjacency_table.json  
        ├── index.html  
        └── js  
            ├── bmap.js  
            ├── bmap.js.map  
            ├── echarts.js  
            ├── echarts.js.map  
            └── jquery-3.6.0.js   

## 使用

1. 安装python依赖

   `pip install flask pandas numpy`

2. 切换到`./web_visualization`

3. 运行`main.py`

4. 使用上方导航栏切换不同视图

5. 注意PathVis仅支持部分站点间的路径规划，支持的站点已在网页中使用黄色图标标记

   例如：起始站：`北京南`     终点站： `乌鲁木齐`    时间优先

   ​			起始站：`济南东`     终点站： `长沙南`       距离优先

   ​			注意不要在车站后加`站`字

## 数据获取与处理

本部分用以讲解数据的获取与处理过程，如仅想获得展示效果，此部分可以跳过

### 数据构建步骤

1. 切换到`./data_acquisition_and_processing`
2. 依次执行`main.ipynb`中各个模块
3. 将数据库中`train.StationGeo`复制为`train.Station`
4. 依次执行`DataProcessor.ipynb`中各个模块
5. 导出`train.Train`为`TrainInfo.json`，导出`train.Station`为`StationInfo.json`
6. 将生成的json文件放入`./web_visualization/static/data`

### 基础数据:

* `trains_base.json`:车次基础数据，来源：12306.cn
* `station_base.csv`:车站基础数据，来源：12306.cn

### 项目文件

#### 基础数据处理及爬虫文件

* `json_train.py`:根据车次基础数据提取所有车次信息和车次代号（去除冗余信息）
  * In：
    * data\train_base.json：车次基础数据
  * Out：
    * data\train.json：从基础数据中提取的车次数据文件
* `json_staion_geo`根据数据库中的车站信息生成json文件
  * In:
    * mongoDB.train.StationGeo：存储车站详细信息的集合
  * Out:
    * data\station_geo.json：存储车站地理位置信息的json文件
* `spider_telecode.py`:根据车站基础数据获取包含电报码的车站初步信息（在moerail.ml网站爬取）
  * In：
    * data\station_base.csv，车站基础数据
  * Out：
    * mongoDB.train.StationTelecode：数据库中存储包含电报码的车站初步信息集合
* `spider_station_geo.py`:根据车站初步信息生成地理位置信息（利用高德地图api获得）
  * In：
    * mongoDB.train.StationTelecode：数据库中存储车站详细信息的集合
  * Out：
    * mongoDB.train.StationGeo：存储车站地理位置信息的集合
* `spider_traininfo.py`:根据车次信息获取列车详细信息（在oklx.com网站爬取）
  * In：
    * data\train.json：全国所有车次数据文件
  * Out：
    * mongoDB.train.Train：数据库中存储车次详细信息的集合

#### 主文件

* `main.ipynb`:主程序，调用爬虫文件
* `DataProcessor.ipynb`:对爬取数据进行进一步处理
  * In：
    * mongoDB.train.Train：数据库中存储车次详细信息的集合
    * mongoDB.train.Station 数据库中存储车站详细信息的集合
  * Out：
    * AccessInfo.json
    * MergedTrainInfo.json
    * min_adjacency_table.json
    * RelationChartInfo.json


### 注释说明

* 车次基础数据来源：12306.cn
* 车站电报码信息来源：moerail.ml
* 车次详细信息来源：oklx.com(12306爬取速度太慢)
* 数据存储：mongoDB数据库（基于分布式文件存储的开源数据库系统，操作起来比较简单和容易）
* 获取车站基础数据3480个，生成有效地理位置数据3480个
* 获取获取车次基础数据共8314次，最终获取8220次，去重后8217次
* train.StationTelecode是生成train.StationGeo的过渡库



