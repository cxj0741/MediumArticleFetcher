from playwright.sync_api import sync_playwright
import random

# 你的代理列表
proxies_list = [
    {"ip": "104.237.242.135", "port": 8001},
    {"ip": "104.237.242.136", "port": 8002},
    {"ip": "104.237.242.137", "port": 8003},
    {"ip": "104.237.242.138", "port": 8004},
    {"ip": "104.237.242.139", "port": 8005},
    {"ip": "104.237.242.14", "port": 8006},
    {"ip": "104.237.242.140", "port": 8007},
    {"ip": "104.237.242.141", "port": 8008},
    {"ip": "104.237.242.142", "port": 8009},
    {"ip": "104.237.242.143", "port": 8010},
]

# 你的 Oxylabs 用户名和密码
username = 'cxjhzw_2MZmd'
password = 'Lsm666666666+'

# 随机选择一个代理
selected_proxy = random.choice(proxies_list)

# 设置代理URL
proxy = {
    "server": f"http://dc.oxylabs.io:{selected_proxy['port']}",
    "username": f"user-{username}",
    "password": password
}

# 目标URL
# target_url = 'https://freedium.cfd/https://medium.com/life-without-children/im-the-witch-d97c44df32fd?source=explore---------0-110--------------------25798464_a388_49c2_987e_e146c0257985-------15'  # 替换为你要抓取的网站
target_url = 'https://medium.com/'  # 替换为你要抓取的网站
# target_url = 'https://readmedium.com/zh/my-stake-your-stake-whats-the-price-of-a-stake-a2a45dc1b368'  # 免费网站
# target_url = 'https://www.cnblogs.com/'  # 免费网站

# 使用 Playwright 访问网站
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, proxy=proxy)
    context = browser.new_context(
        storage_state='state.json',
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
    )
    page = context.new_page()

    try:
        # 设置较长的超时时间以防止超时
        page.goto(target_url, timeout=60000)
        print(f"Page title: {page.title()}")
        # 你可以根据需要在这里执行更多操作
        page.wait_for_timeout(20000)
    except Exception as e:
        print(f"Request failed: {e}")
    finally:
        browser.close()
