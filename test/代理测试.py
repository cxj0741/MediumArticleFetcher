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
target_url = "https://medium.com/signifier/blue-mountains-blue-riders-74fc72425423"

response = requests.get(target_url, proxies=proxies)
response.raise_for_status()  # 检查是否请求成功

soup = BeautifulSoup(response.content, 'html.parser')
author_locator = soup.select_one('[data-testid="authorName"]')
print(author_locator.get_text(strip=True))


# 找到包含 clapCount 的 <script> 标签
script_tag = soup.find('script', string=lambda t: 'clapCount' in t)

if script_tag:
    # 提取脚本内容
    script_content = script_tag.string.strip()

    # 尝试解析为 JSON
    try:
        # 提取 <script> 标签中的文本内容
        script_content = script_tag.string

        # 使用正则表达式直接提取 clapCount 的值
        match = re.search(r'"clapCount":(\d+)', script_content)
        if match:
            clap_count = match.group(1)
            # print(f'Clap Count: {clap_count}')
            print(f'{clap_count}')
        else:
            print('未找到 clapCount 数据')
    except json.JSONDecodeError:
        print("无法解析 JSON 数据")

else:
    print("未找到包含 clapCount 的脚本标签")
# 查找包含 'postResponses' 的 <script> 标签
script_tag = soup.find('script', string=lambda t: 'postResponses' in t)

if script_tag:
    # 提取脚本内容
    script_content = script_tag.string.strip()

    # 尝试解析为 JSON
    try:
        # 使用正则表达式直接提取 postResponses 的 count 值
        match = re.search(r'"postResponses":\{"__typename":"PostResponses","count":(\d+)\}', script_content)
        if match:
            count = match.group(1)
            # print(f'Comment Count: {count}')
            print(f'{count}')
        else:
            print('未找到 postResponses count')
    except Exception as e:
        print(f'解析失败: {e}')
else:
    print("未找到包含 'postResponses' 的脚本标签")