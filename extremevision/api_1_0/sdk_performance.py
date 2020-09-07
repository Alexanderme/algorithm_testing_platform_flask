"""
    #  @ModuleName: sdk_performance
    #  @Function: 
    #  @Author: Ljx
    #  @Time: 2020/7/28 9:49
"""

from . import api
from flask import request, jsonify
from extremevision.sdk_config import run_sdk_config_GPU
from extremevision.utils.response_codes import RET
from extremevision.utils.connect_server import ParamikoCentos
from werkzeug.utils import secure_filename
from extremevision.api_1_0.sdk_subprocess import sdk_subprocess
import subprocess
import datetime
import os
import re

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 设置服务器全局变量
server = None


@api.route('/algo_sdk/connect_server', methods=['POST'])
def connect_server():
    res_datas = request.values
    print(res_datas)
    server_ip = res_datas.get('server_ip')
    server_port = int(res_datas.get('server_port'))
    server_user = res_datas.get('server_user')
    server_passwd = res_datas.get('server_passwd')
    print(server_ip, server_port, server_user, server_passwd)
    if not all([server_ip, server_port, server_user, server_passwd]):
        return jsonify(error=RET.DATAERR, errmsg="传入数据不完整")

    if int(server_port) < 0 or int(server_port) > 65000:
        return jsonify(error=RET.DATAERR, errmsg="端口填写错误")
    global server
    server = ParamikoCentos(hostname=server_ip, username=server_user, password=server_passwd, port=server_port)
    try:
        server.type_login_root()
    except Exception as e:
        return jsonify(error=RET.SERVERERR, errmsg="连接服务器失败")
    return jsonify(error=RET.OK, errmsg="服务器连接成功")


@api.route('/algo_sdk/resource_occupation', methods=["POST"])
def sdk_resource_occupation():
    """
    用于验证算法占用服务器资源信息
    :return:
    """
    # 1:接收镜像等参数  image_name, pic,
    # 2:运行sdk镜像算法一段时间
    # 3:返回资源占用  GPU 计算初始值,结束值相减  cpu 内存

    res_datas = request.values
    pic_file = request.files.get('pic_file')
    image_name = res_datas.get('image_name')

    global server

    if server is None:
        return jsonify(errno=RET.SERVERERR, errmsg='请先连接服务器')
    filename = pic_file.filename
    EXTREMEVISION_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
    files_dir = os.path.join(EXTREMEVISION_DIR, "libs/shell").replace("\\", "/")
    file_name = os.path.join(files_dir, filename).replace("\\", "/")
    secure_filename(filename)
    pic_file.save(file_name)

    pattern = re.compile("(/.*?):(.*?) ")
    remote_dir = re.findall(pattern, run_sdk_config_GPU)[0][0]
    print(remote_dir)

    res_sftp_put = server.sftp_put_dir('extremevision/libs/shell', remote_dir)
    #print('res_sftp_put', res_sftp_put)
    #if not res_sftp_put:
     #   return jsonify(errno=RET.SERVERERR, errmsg='批量上传文件失败')

    # 获取到容器id
    try:
        contain_id = server.exec_command(run_sdk_config_GPU + f"{image_name}")[:8]
    except Exception as e:
        return jsonify(errno=RET.SERVERERR, errmsg='请先连服务器')

    # 执行授权文件, 并且运行算法
    server.exec_command(f"docker exec  {contain_id} bash /tmp/sdk_resource_occupation.sh")
    server.exec_command(f"docker exec  -t  {contain_id} python3 /tmp/get_remote_use.py {filename}")
    
    os.system("touch /tmp/ljx/res_used.txt")
    with open("/tmp/ljx/res_used.txt", 'r') as f:
        res = f.read().splitlines()
    
    cmd = f"rm -rf /tmp/ljx/*; docker stop {contain_id}"
    status, _ = sdk_subprocess(cmd)
    if not status:
        return jsonify(errno=RET.DATAERR, msg=res)

    return jsonify(errno=RET.OK, errmsg=res)

@api.route('/algo_sdk/package_vas', methods=['POST'])
def deal_with_vas():
    """
    # 封装vas
    :param algo_image:  接收传入的镜像名称:image_name,
    :return:
    """
    res_datas = request.json
    port = res_datas.get('port')
    image_name = res_datas.get('image_name')
    vas_version = res_datas.get('vas_version')

    # 获取到容器id
    cmd_run_sdk = run_sdk_config_GPU + f"-p {port}:80 {image_name}"
    status, res = sdk_subprocess(cmd_run_sdk)
    if status:
        contain_id = res
    else:
        return jsonify(errno=RET.DATAERR, msg=res)

    global server

    if server is None:
        return jsonify(errno=RET.SERVERERR, errmsg='请先连接服务器')

    # 判断命令上传封装的ias包p
    if vas_version == '3.4':
        cmd = f"cp {path}/sdk_package/ias/ias_3.4.tar.gz /tmp/ljx;tar -xvf /tmp/ljx/ias_3.4.tar.gz -C /tmp/ljx"
        status, _ = sdk_subprocess(cmd)
        if not status:
            return jsonify(errno=RET.DATAERR, msg=res)
    else:
        cmd = f"cp {path}/sdk_package/ias/ias_4.1.tar.gz /tmp/ljx;tar -xvf /tmp/ljx/ias_4.1.tar.gz -C /tmp/ljx"
        status, _ = sdk_subprocess(cmd)
        if not status:
            return jsonify(errno=RET.DATAERR, msg=res)

    # 上传成功之后解压 安装
    ias_install = f"docker exec  {contain_id} bash /tmp/give_license.sh &"
    subprocess.Popen(ias_install, shell=True)
    #os.system(ias_install)

    return jsonify(errno=RET.OK, errmsg='封装ias成功')

@api.route('/algo_sdk/openvino_performance', methods=["POST"])
def sdk_openvino_performance():
    res_datas = request.values
    image_name = res_datas.get('image_name')

    global server
    if server is None:
        return jsonify(errno=RET.SERVERERR, errmsg='请先连接服务器')



def get_total_seconds(info):
    begin_time = f"cat {info}|grep event |awk -F" " '{print $2}'|head -1"
    end_time = f"tac {info}|grep event |awk -F" " '{print $2}'|head -1"
    run_times = f"cat {info} |grep event |wc -l"

    begin_time = datetime.strptime(begin_time, '%H:%M:%S.%f')
    end_time = datetime.strptime(end_time, '%H:%M:%S.%f')
    use_time = (end_time - begin_time).seconds

    fps = int(run_times / use_time)
    return fps
