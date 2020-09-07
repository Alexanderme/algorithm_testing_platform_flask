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
from extremevision.utils.sdk_precision.run import iter_files, clear_dirs
from extremevision.api_1_0.sdk_subprocess import sdk_subprocess
import zipfile
import os


@api.route('/algo_sdk/get_files_result', methods=["POST"])
def get_files_result():
    """
    需要用户指定服务器中的图片,xml存放的路径  指定算法标签  报警字段默认alert_info="alert_info"
    :return:
    """
    res_datas = request.values
    file = request.files.get("files")
    tag_names = res_datas.get('tag_names')
    alert_info = res_datas.get('alert_info')
    port = res_datas.get('port')
    tag_names = tag_names.split(",")
    iou = res_datas.get('iou')   

    if not all([tag_names, port, iou, alert_info]):
        return jsonify(error=RET.DATAERR, errmsg="传入数据不完整")

    if iou is not None:
        if float(iou) > 1 or float(iou) < 0 :
           return jsonify(error=RET.DATAERR, errmsg="请传入正确的iou")

    filename = file.filename
    if not filename.lower().endswith('zip'):
        return jsonify(error=RET.DATAERR, errmsg="上传的图片和xml文件请打包zip格式上传")

    EXTREMEVISION_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
    files_dir = os.path.join(EXTREMEVISION_DIR, "utils/sdk_precision/input/files").replace("\\", "/")
    file_name = os.path.join(files_dir, filename).replace("\\", "/")
    secure_filename(filename)
    file.save(file_name)
    with zipfile.ZipFile(file_name, 'r') as f:
        f.extractall(files_dir)

    if alert_info is None:
        iter_files(files_dir, port, tag_names)
    else:
        iter_files(files_dir, port, tag_names, alert_info)
    files_dir = os.path.join(EXTREMEVISION_DIR, "utils/sdk_precision/main.py")
    if iou is None:
        cmd = f"python3 {files_dir}"
    else:
        cmd = f"python3 {files_dir} -t {iou}"

    os.system(cmd)

    file_res = os.path.join(EXTREMEVISION_DIR, "utils/sdk_precision/output/output.txt")
    with open(file_res, 'r') as f:
        res = f.read().splitlines()
        res = str(res).replace("'',", "\n")
    
    clear_dirs()
    contain_stop = "docker ps |grep %s|awk '{print $1}'|xargs docker stop"%port
    status, _ = sdk_subprocess(contain_stop)
    if not status:
        return jsonify(errno=RET.DATAERR, msg=res)
    return jsonify(errno=RET.OK, errmsg=str(res))
