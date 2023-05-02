import json
import pathlib
import subprocess
import sys
import os
import time
import threading
import traceback

import flask
from flask import request
import random
import aria2p

app = flask.Flask(__name__)

py_path = os.path.abspath(os.curdir)

config = {}
waiting_start = False
should_wait = True




@app.before_request
def auth_login():
    au = request.headers.get("Authorization")
    if not au == config["Authorization"]:
        return json.dumps({"status": "error", "msg": "Authorization Error"}), 403
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
        return "该程序已经启动...", 200
    if waiting_start:
        return "等待程序启动...", 200
    try:
        subprocess.Popen("start " + os.path.join(py_path, config["start"] + " cmd /k"), shell=True)
    except:
        return json.dumps({"status": "error", "msg": traceback.format_exc()}), 500
    global should_wait
    should_wait = True
    thread = threading.Thread(target=wait_for_start)
    thread.start()
    return json.dumps({"status": "ok"}), 200


@app.route("/download", methods=["POST"])
def download():
    data = request.form
    type = data["type"]

    save_path = ""
    if type == "ckpt":
        save_path = os.path.join(py_path, "models", "Stable-diffusion")

    elif type == "vae":
        save_path = os.path.join(py_path, "models", "VAE")
    elif type == "emb":
        save_path = os.path.join(py_path, "embeddings")
    elif type == "lora":
        save_path = os.path.join(py_path, "models", "models/Lora")
        pass
    else:
        return json.dumps({"status": "unkown_type", "msg": f"未知的类型:{type}"}), 500
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    try:
        file_path = data["file_url"]
    except KeyError:
        return json.dumps({"status": "give_download_url", "msg": "请给出下载链接"}), 500

    downloads = aria2.get_downloads()
    for i in downloads:
        if i.status == "error":
            in_download_stop(i.gid)
            continue
        for a in i.files:
            for b in a.uris:
                if b["uri"] == file_path and i.status != "complete":
                    return json.dumps(
                        {"status": "downloading", "file_path": file_path, "gid": i.gid, "status_download": i.status,
                         "msg": "所选链接正在下载中"}), 200
                elif i.status == "complete":
                    return json.dumps(
                        {"status": "download_complete", "file_path": file_path, "gid": i.gid, "status_download": i.status,
                         "msg": "所选链接下载完成"}), 200
                elif i.status == "error":
                    return json.dumps(
                        {"status": "download_error", "file_path": file_path, "gid": i.gid, "status_download": i.status,
                         "msg": "所选链接下载出错，请终止此下载任务后重新发送下载请求"}), 200
    aria2.add(file_path, options={"dir": save_path, "out": pathlib.Path(file_path).name})
    downloads = aria2.get_downloads()
    gid = ""
    for i in downloads:
        if i.name == pathlib.Path(file_path).name:
            gid = i.gid
    return json.dumps({"status": "ok", "msg": f"链接:{file_path}开始下载", "gid": gid}), 200


@app.route("/download_status")
def download_status():
    return_data = []
    downloads = aria2.get_downloads()
    for i in downloads:
        temp_dic = {"downloading": i.name, "status": i.status, "speed": i.download_speed_string(),
                    "total": i.total_length_string(), "finish": i.completed_length_string(), "gid": i.gid,
                    "details": []}
        # return_data +=f"下载文件:{i.name},状态:{i.status},速度:{i.download_speed_string()}\n,总计:{i.total_length_string()},下载完成:{i.completed_length_string()},gid:{i.gid}\n"
        for a in i.files:
            for b in a.uris:
                temp_dic["details"].append({"thread": b['uri'], "status": b['status']})
                # return_data +=f"    线程:链接:{b['uri']},状态:{b['status']},\n"
        return_data.append(temp_dic)

    return json.dumps(return_data), 200


def in_download_stop(gid):
    try:
        download_ = aria2.get_download(gid)
        download_.remove(force=True, files=True)
    except aria2p.client.ClientException:
        pass


@app.route("/download_stop/<gid>")
def download_stop(gid):
    try:
        download_ = aria2.get_download(gid)
    except aria2p.client.ClientException:
        return json.dumps({"status": "error", "msg": f"gid:{gid}无效", "gid": gid}), 500
    download_.remove(force=True, files=True)

    return json.dumps({"status": "ok", "msg": f"任务:{download_.name}已被停止...", "gid": gid}), 200


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
        return json.dumps({"status": "wait_for_start", "msg": "正在启动,需要等一下才能够关闭"}), 200
    if result == "":
        return json.dumps({"status": "has_stoped", "msg": "早已被关闭..."}), 200
    return json.dumps({"status": "ok", "msg": result}), 200


@app.route("/init")
def init_():
    global waiting_start
    global should_wait
    global config
    config = json.loads(open(os.path.join(py_path, "server_config.ini"), "r").read())
    waiting_start = False
    should_wait = True
    return json.dumps({"status": "ok", "msg": "重新初始化完成，你确定以无程序运行"}), 200


if __name__ == "__main__":
    if not os.path.exists(os.path.join(py_path, "server_config.ini")):
        print("找不到配置文件...")
        config = {"listen_port": 6980, "listen_address": "0.0.0.0", "webui_port": 7860, "start": "webui.bat",
                  "Authorization": "".join(random.sample('abcdefghijklmnopqrstuvwxyz!@#$%^&*()', 10)),"rpc-listen-port":6800,"secret":""}
        with open(os.path.join(py_path, "server_config.ini"), "w") as f:
            f.write(json.dumps(config))
        print("已生成默认配置文件，请修改后重试...")
        os.system("pause")
        sys.exit()
    config = json.loads(open(os.path.join(py_path, "server_config.ini"), "r").read())
    aria2 = aria2p.API(
        aria2p.Client(
            host="http://localhost",
            port=config["rpc-listen-port"],
            secret=config["secret"]
        )
    )
    app.run(port=config["listen_port"], host=config["listen_address"], threaded=True)
