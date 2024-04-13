# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request
from http import HTTPStatus
import dashscope
from flask_cors import CORS
from prompt import image_prompt  # 导入变量和函数
import base64
import oss2
import os
from oss2.credentials import EnvironmentVariableCredentialsProvider
from datetime import datetime, timedelta
import re
import json

ALIYUN_ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID")
ALIYUN_ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET")
ALIYUN_OSS_ENDPOINT = os.getenv("ALIYUN_OSS_ENDPOINT")
ALIYUN_BUCKET_NAME = os.getenv("ALIYUN_BUCKET_NAME")
if not all([ALIYUN_ACCESS_KEY_ID, ALIYUN_ACCESS_KEY_SECRET, ALIYUN_OSS_ENDPOINT, ALIYUN_BUCKET_NAME]):
    # 如果其中任何一个环境变量是 None，就抛出错误
    raise EnvironmentError("环境变量中 Aliyun OSS 未被找到")

# 从环境变量中获取访问凭证。运行本代码示例之前，请确保已设置环境变量OSS_ACCESS_KEY_ID和OSS_ACCESS_KEY_SECRET。
auth = oss2.ProviderAuth(EnvironmentVariableCredentialsProvider())
bucket = oss2.Bucket(auth, 'https://oss-cn-hangzhou.aliyuncs.com', ALIYUN_BUCKET_NAME)

app = Flask(__name__)
CORS(app)

@app.route('/analyze_image', methods=['GET'])
def analyze_image():
   # 从查询字符串中获取'image'参数
    image = request.args.get('image')
    print('image參數：', image)
    if image:
           # 构造messages结构
        messages = [
            {
                "role": "user",
                "content": [
                    {"image": image},
                    {"text": f"{image_prompt}"}
                ]
            }
        ]

        # 调用MultiModalConversation.call
        imageInfoResponse = dashscope.MultiModalConversation.call(model='qwen-vl-plus', messages=messages)
        print('imageInfoResponse', imageInfoResponse)
   
        if imageInfoResponse.status_code == HTTPStatus.OK:
            print(f"图片识别结果: {imageInfoResponse}")
        else:
            print(imageInfoResponse.code)  # The error code.
            print(imageInfoResponse.message)  # The error message.
                 # 检查output.choices是否存在且不为空
        if not hasattr(imageInfoResponse.output, 'choices') or not imageInfoResponse.output.choices:
            return jsonify({"error": "Missing choices in the response output"}), HTTPStatus.INTERNAL_SERVER_ERROR

        json_string = str(imageInfoResponse.output.choices[0].message.content[0])

        json_pattern = r'```json(.*)```'
        json_content = re.search(json_pattern, json_string).group(1)
        return jsonify({"code": imageInfoResponse.code, "data": json_content}), imageInfoResponse.status_code

    else:
        # 如果没有提供'image'参数，返回错误响应
        return jsonify({'status': 'error', 'message': 'Missing image parameter'}), 400

 
@app.route('/upload_base64_image', methods=['POST'])
def upload_base64_image():
    image_data = request.form.get('image')

    base64_image = image_data.split(",")[1].encode()  # 获取Base64编码并转换为bytes类型
    image_bytes = base64.b64decode(base64_image)  # 解码Base64编码为原始图片字节数据
    # 获取当前时间，并格式化为例如 "YYYY-MM-DD-HH-MM-SS" 格式
    timestamp_str = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
    # 构建新的文件名
    object_name = f"pet/{timestamp_str}.jpg"
    bucket.put_object(object_name, image_bytes)  # 上传二进制数据
    # 初始化所需参数
    presigned_url = bucket.sign_url('GET', object_name, 3600)
    return jsonify({"code": 200, "data": presigned_url}), 200
    # response = analyze_image(presigned_url)
    # return response
if __name__ == '__main__':
    app.run(debug=True)
