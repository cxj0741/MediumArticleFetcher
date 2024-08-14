import requests


def test_proxy(proxy_url):
    proxies = {
        'http': proxy_url,
        'https': proxy_url,
    }

    try:
        # 发起请求
        # response = requests.get('https://www.msn.cn/zh-cn/news/other/%E7%9C%9F%E7%9B%B8%E8%97%8F%E4%B8%8D%E4%BD%8F-%E9%82%B1%E8%B4%BB%E5%8F%AF%E5%8F%91%E5%A3%B0-%E8%A7%A3%E9%87%8A%E8%8E%8E%E8%8E%8E%E8%BE%93%E9%99%88%E6%A2%A6%E5%8E%9F%E5%9B%A0-4%E4%B8%AA%E7%BB%86%E8%8A%82%E9%81%93%E5%87%BA%E9%9A%90%E6%83%85/ar-AA1oMxoc?ocid=msedgntp&pc=HCTS&cvid=66bc8bfe2d4545d68473d158c741e67e&ei=6', proxies=proxies, timeout=100)
        # response = requests.get('https://chatgpt.com/c/d3720d71-3300-4f43-aef7-2805e1af2e63', proxies=proxies, timeout=100)
        response = requests.get('https://medium.com', proxies=proxies, timeout=100)

        # 打印响应状态和前500个字符
        response.raise_for_status()  # 确保响应状态码是200
        print("请求成功")
        print("响应的前500个字符：")
        print(response.text[:500])

    except requests.RequestException as e:
        print(f"请求失败: {e}")


# 你的端点
proxy_url = 'https://customer-cxjhzw_DBcRk:Lsm666666666+@pr.oxylabs.io:10000'

# 测试代理
test_proxy(proxy_url)
