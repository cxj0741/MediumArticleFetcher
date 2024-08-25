import asyncio
from concurrent.futures import ThreadPoolExecutor
from playwright.async_api import Page, async_playwright
import uuid
import pdfkit
from bs4 import BeautifulSoup
import const_config
from logger_config import logger
import global_exception_handler

# 创建 BeautifulSoup 对象
async def create_soup(page_content):
    soup = BeautifulSoup(page_content, 'lxml')
    return soup

# 滚动到页面底部以加载更多内容
async def scroll_to_bottom(page: Page):
    i = 1
    html_str = ''
    while True:
        await page.mouse.wheel(0, const_config.SCROLL_DISTANCE)
        await page.wait_for_timeout(1)
        elements = await page.query_selector_all(const_config.SELECTOR)
        logger.info(f"正在进行第{i + 1}次滑动，共找到 {len(elements)} 条数据")
        i += 1
        if len(elements) >= const_config.MAX_ELEMENTS:
            break
    for index, element in enumerate(elements[:const_config.MAX_ELEMENTS], start=1):
        parent_html = await element.evaluate('(element) => element.parentElement.outerHTML')
        html_str += parent_html
        logger.info(f"第 {index} 条数据的父级元素 HTML: {parent_html}")

    return html_str

# 获取页面中的所有链接
def get_urls(soup):
    list_urls = []
    find_all = soup.find_all('a')
    for a in find_all:
        href = a.get('href')
        if href is not None:
            logger.info(f'获取到的链接为{href}')
            new_href = const_config.FREE_URL_PREFIX + const_config.BASE_URL + href
            logger.info(f'拼接后的链接为{new_href}')
            list_urls.append(new_href)
    return list_urls

# 同步生成 PDF 文件
def sync_pdfkit_from_url(url, output_path, config):
    try:
        pdfkit.from_url(url, output_path, configuration=config)
    except Exception as e:
        logger.error(f'生成 URL {url} 的 PDF 时出错: {e}')
        raise

# 异步生成 PDF 文件
async def by_url_get_content(url: str, semaphore):
    async with semaphore:
        path_to_wkhtmltopdf = r'D:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        id = uuid.uuid4()
        output_path = f'D:\\articles\\article_{id}.pdf'
        config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)

        loop = asyncio.get_event_loop()
        retry_attempts = 3
        for attempt in range(retry_attempts):
            try:
                with ThreadPoolExecutor() as pool:
                    await loop.run_in_executor(pool, sync_pdfkit_from_url, url, output_path, config)
                logger.info(f'PDF文件已保存到: {output_path}')
                break
            except Exception as e:
                logger.error(f'第 {attempt + 1} 次尝试生成 URL {url} 的 PDF 失败: {e}')
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(2)  # 重试前等待

# 异步抓取文章内容和图片
async def scrape_article_content_and_images(url):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url)

        # 等待页面和所有 img 元素加载完成
        await page.wait_for_timeout(5000)  # 等待 5 秒或根据需要调整
        await page.wait_for_selector('.main-content img', state='visible')  # 确保 img 元素可见

        content = page.locator(r'body > div.container.w-full.md\:max-w-3xl.mx-auto.pt-20.break-words.text-gray-900.dark\:text-gray-200.bg-white.dark\:bg-gray-800 > div.w-full.px-4.md\:px-6.text-xl.text-gray-800.dark\:text-gray-100.leading-normal > div.main-content.mt-8')
        text = await content.inner_text()
        logger.info(f'文章内容: {text}')

        # 使用 CSS 选择器获取 img 元素
        imgs = page.locator('.main-content img')

        # 获取所有 img 元素的数量
        img_count = await imgs.count()
        logger.info(f'找到 {img_count} 个 img 元素')

        # 遍历每个 img 元素并获取 src 属性
        for i in range(img_count):
            img_element = imgs.nth(i)

            # 使用 evaluate 获取 img 元素的 outerHTML
            outer_html = await img_element.evaluate('element => element.outerHTML')
            logger.info(f'第 {i + 1} 个 img 元素的 outerHTML: {outer_html}')

            # 获取 img 元素的 src 属性
            src = await img_element.get_attribute('src')
            if not src:
                # 如果 src 为空，尝试获取 data-src 属性
                src = await img_element.get_attribute('data-src')

            logger.info(f'第 {i + 1} 个 img 元素的 src 属性: {src}')

        await context.close()
        await browser.close()

# 主运行函数
async def run(playwright, keyword=None, refresh=False):
    context = await playwright.chromium.launch_persistent_context(
        user_data_dir=r'C:\Users\86157\AppData\Local\Google\Chrome\User Data',
        headless=False,
        viewport={"width": 1280, "height": 720}
    )
    page = await context.new_page()  # 确保使用 await 获取 Page 对象
    await page.goto("https://medium.com/")
    await page.wait_for_load_state("load")
    if keyword is not None:
        await page.fill('[data-testid="headerSearchInput"]', keyword)
        await page.keyboard.press('Enter')
        await page.wait_for_load_state("load")
        logger.info(f'已输入关键字搜索 {keyword}')
    else:
        # 刷新页面
        await page.reload()
        await page.wait_for_load_state("load")
        logger.info("页面已刷新")
    html_str = await scroll_to_bottom(page)
    # 获取到 html 后关闭页面
    await context.close()
    soup = await create_soup(html_str)
    urls = get_urls(soup)

    # 生成 PDF
    semaphore = asyncio.Semaphore(5)  # 限制并发请求数为 5
    pdf_tasks = [by_url_get_content(url, semaphore) for url in urls]
    await asyncio.gather(*pdf_tasks)

    # 抓取文章内容和图片
    content_tasks = [scrape_article_content_and_images(url) for url in urls]
    await asyncio.gather(*content_tasks)

if __name__ == "__main__":
    global_exception_handler.GlobalExceptionHandler.setup()

    async def main():
        async with async_playwright() as playwright:
            await run(playwright)

    asyncio.run(main())
