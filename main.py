from flask import Flask, request, jsonify
app = Flask(__name__)
# 解决乱码问题

# 前端由此路由获取数据的json对象
@app.route("/StationVis", methods=['GET', 'POST'])
def StationVis():
    return app.send_static_file("StationVis.html")

@app.route("/TrainVis", methods=['GET', 'POST'])
def TrainVis():
    return app.send_static_file("TrainVis.html")

@app.route("/AccessVis", methods=['GET', 'POST'])
def AccessVis():
    return app.send_static_file("AccessVis.html")

@app.route("/PathVis", methods=['GET', 'POST'])
def PathVis():
    return app.send_static_file("PathVis.html")

@app.route("/", methods=['GET', 'POST'])
def root():
    return app.send_static_file("index.html")

if __name__=="__main__":
    app.run(debug=True)