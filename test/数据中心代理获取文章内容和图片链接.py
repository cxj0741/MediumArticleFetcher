import json
import re

import requests
from bs4 import BeautifulSoup

username = 'cxjhzw_2MZmd'
password = 'Lsm666666666+'
proxy = 'dc.oxylabs.io:8000'  # 8000端口用于轮换代理

proxies = {
    "https": f'https://user-{username}:{password}@{proxy}'
}
# 目标URL，访问百度首页
target_url = "https://readmedium.com/zh/2024-best-of-the-midwest-startup-city-rankings-2e1108e3d996"

response = requests.get(target_url,proxies,timeout=180)
response.raise_for_status()  # 检查是否请求成功

soup = BeautifulSoup(response.content, 'html.parser')
print(proxies)
article = soup.find('article')
if article :
    print(article.get_text(separator='\n', strip=True))
    images = article.find_all('img')

    img_links = [img.get('src') for img in images]

    for link in img_links:
        print(link)
else:
    print("为空")


