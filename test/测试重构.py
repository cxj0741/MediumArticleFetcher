import asyncio
import re
import httpx
from playwright.async_api import Page, async_playwright
from bs4 import BeautifulSoup
import const_config
from logger_config import logger
# from mongodb_config import insert_articles_batch
import global_exception_handler

article_data_list = []


async def main():
    urls = None
    async with async_playwright() as playwright:
        urls = await run(playwright)
    username = 'cxjhzw_2MZmd'
    password = 'Lsm666666666+'
    proxy = 'http://dc.oxylabs.io:8000'
    content_tasks = [scrape_article_content_and_images(url, username, password, proxy) for url in urls]
    await asyncio.gather(*content_tasks)


async def create_soup(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    return soup


async def scroll_to_bottom(page: Page):
    await page.wait_for_selector('#root > div > div> div> div > div > button > div > div > div')
    await page.wait_for_timeout(2000)
    i = 1
    html_str = ''
    while True:
        await page.mouse.wheel(0, const_config.SCROLL_DISTANCE)
        await page.wait_for_timeout(2000)
        elements = await page.query_selector_all(const_config.SELECTOR)
        logger.info(f"正在进行第{i}次滑动，共找到 {len(elements)} 条数据")
        i += 1
        if len(elements) >= const_config.MAX_ELEMENTS:
            break
        if i > 500:
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
            href = const_config.BASE_URL + href
            logger.info(f'获取到的链接为 {href}')
            list_urls.append(href)
    return list_urls


def remove_prefix(url, prefix="https://freedium.cfd/"):
    return url[len(prefix):] if url.startswith(prefix) else url


async def fetch_response(url, username, password, proxy):
    proxies = {
        'http://': proxy,
        'https://': proxy,
    }

    async with httpx.AsyncClient(timeout=180, follow_redirects=False, proxies=proxies) as client:
        try:
            response = await client.get(url, auth=(username, password))
            if response.status_code == 301:
                redirect_url = response.headers.get('Location')
                if redirect_url:
                    logger.info(f"Redirecting to: {redirect_url}")
                    response = await client.get(redirect_url, auth=(username, password))
                else:
                    raise ValueError("重定向但没有提供新的 URL")
            return response
        except httpx.RequestError as e:
            raise RuntimeError(f"请求失败: {e}")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"HTTP状态错误: {e}")


def process_response(response):
    try:
        response.raise_for_status()  # 处理HTTP错误
        content = response.text
        soup = BeautifulSoup(content, 'html.parser')

        # Extract author info
        author_locator = soup.select_one('[data-testid="authorName"]')
        if author_locator:
            logger.info(f'作者信息: {author_locator.get_text(strip=True)}')
        else:
            raise ValueError("未找到作者信息")

        # Extract clapCount
        script_tag = soup.find('script', string=lambda t: 'clapCount' in t)
        if script_tag:
            script_content = script_tag.string.strip()
            match = re.search(r'"clapCount":(\d+)', script_content)
            if match:
                clap_count = match.group(1)
                logger.info(f'clapCount: {clap_count}')
            else:
                raise ValueError('未找到 clapCount 数据')
        else:
            raise ValueError("未找到包含 clapCount 的脚本标签")

        # Extract postResponses count
        script_tag = soup.find('script', string=lambda t: 'postResponses' in t)
        if script_tag:
            script_content = script_tag.string.strip()
            match = re.search(r'"postResponses":\{"__typename":"PostResponses","count":(\d+)\}', script_content)
            if match:
                count = match.group(1)
                logger.info(f'postResponses count: {count}')
            else:
                raise ValueError('未找到 postResponses count')
        else:
            raise ValueError("未找到包含 'postResponses' 的脚本标签")

    except httpx.RequestError as e:
        raise RuntimeError(f"请求失败: {e}")
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"HTTP状态错误: {e}")
    except ValueError as e:
        logger.error(f"处理错误: {e}")


async def scrape_article_content_and_images(url, username, password, proxy):
    response = await fetch_response(url, username, password, proxy)
    process_response(response)


async def run(playwright, keyword=None, refresh=False):
    try:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(
            storage_state='state.json',
            viewport={'width': 1280, 'height': 720}
        )
        page = await context.new_page()
        await page.goto("https://medium.com/")

        await page.wait_for_load_state("load")
        await page.wait_for_timeout(2000)
        if keyword is not None:
            await page.fill('[data-testid="headerSearchInput"]', keyword)
            await page.keyboard.press('Enter')
            await page.wait_for_load_state("load")
            logger.info(f'已输入关键字搜索 {keyword}')
        else:
            await page.reload()
            await page.wait_for_load_state("load")
            logger.info("页面已刷新")

        html_str = await scroll_to_bottom(page)
        soup = await create_soup(html_str)
        urls = get_urls(soup)

    finally:
        await context.close()
        logger.info("浏览器关闭")
        return urls


if __name__ == "__main__":
    global_exception_handler.GlobalExceptionHandler.setup()
    asyncio.run(main())
