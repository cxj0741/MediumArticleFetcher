import requests
from bs4 import BeautifulSoup

proxy_username = 'customer-cxjhzw_Slva4-cc-am'
proxy_password = 'Lsm666666666+'
proxy_server = 'cnt9t1is.com'
proxy_port = 8000

# 使用正确的协议配置
proxies = {
    "http": f"http://{proxy_username}:{proxy_password}@{proxy_server}:{proxy_port}",
    "https": f"https://{proxy_username}:{proxy_password}@{proxy_server}:{proxy_port}",
}

try:
    response = requests.get("https://medium.com/@fadingeek/anytype-and-capacities-how-i-organize-and-use-them-to-maximize-productivity-2339e28c21bd", proxies=proxies, timeout=60)
    response.raise_for_status()  # 确保响应状态码为 200，否则抛出异常
    soup = BeautifulSoup(response.content, 'html.parser')
    print("soup")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
