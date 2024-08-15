import asyncio
import re
import random
import httpx
from playwright.async_api import Page, async_playwright
from bs4 import BeautifulSoup
import const_config
from logger_config import logger
import global_exception_handler
from mongodb_config import insert_articles_batch

article_data_list = []

# 将 Playwright 实例创建在全局
async def fetch_main(keyword: str = None, refresh: bool = False):
    async with async_playwright() as playwright:
        urls = await run(playwright)
        batch_size = 10
        for i in range(0, len(urls), batch_size):
            batch_urls = urls[i:i + batch_size]
            article_data_list.clear()
            content_tasks = [scrape_article_content_and_images(url) for url in batch_urls]

            try:
                results = await asyncio.gather(*content_tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"任务执行中发生错误: {result}")
                insert_articles_batch(article_data_list)
            except Exception as e:
                logger.error(f"在 gather 中发生未捕获的错误: {e}")

async def create_soup(page_content):
    soup = BeautifulSoup(page_content, 'lxml')
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
        logger.info(f"正在进行第{i + 1}次滑动，共找到 {len(elements)} 条数据")
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
            logger.info(f'获取到的链接为{href}')
            list_urls.append(href)
    return list_urls

async def scrape_article_content_and_images(url: str):
    try:
        article_data = {'url': url}
        proxies = {
            'https://': "https://customer-cxjhzw_DBcRk-cc-us:Lsm666666666+@pr.oxylabs.io:7777"
        }

        try:
            async with httpx.AsyncClient(timeout=120, follow_redirects=True, proxies=proxies) as client:
                attempt = 0
                max_retries = 5
                while attempt < max_retries:
                    try:
                        response = await client.get(url)
                        response.raise_for_status()  # 处理HTTP错误
                        content = response.text
                        logger.info("请求成功")
                        break
                    except httpx.RequestError as e:
                        attempt += 1
                        logger.info(f"请求失败: {e}. 尝试 {attempt}/{max_retries}...")
                        if attempt >= max_retries:
                            logger.error("达到最大重试次数，放弃请求。")
                            raise
                        delay = random.uniform(1, 3)
                        await asyncio.sleep(delay)  # 延迟重试
                soup = BeautifulSoup(content, 'html.parser')

                # Extract author info
                author_locator = soup.select_one('[data-testid="authorName"]')
                author = None
                if author_locator:
                    author = author_locator.get_text(strip=True)
                    article_data['author'] = author
                    logger.info(f"作者信息为：{author}")
                else:
                    raise ValueError("未找到作者信息")

                # Extract clapCount
                script_tag = soup.find('script', string=lambda t: 'clapCount' in t)
                if script_tag:
                    script_content = script_tag.string.strip()
                    match = re.search(r'"clapCount":(\d+)', script_content)
                    if match:
                        clap_count = match.group(1)
                        logger.info(f"点赞数为：{clap_count}")
                        article_data['likes'] = clap_count
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
                        logger.info(f"评论数为：{count}")
                        article_data['comments'] = count
                    else:
                        raise ValueError('未找到 postResponses count')
                else:
                    raise ValueError("未找到包含 'postResponses' 的脚本标签")

        except httpx.ConnectError as e:
            logger.error(f"连接错误: {e}")
        # 找到最后一个 '/' 的位置
        last_slash_index = url.rfind('/')

        # 从最后一个 '/' 开始获取后续的子字符串
        result = url[last_slash_index:]
        new_href = const_config.FREE_URL_PREFIX + result
        # print(f"截取以后的url为{url.lstrip('/')}")
        logger.info(f'拼接后的链接为{new_href}')

        try:
            async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
                try:
                    response = await client.get(new_href)
                    response.raise_for_status()  # 处理HTTP错误
                    content = response.text
                except httpx.RequestError as e:
                    logger.error(f"请求错误: {e}")
                    return
                soup = BeautifulSoup(content, 'html.parser')

                article = soup.find('article')
                if article:
                    content = article.get_text(separator='\n', strip=True)
                    article_data['content'] = content

                    # 获取文章中的图片链接
                    images = article.find_all('img')
                    # print(images)
                    img_links = [img.get('src') for img in images]
                    article_data['images'] = img_links
                    # print(article_data['images'])
                else:
                    article_data['images'] = None
                    logger.info("没有找到文章")

            article_data_list.append(article_data)
        except httpx.ConnectError as e:
            logger.error(f"连接错误: {e}")
            article_data['error'] = f"连接错误: {e}"
    except Exception as e:
        logger.error(f"处理URL {url} 时发生错误: {e}")

async def run(playwright, keyword=None, refresh=False):
    try:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(
            storage_state='state.json',
            viewport={'width': 1280, 'height': 720}
        )
        page = await context.new_page()
        await page.goto("https://medium.com/",timeout=60000)
        await page.wait_for_load_state("load")
        await page.wait_for_timeout(2000)

        if keyword is not None:
            await page.fill('[data-testid="headerSearchInput"]', keyword)
            await page.keyboard.press('Enter')
            await page.wait_for_load_state("load")
            logger.info(f'已输入关键字搜索{keyword}')
        else:
            await page.reload()
            await page.wait_for_load_state("load")
            logger.info("页面已刷新")

        html_str = await scroll_to_bottom(page)
        soup = await create_soup(html_str)
        urls = get_urls(soup)
    except Exception as e:
        logger.error(f"浏览器操作时发生错误: {e}")
        urls = []
    finally:
        await context.close()
        logger.info("浏览器关闭")
        return urls

if __name__ == "__main__":
    global_exception_handler.GlobalExceptionHandler.setup()
    asyncio.run(fetch_main())
