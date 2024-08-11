import os
from playwright.sync_api import sync_playwright


def run(keyword=None, refresh=False):
    user_data_dir = os.path.abspath('../User Data')

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 720}
        )
        page = browser.new_page()
        page.goto("https://medium.com/")

        # 输出整个页面的文本内容
        content = page.content()
        print(content)  # 打印页面内容到控制台

        # 关闭浏览器
        browser.close()


if __name__ == "__main__":
    run()
