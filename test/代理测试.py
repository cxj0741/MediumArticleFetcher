import requests
from requests.auth import HTTPProxyAuth

# 配置代理服务器地址和端口
proxy = "http://open.proxymesh.com:31280"

# 配置你的 ProxyMesh 用户名和密码
username = "15735667232"
password = "LSM666666."  # 这里替换成你的密码

# 创建一个认证对象
auth = HTTPProxyAuth(username, password)

# 设置代理和认证信息
proxies = {
    "http": proxy,
    "https": proxy,
}

# 发送带有代理和认证的请求
try:
    response = requests.get("https://www.medium.com", proxies=proxies, auth=auth)
    print(f"Response Status Code: {response.status_code}")
    print(f"Page Content: {response.text[:500]}")  # 打印前500个字符

except Exception as e:
    print(f"An error occurred: {e}")
