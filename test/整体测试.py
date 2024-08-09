import asyncio
from concurrent.futures import ThreadPoolExecutor
from playwright.async_api import Page, async_playwright
import uuid
import pdfkit
from bs4 import BeautifulSoup
import const_config
from logger_config import logger
from mongodb_config import insert_articles_batch
import global_exception_handler

article_data_list = []

# 将 Playwright 实例创建在全局
async def main():
    async with async_playwright() as playwright:
        await run(playwright)

async def create_soup(page_content):
    soup = BeautifulSoup(page_content, 'lxml')
    return soup

async def scroll_to_bottom(page: Page):
    await page.wait_for_timeout(2000)
    i = 1
    html_str = ''
    while True:
        await page.mouse.wheel(0, const_config.SCROLL_DISTANCE)
        await page.wait_for_timeout(100)
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
    # try:
    #     pdfkit.from_url(url, output_path, configuration=config)
    #     logger.info(f'PDF文件已保存到: {output_path}')
    # except Exception as e:
    #     logger.error(f'未能成功，失败的{url}为: {e}')
    #     raise
    pass

def remove_prefix(url, prefix="https://freedium.cfd/"):
    return url[len(prefix):] if url.startswith(prefix) else url

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
                break
            except Exception as e:
                if attempt < retry_attempts :
                    logger.error(f'生成pdf失败,这是第 {attempt + 1}次失败，将继续重试: {e}')
                    await asyncio.sleep(2)  # Wait before retrying
                else:
                    logger.error(f'生成pdf失败,重试达到上限，失败的URL为 {url}: {e}')

async def scrape_article_content_and_images(url, context):
    page=None
    article_data = {'url': url}

    try:
        page = await context.new_page()
        await page.goto(url, timeout=60000)  # 设置页面加载超时时间
        await page.wait_for_load_state('networkidle')  # 等待网络空闲


        try:
            content = page.locator(
                r'body > div.container.w-full.md\:max-w-3xl.mx-auto.pt-20.break-words.text-gray-900.dark\:text-gray-200.bg-white.dark\:bg-gray-800 > div.w-full.px-4.md\:px-6.text-xl.text-gray-800.dark\:text-gray-100.leading-normal > div.main-content.mt-8')
            text = await content.inner_text()
            article_data['content'] = text
        except:
            article_data['content'] = article_data.get('content', None)
        logger.info(f'文章内容: {text[:5]}...')  # 只记录前100个字符

        img_element = await page.query_selector('.main-content img')
        if img_element is None:
            logger.info('没有找到 img 元素')
            article_data['images'] = []
        else:
            imgs = page.locator('.main-content img')
            img_count = await imgs.count()
            images = []
            for i in range(img_count):
                img_element = imgs.nth(i)
                src = await img_element.get_attribute('src')
                if not src:
                    src = await img_element.get_attribute('data-src')
                images.append(src)
            article_data['images'] = images

        new_url = remove_prefix(url)
        await page.goto(new_url, timeout=60000)  # 设置页面加载超时时间

        try:
            author_locator = page.get_by_test_id("authorName")
            article_data['author'] = await author_locator.inner_text()
        except:
            article_data['author'] = article_data.get('author', None)

        try:
            comments_locator = page.locator("section").get_by_label("responses")
            article_data['comments'] = await comments_locator.inner_text()
        except:
            article_data['comments'] = article_data.get('comments', None)
        try:
            likes_locator = page.locator(
                ' #root > div > div > div:nth-child(2) > div > article > div > div > section > div > div>div>div>div>div>div>div>div>div>div>div>div div > div > p > button ')
            article_data['likes'] = await likes_locator.inner_text()
        except:
            article_data['likes'] = article_data.get('likes', None)

        logger.info(f'作者: {article_data["author"]}')
        logger.info(f'评论数量: {article_data["comments"]}')
        logger.info(f'点赞量: {article_data["likes"]}')

        article_data_list.append(article_data)
        logger.info(f"这次生成的数据为{article_data}")

    except Exception as e:
        logger.error(f'{url}文章无法生成结构化数据: {e}')
        # 检查并填充缺失的数据
        article_data['content'] = article_data.get('content', None)
        article_data['images'] = article_data.get('images', None)
        article_data['author'] = article_data.get('author', None)
        article_data['comments'] = article_data.get('comments', None)
        article_data['likes'] = article_data.get('likes', None)

        article_data_list.append(article_data)

    finally:
        if page:
            try:
                await page.close()
            except Exception as e:
                logger.error(f'关闭页面时出错: {e}')

async def run(playwright, keyword=None, refresh=False):
    try:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=r'C:\Users\86157\AppData\Local\Google\Chrome\User Data',
            headless=True,
            viewport={"width": 1280, "height": 720}
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
        else:
            await page.reload()
            await page.wait_for_load_state("load")
            logger.info("页面已刷新")
        html_str = await scroll_to_bottom(page)

        soup = await create_soup(html_str)
        urls = get_urls(soup)

        # 创建任务
        timeout_seconds = 30  # 每个任务的超时时间
        content_tasks = [
            asyncio.create_task(
                asyncio.wait_for(scrape_article_content_and_images(url, context), timeout=timeout_seconds)
            )
            for url in urls
        ]

        # 使用 asyncio.wait 处理任务
        done, pending = await asyncio.wait(content_tasks, return_when=asyncio.ALL_COMPLETED)

        # 处理超时的任务
        max_retries = 3  # 最大重试次数
        retry_count = 0

        while pending and retry_count < max_retries:
            retry_count += 1
            logger.info(f'第 {retry_count} 次重试处理超时任务')
            new_tasks = [
                asyncio.create_task(
                    asyncio.wait_for(scrape_article_content_and_images(urls[idx], context), timeout=timeout_seconds)
                )
                for idx, task in enumerate(content_tasks) if task in pending
            ]

            done, pending = await asyncio.wait(new_tasks, return_when=asyncio.ALL_COMPLETED)

        # 最终处理成功完成的任务
        for task in done:
            try:
                await task  # 这将引发任务中的任何异常
            except asyncio.TimeoutError:
                logger.error(f'任务 {task} 超时')
            except Exception as e:
                logger.error(f'任务 {task} 失败，错误: {e}')

        if pending:
            logger.warning(f'有任务在重试 {max_retries} 次后仍未完成: {pending}')

    finally:
        await context.close()

if __name__ == "__main__":
    global_exception_handler.GlobalExceptionHandler.setup()
    asyncio.run(main())
