"""
    #  @ModuleName: algoDealWithFilesData
    #  @Function: 
    #  @Author: Ljx
    #  @Time: 2020/9/7 15:02
"""
from extremevision import celery
from flask import jsonify
from extremevision.utils.response_codes import RET
from collections import defaultdict
import os
import requests
import chardet
import re
import time
from xml.etree.ElementTree import parse

from extremevision.sdk_config import request_host, request_host_without_port
error_files_list = defaultdict(list)

@celery.task(bind=True)
def deal_with_files_data(self, file_name, files_dir, port, file_suffix, tag_suffix, tag_kinds):
    # 解压
    os.system(f"unzip {file_name} -d {files_dir}")
    # 删除文件
    os.system(f"rm -f {file_name}")
    total_files = iter_files(files_dir)

    # 封装ias 启动算法
    url = request_host + "/api/v1.0/algo_sdk/package_ias"
    data = {
        "port": port,
        "image_name": "ccr.ccs.tencentyun.com/source/dev_helmet_kww_cpu_sdk3.0_modc_uni_lic1b:v1.1.1"
    }
    res = requests.post(url, data=data).json().get("errno")
    if res != "0":
        return jsonify(error=RET.ALGOVERSIONERR, errmsg="封装ias失败")
   
    # 遍历
    # 验证文件和标签数据是否一致  判断文集和标签是否以指定文件后缀统一格式
    files_tag = total_files["files_tag"]
    files = total_files["files"]
    for file_tag, file in zip(files_tag, files):
        # 判断文件和标注文件命名是否匹配
        if file_tag.split(".")[0] != file.split(".")[0]:
            error_files_list["filename_not_match"].append(file)
        # 判断是否是以否以指定后缀命名
        if not file.endswith(file_suffix):
            error_files_list["image"].append(file)
        if not file_tag.endswith(tag_suffix):
            error_files_list["tag"].append(file_tag)
        # 处理xml标签中存在小数点, 更正小数点为正数, 以及判断是否存在多余的标签, 并且删除掉
        files_tag_dir = os.path.join(files_dir, file_tag)
        if file_tag.endswith("xml"):
            get_xml_res(files_tag_dir, tag_kinds)
        # 判断xml类型是不是ascii
        with open(files_tag_dir, 'rb') as f:
            data = f.read()
            if chardet.detect(data).get("encoding") != 'ascii':
                error_files_list["tag_file_not_ascii"].append(file_tag)
        # 判断命名是否存在中文
        pattern = re.compile(u"[\u4e00-\u9fa5]+")
        result = re.findall(pattern, file)
        if result:
            error_files_list["file_contains_chinese"].append(file)
    self.update_state(state='PROGRESS', meta={'current': 4, 'total': 10, 'status': 40})
    # 通过算法运行判断图片是否能正常运行
    files = total_files["files_dir"]
    url = request_host_without_port + ":" + str(port) + "/api/analysisImage"
    time.sleep(5)
    print(url)
    for file in files:
        filename = file.split("/")[-1]
        data = {
            'image': (filename, open(file, 'rb'))
        }
        try:
            requests.post(url, files=data)
        except Exception as e:
            error_files_list["file_cant_open"].append(filename)
    self.update_state(state='PROGRESS', meta={'current': 9, 'total': 10, 'status': 90})
    # 打包下载结果
    with open(os.path.join(files_dir, "res.txt"), 'a') as f:
        f.write(str(error_files_list))
    os.system(f"cd {files_dir};tar -cvf result.tar *")
    result_files = f"{files_dir}/result.tar"
    return {'current': 100, 'total': 100, 'status': 'Task completed!', 'result': result_files, "port":port, "files_dir":files_dir}


def get_xml_res(xml, tag_kinds):
    """
    获取xml中的类型和坐标  检查是否存在多余标签 检查是否存在数字坐标
    :paramer  传入xml绝对路径 以列表返回每个xml文件内容
    """
    file = xml.split("/")[-1]
    doc = parse(xml)
    root = doc.getroot()
    res_kinds = doc.iterfind('object/name')
    res_coordinates = doc.iterfind('object/bndbox')
    for res_kind in res_kinds:
        if res_kind.text not in tag_kinds:
            error_files_list["tag_not_in_tag_kinds"].append(xml)
            tfs = root.findall(f"./object[name='{res_kind.text}']")
            for tf in tfs:
                root.remove(tf)
                doc.write(xml, xml_declaration=True)
    for res_coordinate in res_coordinates:
        ymin = res_coordinate.find('ymin').text
        xmin = res_coordinate.find('xmin').text
        ymax = res_coordinate.find('ymax').text
        xmax = res_coordinate.find('xmax').text
        if '.' in ymin or '.' in xmin or '.' in ymax or '.' in xmax:
            if xml not in error_files_list["wrong_xml_with_float"]:
                error_files_list["wrong_xml_with_float"].append(file)

                res_coordinates_ymin = root.findall('object/bndbox/ymin')
                res_coordinates_ymax = root.findall('object/bndbox/ymax')
                res_coordinates_xmin = root.findall('object/bndbox/xmin')
                res_coordinates_xmax = root.findall('object/bndbox/xmax')

                for res_coordinate in res_coordinates_ymin:
                    ymin = int(float(res_coordinate.text))
                    res_coordinate.text = str(ymin)
                    doc.write(xml, xml_declaration=True)
                for res_coordinate in res_coordinates_ymax:
                    ymax = int(float(res_coordinate.text))
                    res_coordinate.text = str(ymax)
                    doc.write(xml, xml_declaration=True)

                for res_coordinate in res_coordinates_xmin:
                    xmin = int(float(res_coordinate.text))
                    res_coordinate.text = str(xmin)
                    doc.write(xml, xml_declaration=True)

                for res_coordinate in res_coordinates_xmax:
                    xmax = int(float(res_coordinate.text))
                    res_coordinate.text = str(xmax)
                    doc.write(xml, xml_declaration=True)


def iter_files(rootDir):
    """
    根据文件路径 返回文件名称 以及文件路径名称
    :param rootDir:
    :return:
    """
    total_files_count = defaultdict(list)
    for root, dirs, files in os.walk(rootDir):
        for file in files:
            files_dir = os.path.join(root, file)
            if file.endswith("txt") or file.endswith("xml") or file.endswith("json"):
                total_files_count["files_tag"].append(file)
                total_files_count["files_tag_dir"].append(files_dir)
            else:
                total_files_count["files"].append(file)
                total_files_count["files_dir"].append(files_dir)
        for dir in dirs:
            iter_files(dir)
    # 避免出现问题, 对结果排序
    total_files_count["files_tag"] = sorted(total_files_count["files_tag"],
                                            key=lambda files_tag: files_tag.split(".")[0])
    total_files_count["files_tag_dir"] = sorted(total_files_count["files_tag_dir"],
                                            key=lambda files_tag_dir: files_tag_dir.split(".")[0])
    total_files_count["files"] = sorted(total_files_count["files"], key=lambda files: files.split(".")[0])
    total_files_count["files_dir"] = sorted(total_files_count["files_dir"],
                                            key=lambda files_dir: files_dir.split(".")[0])
    return total_files_count
