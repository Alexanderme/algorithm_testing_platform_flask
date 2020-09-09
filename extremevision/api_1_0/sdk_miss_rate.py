"""
    #  @ModuleName: sdk_miss_rate
    #  @Function: 
    #  @Author: Ljx
    #  @Time: 2020/7/17 17:32
"""

from . import api
from flask import jsonify, request
from extremevision.utils.response_codes import RET
from werkzeug.utils import secure_filename
from extremevision.utils.sdk_precision.run import clear_dirs, run_files
from extremevision.api_1_0.sdk_subprocess import sdk_subprocess
from extremevision.sdk_config import request_host
import os
import uuid
import requests

path = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))

@api.route('/algo_sdk/get_files_result', methods=["POST"])
def get_files_result():
    """
    需要用户指定服务器中的图片,xml存放的路径  指定算法标签  报警字段默认alert_info="alert_info"
    :return:
    """
    res_datas = request.values
    files = request.files.get("files")
    tag_names = res_datas.get('tag_names')
    alert_info = res_datas.get('alert_info')
    port = res_datas.get('port')
    iou = res_datas.get('iou')
    image_name = res_datas.get("image_name")
    args = res_datas.get("args")
    tag_names = tag_names.split(",")

    if not all([tag_names, port, iou, alert_info]):
        return jsonify(error=RET.DATAERR, errmsg="传入数据不完整")

    if iou is not None:
        if float(iou) > 1 or float(iou) < 0 :
           return jsonify(error=RET.DATAERR, errmsg="请传入正确的iou")

    filename = files.filename
    if not filename.lower().endswith('zip'):
        return jsonify(error=RET.DATAERR, errmsg="上传的图片和xml文件请打包zip格式上传")

    random_str = ''.join([each for each in str(uuid.uuid1()).split('-')])
    files_dir = os.path.join(path, f"tmp/algo_miss_rate/{random_str}")
    if not os.path.exists(files_dir):
        os.makedirs(files_dir)
    file_name = os.path.join(files_dir, filename)
    secure_filename(filename)
    files.save(file_name)

    os.system(f"unzip {file_name} -d {files_dir}")
    os.system(f"rm -rf {file_name}")

    # 封装ias 启动算法
    url = request_host + "/api/v1.0/algo_sdk/package_ias"
    data = {
        "port": port,
        "image_name": image_name
    }
    res = requests.post(url, data=data).json().get("errno")
    if res != "0":
        return jsonify(error=RET.ALGOVERSIONERR, errmsg="封装ias失败")

    task = run_files.delay(files_dir, port, tag_names, iou, args, alert_info)

    return jsonify(errno=RET.OK, task_id=task.id)


@api.route('/algo_sdk/rate_taskstatus', methods=["GET"])
def rate_taskstatus():
    res_datas = request.values
    task_id = res_datas.get('task_id')
    # 根据taskid 获取任务状态
    task = run_files.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),
        }
    return jsonify(response)
