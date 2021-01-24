"""
    #  @ModuleName: sdk_run_res_file
    #  @Function: 
    #  @Author: Ljx
    #  @Time: 2020/8/13 11:29
"""
from . import api
from flask import request, jsonify, Response
from extremevision.utils.response_codes import RET
from werkzeug.utils import secure_filename
from extremevision.sdk_config import request_host
from extremevision.tasks.algoRunResFiles import algo_ias_files
import os
import requests
import uuid
import random

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@api.route('/algo_sdk/run_file_get_results', methods=['POST'])
def run_file_get_results():
    """
    封装IAS 运行ias得到图片或者视频算法结果
    :return:
    """
    res_datas = request.values
    files = request.files.get("files")
    image_name = res_datas.get('image_name')
    args = res_datas.get('args')

    port = random.randint(10000, 65000)

    if not all([files, image_name]):
        return jsonify(error=RET.DATAERR, errmsg="传入数据不完整")

    filename = files.filename
    secure_filename(filename)
    if not filename.lower().endswith('zip'):
        return jsonify(error=RET.DATAERR, errmsg="上传的视频和文件只支持打包好的zip文件,请重新打包上传")

    # 封装ias 启动算法
    url = request_host + "/api/v1.0/algo_sdk/package_ias"
    data = {
        "port": port,
        "image_name": image_name
    }
    res = requests.post(url, data=data).json().get("errno")
    if res != "0":
        return jsonify(error=RET.ALGOVERSIONERR, errmsg="封装ias失败")

    random_str = ''.join([each for each in str(uuid.uuid1()).split('-')])
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 创建临时存放运行文件文件夹 和 算法运行结果文件夹
    ori_files_dir = os.path.join(parent_dir, f"tmp/algo_ias_files/ori_{random_str}")
    res_files_dir = os.path.join(parent_dir, f"tmp/algo_ias_files/res_{random_str}")
    os.makedirs(ori_files_dir)
    os.makedirs(res_files_dir)

    # 第二步上传文件到服务器
    file_name = os.path.join(ori_files_dir, filename)
    files.save(file_name)

    task = algo_ias_files.delay(ori_files_dir, res_files_dir, file_name, port, args, random_str)

    return jsonify(errno=RET.OK, task_id=task.id)


@api.route('/algo_sdk/taskstatus', methods=["GET"])
def taskstatus():
    res_datas = request.values
    task_id = res_datas.get('task_id')
    # 根据taskid 获取任务状态
    task = algo_ias_files.AsyncResult(task_id)
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
            response['error_files'] = task.info['error_files']
            response['ori_files_dir'] = task.info['ori_files_dir']
            response['res_files_dir'] = task.info['res_files_dir']
            response['container_id'] = task.info['container_id']
     
    else:
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),
        }
    return jsonify(response)


@api.route('/algo_sdk/clear_env', methods=["POST"])
def clean_env():
    res_datas = request.values
    container_id = res_datas.get("container_id")
    ori_files_dir = res_datas.get("ori_files_dir")
    res_files_dir = res_datas.get("res_files_dir")

    if not all([container_id, ori_files_dir]):
        return jsonify(error=RET.DATAERR, errmsg=container_id)
    os.system(f"docker stop {container_id}")
    # 删除 运行文件
    os.system(f"rm -rf {ori_files_dir}")
    if res_files_dir != None:
        os.system(f"rm -rf {res_files_dir}")
    return jsonify(errno=RET.OK, errmsg="环境清理成功")


@api.route('/algo_sdk/get_results', methods=["POST"])
def get_results():
    res_datas = request.values
    files = res_datas.get("files")
    response = Response(send_file(files), content_type='application/octet-stream')
    response.headers["Content-disposition"] = 'attachment; filename=result.tar'
    return response


def send_file(files):
    with open(files, 'rb') as targetfile:
        while 1:
            data = targetfile.read(20 * 1024 )  # 每次读取20M
            if not data:
                break
            yield data
