from playwright.sync_api import sync_playwright

# 你的代理服务器信息
proxy_username = 'customer-cxjhzw_Slva4-cc-am'
proxy_password = 'Lsm666666666+'
proxy_server = 'cnt9t1is.com'
proxy_port = 8000

# 设置代理
proxy = {
    "server": f"https://{proxy_server}:{proxy_port}",
    "username": proxy_username,
    "password": proxy_password
}

# 目标URL
target_url = 'https://medium.com/'  # 替换为你要抓取的网站
# target_url = 'https://readmedium.com/zh/my-stake-your-stake-whats-the-price-of-a-stake-a2a45dc1b368'  # 替换为你要抓取的网站
# target_url = 'https://github.com/microsoft/playwright-python/issues'  # 替换为你要抓取的网站
# target_url = 'https://medium.com/python-in-plain-english/simulate-the-first-photo-of-an-exoplanet-308769b755ba'  # 免费网站

# 使用 Playwright 访问网站
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, proxy=proxy)
    context = browser.new_context(
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
