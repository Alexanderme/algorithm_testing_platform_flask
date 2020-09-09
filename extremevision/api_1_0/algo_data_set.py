"""
    #  @ModuleName: algo_data_set
    #  @Function: 
    #  @Author: Ljx
    #  @Time: 2020/9/10 18:05
"""

from . import api
from flask import request, jsonify, Response
from xml.etree import ElementTree
from extremevision.utils.response_codes import RET
from werkzeug.utils import secure_filename
from collections import defaultdict
import uuid
import os
import random

from extremevision.tasks.algoDealWithFilesData import deal_with_files_data

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@api.route('/algo_sdk/image_data_set', methods=["POST"])
def algo_data_set():
    """
    用于验证图片数据集
    :return:
    """

    res_datas = request.values
    files = request.files.get("files")
    tag_suffix = res_datas.get("tag_suffix")
    file_suffix = res_datas.get("file_suffix")
    tag_kinds = res_datas.get("tag_kinds")

    tag_kinds = tag_kinds.replace(" ", "").split(',')
    port = random.randint(10000, 65000)

    # 上传文件到服务器
    filename = files.filename
    secure_filename(filename)
    if not filename.lower().endswith('zip'):
        return jsonify(error=RET.DATAERR, errmsg="上传的视频和文件只支持打包好的zip文件,请重新打包上传")
    random_str = ''.join([each for each in str(uuid.uuid1()).split('-')])
    files_dir = os.path.join(f"{path}", "tmp/datas_set/"+random_str)
    if not os.path.exists(files_dir):
        os.makedirs(files_dir)
    file_name = os.path.join(files_dir, filename)
    files.save(file_name)
    task = deal_with_files_data.delay(file_name, files_dir, port, file_suffix, tag_suffix, tag_kinds)

    return jsonify(errno=RET.OK, task_id=task.id)

@api.route('/algo_sdk/format_xml', methods=['POST'])
def format_xml():
    """
    用于格式化美化xml
    :return:
    """

    xml_file = request.files.get('xml_file')
    # 格式化xml
    indent = '\t'
    newline = '\n'
    level = 0
    if not all([xml_file]):
        return jsonify(error=RET.DATAERR, errmsg="传入数据不完整")

    # if indent is None:
    #     indent = '\t'
    # if newline is None:
    #     newline = '\n'
    # if level is None:
    #     level = 0

    filename = xml_file.filename
    if not filename.lower().endswith('zip'):
        return jsonify(error=RET.DATAERR, errmsg="上传的图片和xml文件请打包zip格式上传")

    random_str = ''.join([each for each in str(uuid.uuid1()).split('-')])
    files_dir = os.path.join(path, f"tmp/data_set_file/{random_str}")
    if not os.path.exists(files_dir):
        os.makedirs(files_dir)
    file_name = os.path.join(files_dir, filename)
    secure_filename(filename)
    xml_file.save(file_name)
    os.system(f"unzip {file_name} -d {files_dir}")
    os.system(f"rm -rf {file_name}")

    xml_files = iter_files(files_dir)
    for xml in xml_files:
        xml = os.path.join(files_dir, xml)
        tree = ElementTree.parse(xml)  # 解析test.xml这个文件，该文件内容如上文
        root = tree.getroot()  # 得到根元素，Element类
        root = prettyXml(root, indent, newline, level)  # 执行美化方法
        tree = ElementTree.ElementTree(root)  # 转换为可保存的结构
        tree.write(xml)  # 保存美化后的结果
    os.system(f"cd  {files_dir};tar -cPvf result_xml.tar *; mv result_xml.tar ..")
    res_xml = os.path.join(path, f"tmp/data_set_file/result_xml.tar")
    os.system(f"rm -rf {files_dir}")
    response = Response(send_file(res_xml), content_type='application/octet-stream')
    response.headers["Content-disposition"] = 'attachment; filename=result_xml.tar'
    return response



def iter_files(rootDir):
    """
    根据文件路径 返回文件名称 以及文件路径名称
    :param rootDir:
    :return:
    """
    filenames = []
    for root, dirs, files in os.walk(rootDir):
        for file in files:
            file = os.path.join(root, file)
            if file.lower().endswith("xml"):
                filenames.append(file)
        for dir in dirs:
            iter_files(dir)

    return filenames

def send_file(files):
    with open(files, 'rb') as targetfile:
        while 1:
            data = targetfile.read(20 * 1024 )  # 每次读取20M
            if not data:
                break
            yield data


def prettyXml(element, indent, newline, level=0):  # elemnt为传进来的Elment类，参数indent用于缩进，newline用于换行
    if element:  # 判断element是否有子元素
        if element.text == None or element.text.isspace():  # 如果element的text没有内容
            element.text = newline + indent * (level + 1)
        else:
            element.text = newline + indent * (level + 1) + element.text.strip() + newline + indent * (level + 1)
            # else:  # 此处两行如果把注释去掉，Element的text也会另起一行
    temp = list(element)  # 将elemnt转成list
    for subelement in temp:
        if temp.index(subelement) < (len(temp) - 1):  # 如果不是list的最后一个元素，说明下一个行是同级别元素的起始，缩进应一致
            subelement.tail = newline + indent * (level + 1)
        else:  # 如果是list的最后一个元素， 说明下一行是母元素的结束，缩进应该少一个
            subelement.tail = newline + indent * level
        prettyXml(subelement, indent, newline, level=level + 1)  # 对子元素进行递归操作
    return element



@api.route('/algo_sdk/data_set_taskstatus', methods=["GET"])
def data_set_taskstatus():
    res_datas = request.values
    task_id = res_datas.get('task_id')
    # 根据taskid 获取任务状态
    task = deal_with_files_data.AsyncResult(task_id)
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
            response['container_id'] = task.info['container_id']
            response['files_dir'] = task.info['files_dir']
    else:
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),
        }
    return jsonify(response)

@api.route('/algo_sdk/data_set_clean_env', methods=["post"])
def data_set_clean_env():
    res_datas = request.values
    container_id = res_datas.get("container_id")
    files_dir = res_datas.get("files_dir")
    os.system(f"docker stop {container_id}")
    # 删除 运行文件
    os.system(f"rm -rf {files_dir}")
    return jsonify(errno=RET.OK, errmsg="环境清理成功")
    
