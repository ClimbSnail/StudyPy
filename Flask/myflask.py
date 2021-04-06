from flask import Flask
from flask import render_template
from flask import request
from flask import Blueprint


app = Flask(__name__)

# 加入路由信息


def request_parse(req):
    '''解析请求数据并以json形式返回'''
    data = None
    try:
        if req.method == 'POST':
            data = req.json
        elif req.method == 'GET':
            data = str(dict(req.args)).replace("'", '"')
        elif req.method == 'PUT':
            data = str(req.get_data(), encoding="utf8")
        else:
            data = dict()
    except Exception as err:
        print(err)
    return data

@app.route("/")
def index():
    # 使用render_template，文件必须要同级目录的templates文件夹中
    return render_template("login.html")


@app.route("/login", methods=['POST', 'GET'])
def login():
    # 接收到用户名和密码（获取form表单中的数据）
    # {username:你写的内容 pwd:你写的内容}
    print("hello")
    username = request.form.get("username")
    password = request.form.get("pwd")
    print(username)
    # request.args.get()
    if username == "heqi" and password == 123:
        return "成功"
    else:
        # 使用render_template，文件必须要同级目录的templates文件夹中
        return render_template("login.html", msg="登录失败")


# 蓝图设置
url_prefix = "/v1/local/operations"
show_local_blueprint = Blueprint(
    'show_local',
    __name__,
    url_prefix=url_prefix
)


@show_local_blueprint.route("/hello")
def list_tags():
    return "world"


app.register_blueprint(show_local_blueprint)

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5001, debug=True)
