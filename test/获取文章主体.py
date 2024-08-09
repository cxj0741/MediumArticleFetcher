from playwright.async_api import async_playwright

url3 = 'https://freedium.cfd/https://medium.com/neurodiversified/accessible-communication-benefits-everyone-b042eb916106'
url1='https://freedium.cfd/https://medium.com/@gagliardidomenico/how-i-built-and-sold-a-micro-saas-in-45-days-d8949f8910ca?source=explore---------5-99--------------------60d1a55d_a6cc_4eaf_b1a4_d0452d3d27e7-------15'
async def run(playwright):
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto(url1)

    # 等待页面和所有 img 元素加载完成
    await page.wait_for_timeout(5000)  # 等待 5 秒或根据需要调整
    await page.wait_for_selector('.main-content img', state='visible')  # 确保 img 元素可见

    content=page.locator(r'body > div.container.w-full.md\:max-w-3xl.mx-auto.pt-20.break-words.text-gray-900.dark\:text-gray-200.bg-white.dark\:bg-gray-800 > div.w-full.px-4.md\:px-6.text-xl.text-gray-800.dark\:text-gray-100.leading-normal > div.main-content.mt-8')
    text=await content.inner_text()
    print(text)

    # 使用 CSS 选择器获取 img 元素
    imgs = page.locator('.main-content img')

    # 获取所有 img 元素的数量
    img_count = await imgs.count()
    print(f'找到 {img_count} 个 img 元素')

    # 遍历每个 img 元素并获取 src 属性
    for i in range(img_count):
        img_element = imgs.nth(i)

        # 使用 evaluate 获取 img 元素的 outerHTML**************************
        outer_html = await img_element.evaluate('element => element.outerHTML')
        print(f'第 {i + 1} 个 img 元素的 outerHTML: {outer_html}')

        # 获取 img 元素的 src 属性
        src = await img_element.get_attribute('src')
        if not src:
            # 如果 src 为空，尝试获取 data-src 属性
            src = await img_element.get_attribute('data-src')

        print(f'第 {i + 1} 个 img 元素的 src 属性: {src}')


    await context.close()
    await browser.close()

async def main():
    async with async_playwright() as playwright:
        await run(playwright)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
