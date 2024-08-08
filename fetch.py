import asyncio
from concurrent.futures import ThreadPoolExecutor
from playwright.async_api import Page, async_playwright
import uuid
import gridfs
import pdfkit
from bs4 import BeautifulSoup
import const_config
from logger_config import logger
from mongodb_config import insert_article_data
import global_exception_handler

article_data_list = []
async def create_soup(page_content):
    soup = BeautifulSoup(page_content, 'lxml')
    return soup


async def scroll_to_bottom(page: Page):
    await page.wait_for_timeout(2000)
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
# 去除前缀函数
def remove_prefix(url, prefix="https://freedium.cfd/"):
    return url[len(prefix):] if url.startswith(prefix) else url

# 生成pdf的
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
                # fs = gridfs.GridFS(db)
                # with open(output_path, 'rb') as f:
                #     fs.put(f, filename=str(id))
                # logger.info(f'PDF文件已保存到数据库: {output_path}')
                logger.info(f'PDF文件已保存到: {output_path}')
                break
            except Exception as e:
                logger.error(f'Attempt {attempt + 1} failed for URL {url}: {e}')
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(2)  # Wait before retrying

# 保存文章内容和图片
async def scrape_article_content_and_images(url):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(url, timeout=60000)  # 设置页面加载超时时间
            await page.wait_for_load_state('networkidle')  # 等待网络空闲

            article_data = {'url': url}

            # 获取文章内容
            content = page.locator(
                r'body > div.container.w-full.md\:max-w-3xl.mx-auto.pt-20.break-words.text-gray-900.dark\:text-gray-200.bg-white.dark\:bg-gray-800 > div.w-full.px-4.md\:px-6.text-xl.text-gray-800.dark\:text-gray-100.leading-normal > div.main-content.mt-8')
            text = await content.inner_text()
            # article_data['content'] = text
            logger.info(f'文章内容: {text[:5]}...')  # 只记录前100个字符

            # 检查 img 元素是否存在
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
                    outer_html = await img_element.evaluate('element => element.outerHTML')
                    src = await img_element.get_attribute('src')
                    if not src:
                        src = await img_element.get_attribute('data-src')
                    images.append(src)
                article_data['images'] = images

            # 获取作者、评论和点赞
            new_url = remove_prefix(url)
            await page.goto(new_url, timeout=60000)  # 设置页面加载超时时间
            # await page.wait_for_load_state('networkidle')  # 等待网络空闲




            author_locator = page.get_by_test_id("authorName")
            # comments_locator = page.locator(
            #     '#root > div > div.l.c > div:nth-child(2) > div.ft.fu.fv.fw.fx.l > article > div > div > section div:nth-child(2) > div > button > p > span')
            likes_locator = page.locator(
                '#root > div > div > div:nth-child(2) > div > article > div > div > section > div > div div > div > p > button ')
            comments_locator = page.locator("section").get_by_label("responses")
            article_data['author'] = await author_locator.inner_text()
            article_data['comments'] = await comments_locator.inner_text()
            article_data['likes'] = await likes_locator.inner_text()

            logger.info(f'作者: {article_data["author"]}')
            logger.info(f'评论数量: {article_data["comments"]}')
            logger.info(f'点赞量: {article_data["likes"]}')

            article_data_list.append(article_data)
            logger.info(f"这次生成的数据为{article_data}")

        except Exception as e:
            logger.error(f'文章无法生成结构化数据: {e}')

        finally:
            await context.close()
            await browser.close()


async def run(playwright, keyword=None, refresh=False):
    context = await playwright.chromium.launch_persistent_context(
        user_data_dir=r'C:\Users\86157\AppData\Local\Google\Chrome\User Data',
        headless=False,
        viewport={"width": 1280, "height": 720}
    )
    page = await context.new_page()  # Ensure you use await to get the Page object
    await page.goto("https://medium.com/")
    await page.wait_for_load_state("load")
    # await page.wait_for_timeout(2000)
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

    # 生成pdf
    semaphore = asyncio.Semaphore(5)  # 限制并发请求数为5
    pdf_tasks = [by_url_get_content(url, semaphore) for url in urls]
    await asyncio.gather(*pdf_tasks)

    content_tasks=[scrape_article_content_and_images(url) for url in urls]
    await asyncio.gather(*content_tasks)

    for article_data in article_data_list:
        insert_article_data(article_data)


if __name__ == "__main__":
    global_exception_handler.GlobalExceptionHandler.setup()


    async def main():
        async with async_playwright() as playwright:
            await run(playwright)


    asyncio.run(main())
