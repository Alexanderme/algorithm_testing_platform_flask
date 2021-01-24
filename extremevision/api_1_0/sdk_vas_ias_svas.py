# @ModuleName: sdk_vas_ias_svas
# @Function:
# @Author: Ljx
# @Time: 2020/7/8 11:53
from . import api
from flask import request, jsonify
from extremevision.utils.response_codes import RET
from extremevision.sdk_config import run_sdk_config_GPU, request_host, opencv41_dir, opencv34_dir
from extremevision.api_1_0.sdk_subprocess import sdk_subprocess
import subprocess
import requests
import os

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
@api.route('/algo_sdk/package_ias', methods=['POST'])
def deal_with_ias():
    """
    # 封装ias
    :param algo_image:  接收传入的镜像名称:image_name,
    :return:
    """
    res_datas = request.values
    port = res_datas.get('port')
    port = int(port)
    image_name = res_datas.get('image_name')

    # 获取到容器id
    cmd = run_sdk_config_GPU + f"-p {port}:80 {image_name}"
    status, res = sdk_subprocess(cmd)
    print(res, "res")
    if status:
        contain_id = res[:12]
    elif "port is already" in res:
        return jsonify(errno=RET.DATAERR, errmsg="端口被占用请重新输入")
    else:
        return jsonify(errno=RET.DATAERR, errmsg="输入镜像名称有误请重新确认之后输入")

    # 获取OpenCV版本
    url = request_host + "/api/v1.0/algo_sdk/opencv_message"
    data = {
        "image_name": image_name
    }
    OpenCv = requests.post(url, data=data).json().get("OpenCv")

    # 判断命令上传封装的ias包p
    if OpenCv == 3.4:
        cmd = f"cp {path}/sdk_package/ias/ias_3.4.tar.gz /tmp/ljx;tar -xvf /tmp/ljx/ias_3.4.tar.gz -C /tmp/ljx"
        status, _ = sdk_subprocess(cmd)
        if not status:
            return jsonify(errno=RET.DATAERR, errmsg="封装失败,请联系管理员")
    else:
        cmd = f"cp {path}/sdk_package/ias/ias_4.1.tar.gz /tmp/ljx;tar -xvf /tmp/ljx/ias_4.1.tar.gz -C /tmp/ljx"
        status, _ = sdk_subprocess(cmd)
        if not status:
            return jsonify(errno=RET.DATAERR, errmsg="封装失败,请联系管理员")

    # 上传成功之后解压 安装
    ias_install = f"docker exec  {contain_id} bash /tmp/give_license.sh &"
    subprocess.Popen(ias_install, shell=True)

    return jsonify(errno=RET.OK, errmsg='封装IAS成功,可以直接调用IAS')



@api.route('/algo_sdk/opencv_message', methods=["POST"])
def sdk_opencv_message():
    """
    用于获取sdk的opencv版本等相关信息
    :return:
    """
    res_datas = request.values
    image_name = res_datas.get('image_name')
    sdk_version = 3

    # 获取到容器id
    cmd_run_sdk = run_sdk_config_GPU + f"{image_name}"
    status, res = sdk_subprocess(cmd_run_sdk)
    if status:
        contain_id = res[:12]
    else:
        return jsonify(errno=RET.DATAERR, errmsg="算法镜像不存在或者算法镜像有误,请确认之后再输入!")

    sdk_message = f"docker exec -it  {contain_id}  bash  -c 'cat /usr/local/ev_sdk/authorization/privateKey.pem'"
    res_p = subprocess.Popen(sdk_message, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = res_p.communicate()
    if "No such file or directory" not in stdout.decode('utf-8'):
        errmsg = "(1):算法SDK版本为3.0系列 配置路径为:/usr/local/ev_sdk/config/algo_config.json \n"
    else:
        sdk_version = 2
        errmsg = "(1):算法SDK版本为2.0系列 配置路径为:/usr/local/ev_sdk/model/algo_config.json \n"

    auth_message = f"docker exec -it  {contain_id}  bash  -c 'cat /usr/local/ev_sdk/3rd/license/lib/pkgconfig/ji_license.pc |grep -i version'"
    res_p = subprocess.Popen(auth_message, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = res_p.communicate()
    if not stdout.decode('utf-8').startswith("cat"):
        errmsg += "(2):当前默认应该使用最新的版本库20.1.3, 当前算法授权库版本为" + str(stdout.decode('utf-8'))
    else:
        errmsg += "(2):获取授权信息失败, 授权库不是最新的20.1.3" + "\n"

    opencv_message = f"docker exec -it  {contain_id}  bash ldd /usr/local/ev_sdk/lib/libji.so |egrep  'libopencv_core.so.4'"
    res_p = subprocess.Popen(opencv_message, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = res_p.communicate()
    if stdout.decode('utf-8') is not '':
        # 公私钥  配置文件 查看
        privateKey = f"docker exec -it  {contain_id}  bash  -c 'cat /usr/local/ev_sdk/authorization/privateKey.pem'"
        res_p = subprocess.Popen(privateKey, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = res_p.communicate()
        privateKey = stdout.decode('utf-8')
        algo_config = f"docker exec -it  {contain_id}  bash  -c 'cat /usr/local/ev_sdk/config/algo_config.json'"
        res_p = subprocess.Popen(algo_config, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = res_p.communicate()
        algo_config = stdout.decode('utf-8')
        errmsg += '(3):当前OpenCV版本为:3.4, vas安装包:vas_v4.3_cv3.4.tar.gz, ias安装包:ias_v4.90_cv3.4.tar.gz'
        OpenCv = 3.4
        if sdk_version == 2:
            privateKey = "不支持2.0系列算法"
            algo_config = "不支持2.0系列算法"
        stop = f"docker stop {contain_id}"
        subprocess.Popen(stop, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return jsonify(errno=RET.OK, errmsg=errmsg, privateKey=privateKey, algo_config=algo_config , OpenCv=OpenCv)
    else:
        privateKey = f"docker exec -it  {contain_id}  bash  -c 'cat /usr/local/ev_sdk/authorization/privateKey.pem'"
        res_p = subprocess.Popen(privateKey, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = res_p.communicate()
        privateKey = stdout.decode('utf-8')
        algo_config = f"docker exec -it  {contain_id}  bash  -c 'cat /usr/local/ev_sdk/config/algo_config.json'"
        res_p = subprocess.Popen(algo_config, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = res_p.communicate()
        algo_config = stdout.decode('utf-8')
        if sdk_version == 2:
            privateKey = "不支持2.0系列算法"
            algo_config = "不支持2.0系列算法"
        errmsg += '(3):当前OpenCV版本为:4.1, vas安装包:vas_v4.3_cv4.1.tar.gz, ias安装包:ias_v4.74_cv4.1.tar.gz '
        OpenCv = 4.1
        stop = f"docker stop {contain_id}"
        subprocess.Popen(stop, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return jsonify(errno=RET.OK, errmsg=errmsg, privateKey=privateKey, algo_config=algo_config , OpenCv=OpenCv)



from extremevision.sdk_config import opencv34_dir, opencv41_dir
@api.route('/algo_sdk/package_vas', methods=['POST'])
def deal_with_vas():
    """
    # 封装vas
    :param algo_image:  接收传入的镜像名称:image_name,
    :return:
    """
    res_datas = request.values
    image_name = res_datas.get('image_name')

    # 获取OpenCV版本
    url = request_host + "/api/v1.0/algo_sdk/opencv_message"
    data = {
        "image_name": image_name
    }
    OpenCv = requests.post(url, data=data).json().get("OpenCv")

    # 判断命令上传封装的ias包p
    if OpenCv == 3.4:
        docker_vas = f"docker build -t {image_name}_test --build-arg IMAGE_NAME={image_name} -f {opencv34_dir} ."
    else:
        docker_vas = f"docker build -t {image_name}_test --build-arg IMAGE_NAME={image_name} -f {opencv41_dir} ."
    status, res_docker_vas = sdk_subprocess(docker_vas)
    if not status:
        return jsonify(errno=RET.DATAERR, errmsg=f"封装失败,请联系管理员, {res_docker_vas}")

    # 上传成功之后解压 安装
    # 获取到容器id
    cmd = run_sdk_config_GPU + f"-p {image_name}_test"
    status, contain_id = sdk_subprocess(cmd)
    os.system(f"docker cp {path}/sdk_package/vas/authorzation.sh {contain_id}:/usr/local/ev_sdk ")
    os.system(f"docker exec  {contain_id} bash /usr/local/ev_sdk/authorzation.sh &")

    cmd = f"docker exec {contain_id} bash -c 'cat /usr/local/vas/vas_data/log/vas.INFO|grep \"ji_init return = 0\"'"
    status, res_code = sdk_subprocess(cmd)
    if not status:
        return jsonify(errno=RET.ALGOVERSIONERR, errmsg=f'封装VAS失败,{res_code}')
    if int(res_code[-1]) == 0:
        return jsonify(errno=RET.OK, errmsg='封装IAS成功,可以直接调用IAS')
    else:
        return jsonify(errno=RET.ALGOVERSIONERR, errmsg=f'封装VAS失败,{res_code}')