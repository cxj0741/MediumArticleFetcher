import asyncio
import os
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
failed_urls = set()

file_path = 'failed_urls.txt'
permanent_failures_path = 'permanent_failures.txt'

# 记录失败的url
def record_failed_url(urls):
    try:
        with open(file_path, 'a') as file:
            for url in urls:
                file.write(f"{url},1\n")
    except Exception as e:
        logger.error(f"记录失败 URL 时发生错误: {e}")

# handle中写入url
def backup_failed_urls(failed_urls):
    # 将内存中的失败 URL 及其失败次数写入文件
    try:
        with open(file_path, 'w') as file:
            for url, count in failed_urls.items():
                file.write(f"{url},{count}\n")
    except Exception as e:
        logger.error(f"备份失败 URL 时发生错误: {e}")

# 处理失败的url
async def handle_failed_urls():
    if not os.path.exists(file_path):
        print("失败 URL 文件不存在")
        return

    temp_failed_urls = {}
    try:
        # 读取文件并更新失败 URL 和失败次数
        with open(file_path, 'r') as file:
            for line in file:
                url, count = line.strip().split(',')
                count = int(count)
                if url in temp_failed_urls:
                    temp_failed_urls[url] = max(temp_failed_urls[url], count)
                else:
                    temp_failed_urls[url] = count

        # 处理失败的 URL
        permanent_failures = []
        tasks = []
        for url, count in list(temp_failed_urls.items()):
            tasks.append(process_failed_url(url, count, temp_failed_urls, permanent_failures))

        await asyncio.gather(*tasks)

        # 备份更新后的失败 URL
        backup_failed_urls(temp_failed_urls)

        # 将永久失败的 URL 追加到永久失败文件中
        if permanent_failures:
            with open(permanent_failures_path, 'a') as file:
                for failure in permanent_failures:
                    file.write(f"{failure}\n")

    except Exception as e:
        print(f"处理失败的 URL 文件时发生错误: {e}")

# 异步调用真正处理失败的url，并放入数据库
async def process_failed_url(url, count, temp_failed_urls, permanent_failures):
    urls=[]
    try:
        # 在这里处理 URL
        print(f"重新处理 URL: {url} (失败次数: {count})")
        await scrape_article_content_and_images(url)  # 异步调用抓取函数
        temp_failed_urls.pop(url, None)  # 将处理成功的 URL 清除
        urls.append(url)
        insert_articles_batch(urls)
    except Exception as e:
        # 处理失败，重新记录失败 URL，并增加失败次数
        if count < 5:
            temp_failed_urls[url] = count + 1
        else:
            # 将失败次数达到最大值的 URL 写入永久失败列表
            permanent_failures.append(f"{url},{count}")
    return urls
# 批量处理urls
async def process_batch(urls):
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
            # print(article_data_list)
        except Exception as e:
            logger.error(f"在 gather 中发生未捕获的错误: {e}")

# 主要代码地方
async def fetch_main(keyword: str = None, refresh: bool = False):
    await handle_failed_urls()
    async with async_playwright() as playwright:
        urls = await run(playwright,keyword, refresh)
    await process_batch(urls)
    # 批量写入失败的 URL
    if failed_urls:
        record_failed_url(failed_urls)
        logger.info(f"将失败的url放入文本文件{file_path}")
        failed_urls.clear()  # 清空失败的 URL 集合

async def create_soup(page_content):
    soup = BeautifulSoup(page_content, 'lxml')
    return soup

async def scroll_to_bottom(page: Page):
    await page.wait_for_selector('#root > div > div> div> div > div > button > div > div > div')
    await page.wait_for_timeout(2000)
    i = 1 #滚动次数
    html_str = ''
    max_scroll_attempts = 40  # 连续最大滚动次数
    scroll_attempts = 0  # 当前连续滚动次数
    last_element_count = 0  # 上一次查询到的元素数量
    min_scroll_attempts = 12  # 连续最大滚动次数最小值，滑动这么多次没有数据变化尝试找寻show more
    while True:
        await page.wait_for_timeout(2000)
        await page.wait_for_load_state("load")
        await page.mouse.wheel(0, const_config.SCROLL_DISTANCE)

        # elements = await page.query_selector_all(const_config.SELECTOR)

        # 检查是否出现“Show More”按钮
        if scroll_attempts > min_scroll_attempts:
            show_more_button = await page.query_selector(
                '#root > div > div.s.c > div.cp.cq.s > div > main > div > div > div:nth-child(2) > div > div:nth-child(10) > div > div > button')
            if show_more_button:
                logger.info("找到 'Show More' 按钮，正在点击...")
                await show_more_button.click()
                await page.wait_for_timeout(2000)  # 等待页面加载更多内容


        # 查询当前页面上的所有目标元素
        elements = await page.query_selector_all(const_config.SELECTOR)
        current_element_count = len(elements)
        logger.info(f"正在进行第{i}次滑动，共找到 {current_element_count} 条数据")
        i += 1

        # 查询完记录变化,数据不变，则连续滑动次数+1
        # 数据改变，则连续滑动次数归零,上次元素数量等于当前元素数量
        if current_element_count==last_element_count:
            scroll_attempts+=1
        else:
            last_element_count = current_element_count
            scroll_attempts=0

        # 如果连续滑动次数大于最大连续滑动次数，则认为到底了，或者卡住了，退出浏览器
        if scroll_attempts>max_scroll_attempts:
            logger.info("检测到连续滑动没有新数据，退出。")
            break

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

# 重试请求的逻辑
async def retry_request(request_func, max_retries=5, retry_delay=(1, 3), *args, **kwargs):
    """重试请求的逻辑。

    Args:
        request_func (coroutine): 发起请求的异步函数。
        max_retries (int): 最大重试次数。
        retry_delay (tuple): 重试之间的延迟范围 (秒)。
        *args, **kwargs: 传递给请求函数的其他参数。

    Returns:
        response: 请求的响应对象。

    Raises:
        Exception: 如果在最大重试次数后仍然失败，抛出异常。
    """
    attempt = 0
    while attempt < max_retries:
        try:
            response = await request_func(*args, **kwargs)
            response.raise_for_status()  # 处理HTTP错误
            logger.info("请求成功")
            return response
        except httpx.RequestError as e:
            attempt += 1
            logger.warning(f"请求失败: {e}. 尝试 {attempt}/{max_retries}...")
            if attempt >= max_retries:
                logger.error("达到最大重试次数，放弃请求。")
                raise
            delay = random.uniform(*retry_delay)
            await asyncio.sleep(delay)  # 延迟重试

# 获取文章详细信息并调用重试逻辑
async def fetch_article_details(url, proxies=None,article_data={}):
    """通过URL获取文章详细信息，包括重试机制。

    Args:
        url (str): 文章的URL。
        proxies (dict): 代理设置，可选。

    Returns:
        dict: 包含文章信息的字典。
    """
    async with httpx.AsyncClient(timeout=120, follow_redirects=True, proxies=proxies) as client:
        # 使用 retry_request 方法进行请求，并传递 client.get 作为请求函数
        response = await retry_request(client.get, url=url)
        content = response.text

        # 解析文章内容
        soup = BeautifulSoup(content, 'html.parser')
        # article_data = {}

        # 提取作者信息
        author_locator = soup.select_one('[data-testid="authorName"]')
        if author_locator:
            author = author_locator.get_text(strip=True)
            article_data['author'] = author
            logger.info(f"作者信息为：{author}")
        else:
            raise ValueError("未找到作者信息")

        # 提取点赞数（clapCount）
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

        # 提取评论数（postResponses count）
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

    return article_data


# 请求文章内容并返回解析后的 BeautifulSoup 对象
async def fetch_article_content(url, timeout=300,client=None):
    """通过URL获取文章内容并返回BeautifulSoup对象。

    Args:
        url (str): 文章的URL。
        timeout (int): 请求超时时间。

    Returns:
        BeautifulSoup: 解析后的文章内容。
    """
    try:

        response = await retry_request(client.get, url=url)  # 使用重试逻辑
        content = response.text
        soup = BeautifulSoup(content, 'html.parser')
        return soup
    except httpx.RequestError as e:
        logger.error(f"请求错误: {e}")
        return None

# 解析文章内容并提取数据
def parse_article_data(soup,article_data = {}):
    """解析文章内容并提取文本和图片链接。

    Args:
        soup (BeautifulSoup): 解析后的文章内容。

    Returns:
        dict: 包含文章文本和图片链接的数据字典。
    """

    article = soup.find('article')

    if article:
        content = article.get_text(separator='\n', strip=True)
        print("文本内容全文已生成")
        article_data['content'] = content

        # 获取文章中的图片链接
        images = article.find_all('img')
        img_links = [img.get('src') for img in images]
        article_data['images'] = img_links
        print("图片已生成")
    else:
        article_data['images'] = None
        logger.info("没有找到文章")

# gpt获取标题
async def get_gpt_summary_and_title(client, article_content):
    api_key = 'sk-snwSSPc5VkLWd6mU3cBd8e27211d46338a4c5fC7C52d651c'
    api_url = 'https://aiserver.marsyoo.com/v1/chat/completions'

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': 'gpt-3.5-turbo',
        'messages': [
            {
                'role': 'system',
                'content': '你是一个帮助生成文章标题和摘要的助手。'
            },
            {
                'role': 'user',
                'content': f"请为以下文章生成一个标题和摘要(摘要就是1-3个概括文章的关键字)：\n\n{article_content}"
            }
        ],
        'max_tokens': 100
    }

    try:
        # print("gpt???????????????????????????????????????")
        # response = await retry_request(client.post, api_url, json=payload, headers=headers)
        response = await retry_request(
            client.post,
            # max_retries=5,
            # retry_delay=(1, 3),
            url=api_url,
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        content = data['choices'][0]['message']['content']

        print("gpt请求成功")
        # 清理返回内容，去掉多余的标签
        lines = content.split('\n')
        title = lines[0].strip() if lines else ''
        summary = ' '.join([line.strip() for line in lines[1:] if line.strip()]) if len(lines) > 1 else ''

        # 去掉可能存在的“标题：”或“摘要：”等多余标识
        title = title.replace('标题：', '').replace('标题:', '').strip()
        summary = summary.replace('摘要：', '').replace('摘要:', '').strip()

        print("标题，摘要生成成功")
        return title, summary
    except httpx.RequestError as e:
        print(f"获取 GPT 响应时发生错误: {e}")
        return None, None
async def scrape_article_content_and_images(url: str):
    try:
        article_data = {'url': url}

        # 住宅代理信息
        # proxies = {
        #     'https://': "https://customer-cxjhzw_DBcRk-cc-us:Lsm666666666+@pr.oxylabs.io:7777"
        # }

        # 数据中心代理
        username = 'cxjhzw_2MZmd'
        password = 'Lsm666666666+'
        proxy = 'dc.oxylabs.io:8000'

        proxies = {
            "https://": f'https://user-{username}:{password}@{proxy}'
        }

        try:
            await fetch_article_details(url, proxies=proxies,article_data=article_data)
        except httpx.ConnectError as e:
            logger.error(f"连接错误: {e}")

        # 找到最后一个 '/' 的位置
        last_slash_index = url.rfind('/')
        # 从最后一个 '/' 开始获取后续的子字符串
        result = url[last_slash_index:]
        new_href = const_config.FREE_URL_PREFIX + result
        # print(f"截取以后的url为{url.lstrip('/')}")
        # logger.info(f'拼接后的链接为{new_href}')

        try:
            async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
                soup = await fetch_article_content(url=new_href,client=client)

                parse_article_data(soup,article_data=article_data)

                # 确保 article_data['content'] 被正确填充
                content = article_data.get('content', '')
                if content:
                    # 调用 GPT 生成文章摘要和标题
                    title, summary = await get_gpt_summary_and_title(client, content)
                    article_data['title'] = title
                    article_data['summary'] = summary
                else:
                    logger.warning("文章内容为空，无法生成标题和摘要")



            article_data_list.append(article_data)
        except httpx.ConnectError as e:
            logger.error(f"连接错误: {e}")
            article_data['error'] = f"连接错误: {e}"
    except Exception as e:
        failed_urls.add(url)
        logger.error(f"处理URL {url} 时发生错误: {e}")

async def run(playwright,keyword=None, refresh=False):
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
        await page.wait_for_load_state("load")

        if keyword is not None:
            await page.fill('[data-testid="headerSearchInput"]', keyword)
            await page.wait_for_load_state("load")
            await page.wait_for_timeout(2000)
            await page.keyboard.press('Enter')
            await page.wait_for_load_state("load")
            await page.wait_for_timeout(2000)
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
