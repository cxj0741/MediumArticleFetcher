import requests

# ScraperAPI 密钥
api_key = '14476adbcfdb04ef25e06ba090ae70b5'

# 设置代理
proxies = {
    "http": f"http://{api_key}:@proxy-server.scraperapi.com:8001",
    "https": f"http://{api_key}:@proxy-server.scraperapi.com:8001"
}

try:
    response = requests.get('https://medium.com/', proxies=proxies, verify=False)
    response.raise_for_status()  # 如果响应状态码不是 200，将引发 HTTPError
    print(response.text[:1000])  # 打印前1000个字符
except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
