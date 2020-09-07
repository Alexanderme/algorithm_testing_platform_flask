from flask import Blueprint

api = Blueprint("api_1_0", __name__)

from . import  sdk_vas_ias_svas, sdk_miss_rate, algo_data_set, sdk_standard, sdk_performance, sdk_run_res_file
