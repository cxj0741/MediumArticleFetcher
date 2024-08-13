from playwright.async_api import async_playwright


async def run(playwright):
    proxy_host = 'brd.superproxy.io:22225'
    proxy_username = 'BRD 客户hl_300d3c5c区域datacenter_proxy1'
    proxy_password = 'O43W4OHMUUZG'

    proxy_url = f'http://{proxy_username}:{proxy_password}@{proxy_host}'

    try:
        # 启动浏览器实例，使用代理
        browser = await playwright.chromium.launch(
            headless=False,
            proxy={"server": proxy_url}
        )

        # 创建新的浏览器上下文
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )

        # 创建新页面并访问目标网站
        page = await context.new_page()

        # 设置超时
        try:
            await page.goto('https://medium.com/', timeout=60000)  # 增加超时设置
        except Exception as e:
            print(f"Navigation Error: {e}")

        # 打印页面标题
        print(await page.title())

        # 关闭浏览器
        await browser.close()

    except Exception as e:
        print(f"An error occurred: {e}")


async def main():
    async with async_playwright() as playwright:
        await run(playwright)


import asyncio

asyncio.run(main())
