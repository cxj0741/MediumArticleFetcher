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
async def main():
    async with async_playwright() as playwright:
        urls=await run(playwright)
        batch_size=10
        for i in range(0, len(urls), batch_size):
            batch_urls = urls[i:i + batch_size]
            article_data_list.clear()
            content_tasks = [scrape_article_content_and_images(url) for url in batch_urls]

            try:
                await asyncio.gather(*content_tasks)
                # print(f"一共插入了{len(article_data_list)}条数据")
                insert_articles_batch(article_data_list)
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                # print(f"在 gather 中发生错误: {e}")
                logger.info(f"在 gather 中发生错误: {e}")

async def create_soup(page_content):
    soup = BeautifulSoup(page_content, 'lxml')
    return soup

# todo 滑动的时候会出现卡住的情况，只往下面滑，不更新网站数量
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
        if i>500:
            break
    for index, element in enumerate(elements[:const_config.MAX_ELEMENTS], start=1):
        parent_html = await element.evaluate('(element) => element.parentElement.outerHTML')
        html_str += parent_html
        logger.info(f"第 {index} 条数据的父级元素 HTML: {parent_html}")

    return html_str

# 获取原始的链接,这里需要加medium.com前缀
def get_urls(soup):
    list_urls = []
    find_all = soup.find_all('a')
    for a in find_all:
        href = a.get('href')
        if href is not None:
            href=const_config.BASE_URL+href
            logger.info(f'获取到的链接为{href}')

            list_urls.append(href)
    return list_urls


async def scrape_article_content_and_images(url: str):
    try:
        article_data = {'url': url}
        # url = 'https://httpbin.org/ip'
        # username = 'cxjhzw_2MZmd'
        # password = 'Lsm666666666+'
        # proxy = 'dc.oxylabs.io:8000'  # 8000端口用于轮换代理
        proxies = {
            'https://': "https://customer-cxjhzw_DBcRk-cc-us:Lsm666666666+@pr.oxylabs.io:7777"
        }

        try:
            #  todo 没有使用代理
            async with httpx.AsyncClient(timeout=120, follow_redirects=True,proxies=proxies) as client:
                try:
                    attempt = 0
                    max_retries=5
                    while attempt < max_retries:
                        try:
                            response = await client.get(url)
                            response.raise_for_status()  # 处理HTTP错误
                            content = response.text
                            print("请求成功")
                            break
                            # print(content[:500])  # 打印响应的前500个字符
                            # return  # 成功则退出函数
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
                    likes=None
                    comments=None
                    if author_locator:
                        author= author_locator.get_text(strip=True)
                        article_data['author']=author
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
                            # print(f'{clap_count}')
                            logger.info(f"点赞数为：{clap_count}")
                            article_data['likes']=clap_count
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
                            article_data['comments']=count

                        else:
                            raise ValueError('未找到 postResponses count')
                    else:
                        raise ValueError("未找到包含 'postResponses' 的脚本标签")

                except httpx.RequestError as e:
                    raise RuntimeError(f"请求失败: {e}")
                except httpx.HTTPStatusError as e:
                    raise RuntimeError(f"HTTP状态错误: {e}")
                # finally:pass


        except httpx.ConnectError as e:
            logger.error(f"连接错误: {e}")

        new_href = const_config.FREE_URL_PREFIX + url.lstrip('/')
        logger.info(f'拼接后到的链接为{new_href}')
        try:
            async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
                try:
                    response = await client.get(url)
                    response.raise_for_status()  # 处理HTTP错误

                    content = response.text
                except:
                    pass
                soup = BeautifulSoup(content, 'html.parser')

                article = soup.find('article')
                if article:
                    content=article.get_text(separator='\n', strip=True)
                    article_data['content'] = content
                    images = article.find_all('img')
                    img_links = [img.get('src') for img in images]
                    article_data['images'] = img_links

                else:
                    article_data['images'] = None
                    article_data['content'] = None
                    logger.info("没有找到文章")
            article_data_list.append(article_data)
        except httpx.ConnectError as e:
            logger.error(f"连接错误: {e}")
            article_data['error'] = f"连接错误: {e}"
    except httpx.ConnectError as e:
        logger.error(f"连接错误: {e}")
    # article_data_list.append(article_data)

async def run(playwright, keyword=None, refresh=False):
    try:
        # 启动一个浏览器实例
        browser = await playwright.chromium.launch(headless=False)

        # 创建一个新的浏览器上下文，并使用 'state.json' 文件加载存储状态，设置窗口大小
        context = await browser.new_context(
            storage_state='state.json',
            viewport={'width': 1280, 'height': 720}  # 设置浏览器窗口大小
        )

        page = await context.new_page()
        await page.goto("https://medium.com/")


        await page.wait_for_load_state("load")
        await page.wait_for_timeout(2000)
        if keyword is not None:
            await page.fill('[data-testid="headerSearchInput"]', keyword)
            await page.keyboard.press('Enter')
            await page.wait_for_load_state("load")
            logger.info(f'已输入关键字搜索{keyword}')
            # await page.wait_for_timeout(3000)
        else:
            await page.reload()
            await page.wait_for_load_state("load")
            logger.info("页面已刷新")
        html_str = await scroll_to_bottom(page)

        soup = await create_soup(html_str)
        urls = get_urls(soup)

    finally:
        # 在所有任务完成后再关闭 context
        await context.close()
        # insert_articles_batch(article_data_list)
        logger.info("浏览器关闭")
        return urls

if __name__ == "__main__":
    global_exception_handler.GlobalExceptionHandler.setup()
    asyncio.run(main())
    # insert_articles_batch(article_data_list)
