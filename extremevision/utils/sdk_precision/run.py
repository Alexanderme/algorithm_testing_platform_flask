from bs4 import BeautifulSoup
import os
import requests
import time
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(os.path.abspath(__file__)))
RES_DIR = os.path.abspath(os.path.join(os.path.abspath(BASE_DIR), "input"))

# 要移动的路径
res_xml_path = os.path.join(RES_DIR, "ground-truth")
# 要移动的结果路径
res_txt_path = os.path.join(RES_DIR, 'detection-results')
ori_json = os.path.join(BASE_DIR, '.temp_files')


def clear_dirs():
    # 先清空文件夹 在创建文件夹
    if os.path.exists(RES_DIR):
        shutil.rmtree(RES_DIR)
    if os.path.exists(ori_json):
        shutil.rmtree(ori_json)
    # 创建需要的文件夹
    os.mkdir(RES_DIR)
    detection_results = os.path.join(RES_DIR, "detection-results")
    ground_truth = os.path.join(RES_DIR, "ground-truth")
    files = os.path.join(RES_DIR, "files")
    os.makedirs(detection_results)
    os.makedirs(ground_truth)
    os.makedirs(files)


def iter_files(rootDir, port, names, alert_info="alert_info", host="127.0.0.1"):
    for root, dirs, files in os.walk(rootDir):
        for file in files:
            if file.lower().endswith('xml'):
                xml_create(file, root)
            if file.lower().endswith('jpg') or file.lower().endswith('png') or file.lower().endswith('jpeg'):
                txt_create(file, root, host, port, names, alert_info)
        for dir in dirs:
            iter_files(dir, port, names, alert_info="alert_info", host="127.0.0.1")


def xml_create(file, root):
    name_txt = file.split('.')[0] + ".txt"
    with open(os.path.join(root, file), "rb") as f:
        file_b = f.read()
    soup = BeautifulSoup(file_b, 'lxml')
    object_all = soup.find_all("object")
    for i in object_all:
        name = i.find_all("name")[0].string
        for m in i.find_all("bndbox"):
            xmin = m.find_all("xmin")[0].string
            ymin = m.find_all("ymin")[0].string
            xmax = m.find_all("xmax")[0].string
            ymax = m.find_all("ymax")[0].string
            with open(os.path.join(res_xml_path, name_txt), "a") as f:
                f.write(
                    "%s %s %s %s %s\n" % (name, int(float(xmin)), int(float(ymin)), int(float(xmax)), int(float(ymax))))


def txt_create(file, root, host, port, names, alert_info="alert_info"):
    url_dir = "/api/analysisImage"
    url = "http://" + host + ":" + str(port) + url_dir
    with open(os.path.join(root, file), "rb") as f:
        fb = f.read()
    data = {
        "image": fb
    }
    response = requests.post(url, files=data)
    res_index = response.json().get("result").get(alert_info)
    if res_index is None or res_index == [] or res_index == 'null' or res_index == 'Null' or res_index == 'NULL':
        name_txt = file.split('.')[0] + ".txt"
        with open(os.path.join(res_txt_path, name_txt), "a") as f:
            f.write("\n")
        return
    for res in res_index:
        name_txt = file.split('.')[0] + ".txt"
        if res.get('confidence') is not None:
            confidence = res.get('confidence')
        else:
            confidence = "1"
        for name in names:
            if res.get(name) is not None:
                name = res.get(name)
                x = res.get('x')
                y = res.get('y')
                width = res.get('width') + x
                height = res.get('height') + y
                with open(os.path.join(res_txt_path, name_txt), "a") as f:
                    f.write("%s %s %s %s %s %s\n" % (name, confidence, x, y, width, height))
            else:
                x = res.get('x')
                y = res.get('y')
                width = res.get('width') + x
                height = res.get('height') + y
                with open(os.path.join(res_txt_path, name_txt), "a") as f:
                    f.write("%s %s %s %s %s %s\n" % (name, confidence, x, y, width, height))
