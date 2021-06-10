from flask import Flask, request, jsonify
app = Flask(__name__)
# 解决乱码问题

# 前端由此路由获取数据的json对象
@app.route("/getData1", methods=['GET', 'POST'])
def getData1():
    js = ""
    with open("static/PeopleInSubwayTime.json", "r", encoding='utf-8') as f:
        js = f.read()
    return js

@app.route("/getData2", methods=['GET', 'POST'])
def getData2():
    js = ""
    with open("static/PeopleInSubwayCount.json", "r", encoding='utf-8') as f:
        js = f.read()
    return js

@app.route("/", methods=['GET', 'POST'])
def root():
    return app.send_static_file("index.html")

if __name__=="__main__":
    app.run(debug=True)