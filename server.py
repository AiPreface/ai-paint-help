import json
import subprocess
import sys
import os
import time
import threading
import flask
from flask import request
import random
app = flask.Flask(__name__)

py_path = os.path.abspath(os.curdir)
config = {}
waiting_start = False
should_wait = True


@app.before_request
def auth_login():
    au = request.headers.get("Authorization")
    if not au == config["Authorization"]:
        return "Authorization Error", 403
    else:
        return None
def get_target(port):
    with os.popen(f'netstat -aon|findstr "{port}"') as res:
        res = res.read().split('\n')
    result = []
    for line in res:
        temp = [i for i in line.split(' ') if i != '']
        if len(temp) > 4:
            result.append({'pid': temp[4], 'address': temp[1], 'state': temp[3]})
    target = ""
    for i in result:
        if i["state"] == "LISTENING":
            target = i["pid"]
    return target

@app.route("/start")
def start():
    target = get_target(config["webui_port"])
    if target != "":
        return "该程序已经启动...",200
    if waiting_start:
        return "等待程序启动...",200
    subprocess.Popen("start "+os.path.join(py_path,config["start"]+" cmd /k"),shell=True)
    global should_wait
    should_wait = True
    thread = threading.Thread(target=wait_for_start)
    thread.start()
    return "ok",200

@app.route("/download")
def download():
    return "Building",200

def wait_for_start():
    global waiting_start
    global should_wait
    while 1:
        if not should_wait:
            should_wait = True
            return
        time.sleep(1)
        target = get_target(config["webui_port"])
        if target == "":
            waiting_start = True
            continue
        else:
            waiting_start = False
            return


@app.route("/stop")
def stop():
    target = get_target(config["webui_port"])
    result = os.popen(f"taskkill -pid {target} -f").read()
    global waiting_start
    global should_wait
    if waiting_start:
        return "正在启动,需要等一下才能够关闭", 200
    if result == "":
        return "早已被关闭...",200
    return result,200

@app.route("/init")
def init_():
    global waiting_start
    global  should_wait
    global config
    config = json.loads(open(os.path.join(py_path, "server_config.ini"), "r").read())
    waiting_start = False
    should_wait = True
    return "重新初始化完成，你确定以无程序运行",200


if __name__ == "__main__":
    if not os.path.exists(os.path.join(py_path,"server_config.ini")):
        print("找不到配置文件...")
        config={"listen_port":6980,"listen_address":"0.0.0.0","webui_port":7860,"start":"webui.bat","Authorization":"".join(random.sample('abcdefghijklmnopqrstuvwxyz!@#$%^&*()',10))}
        with open(os.path.join(py_path,"server_config.ini"),"w") as f:
            f.write(json.dumps(config))
        print("已生成默认配置文件，请修改后重试...")
        os.system("pause")
        sys.exit()
    config = json.loads(open(os.path.join(py_path,"server_config.ini"),"r").read())
    app.run(port=config["listen_port"],host=config["listen_address"],threaded=True)





