import asyncio
from concurrent.futures import ThreadPoolExecutor
from playwright.async_api import Page, async_playwright
import uuid
import gridfs
import pdfkit
from bs4 import BeautifulSoup
import const_config
from logger_config import logger
from mongodb_config import db
import global_exception_handler


async def create_soup(page_content):
    soup = BeautifulSoup(page_content, 'lxml')
    return soup


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


def get_urls(soup):
    list_urls = []
    find_all = soup.find_all('a')
    for a in find_all:
        href = a.get('href')
        if href is not None:
            logger.info(f'获取到的链接为{href}')
            new_href = const_config.FREE_URL_PREFIX + const_config.BASE_URL + href
            logger.info(f'拼接后到的链接为{new_href}')
            list_urls.append(new_href)
    return list_urls


def sync_pdfkit_from_url(url, output_path, config):
    try:
        pdfkit.from_url(url, output_path, configuration=config)
    except Exception as e:
        logger.error(f'Error generating PDF for URL {url}: {e}')
        raise


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
                fs = gridfs.GridFS(db)
                with open(output_path, 'rb') as f:
                    fs.put(f, filename=str(id))
                logger.info(f'PDF文件已保存到数据库: {output_path}')
                break
            except Exception as e:
                logger.error(f'Attempt {attempt + 1} failed for URL {url}: {e}')
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(2)  # Wait before retrying


async def run(playwright, keyword=None, refresh=False):
    context = await playwright.chromium.launch_persistent_context(
        user_data_dir=r'C:\Users\86157\AppData\Local\Google\Chrome\User Data',
        headless=False,
        viewport={"width": 1280, "height": 720}
    )
    page = await context.new_page()  # Ensure you use await to get the Page object
    await page.goto("https://medium.com/")
    await page.wait_for_load_state("load")
    if keyword is not None:
        await page.fill('[data-testid="headerSearchInput"]', keyword)
        await page.keyboard.press('Enter')
        await page.wait_for_load_state("load")
        logger.info(f'已输入关键字搜索{keyword}')
    else:
        # 刷新页面
        await page.reload()
        await page.wait_for_load_state("load")
        logger.info("页面已刷新")
    html_str = await scroll_to_bottom(page)
    # 获取到html后关闭页面
    await context.close()
    # playwright.stop()
    soup = await create_soup(html_str)
    urls = get_urls(soup)

    semaphore = asyncio.Semaphore(5)  # 限制并发请求数为5
    tasks = [by_url_get_content(url, semaphore) for url in urls]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    global_exception_handler.GlobalExceptionHandler.setup()


    async def main():
        async with async_playwright() as playwright:
            await run(playwright)


    asyncio.run(main())
