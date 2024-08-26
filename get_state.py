import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

user_data_dir=r"C:\Users\86157\AppData\Local\Google\Chrome\User Data"
async def save_storage_state(playwright):
    # 使用相对路径获取用户数据目录
    # 假设 user_data_dir 文件夹与代码在同一路径下
    # base_dir = Path(__file__).parent  # 获取当前脚本所在目录
    # user_data_dir = base_dir / 'User Data'  # 构建用户数据目录路径\
    # 启动一个浏览器实例
    browser = await playwright.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,  # 修改为实际的用户数据目录
        headless=False
    )

    # 打开一个新的页面并导航到目标网站
    page = await browser.new_page()
    await page.goto("https://medium.com")

    # 保存存储状态到 'state.json'
    await page.context.storage_state(path='state.json')

    # 关闭浏览器
    await browser.close()


async def main():
    async with async_playwright() as playwright:
        await save_storage_state(playwright)


if __name__ == "__main__":
    asyncio.run(main())
