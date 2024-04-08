import json

# 给定的字符串
json_content = '\n{\n    "result": [\n        "睡得好香",\n        "舒服得不想动弹",\n        "享受着午后的慵懒"\n    ]\n}\n'

# 使用strip()去除字符串开头和结尾的空白字符
s = json_content.strip()

# 使用json.loads()将字符串转换为Python对象
data = json.loads(s)

# 提取result键对应的值，即包含数组的部分
result_array = data["result"]

print(result_array)