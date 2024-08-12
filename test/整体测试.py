import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from random import random
import random

from playwright.async_api import Page, async_playwright
import uuid
import pdfkit
from bs4 import BeautifulSoup
import const_config
from logger_config import logger
from mongodb_config import insert_articles_batch
import global_exception_handler

article_data_list = []


async def simulate_mouse_movement(page: Page):
    # 获取页面的宽度和高度
    viewport_size = await page.evaluate('''() => {
        return { width: window.innerWidth, height: window.innerHeight };
    }''')

    width = viewport_size['width']
    height = viewport_size['height']

    # 随机移动鼠标
    for _ in range(random.randint(5, 10)):  # 随机滑动次数
        x = random.randint(0, width)
        y = random.randint(0, height)
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(1, 3))  # 随机停顿时间


async def handle_captcha(page: Page):
    try:
        # 等待页面完全加载
        await page.wait_for_load_state('networkidle', timeout=10000)  # 等待页面在10秒内完全加载

        # 尝试点击页面中的指定元素以触发验证码
        element_to_click = await page.query_selector('body > div.main-wrapper > div > h1')
        if element_to_click:
            logger.info("尝试点击页面中的元素以触发验证码")
            await element_to_click.click()  # 模拟点击 h1 元素
            await page.wait_for_timeout(2000)  # 等待2秒，看看验证码是否出现
        else:
            logger.info("未找到指定的元素")

        # 等待验证码复选框出现
        captcha_checkbox = await page.wait_for_selector('input[type="checkbox"]', timeout=30000)  # 等待最多10秒
        if captcha_checkbox:
            logger.info("验证码页面已出现，正在尝试通过验证")

            # 点击验证码复选框
            await captcha_checkbox.click()
            await page.wait_for_load_state('networkidle')  # 等待页面重新加载
            logger.info("验证通过")
        else:
            logger.info("未检测到验证码页面")
    except Exception as e:
        logger.error(f"处理验证码时出错: {e}")



# 将 Playwright 实例创建在全局
async def main():
    async with async_playwright() as playwright:
        await run(playwright)

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
        await page.wait_for_timeout(10)
        elements = await page.query_selector_all(const_config.SELECTOR)
        logger.info(f"正在进行第{i + 1}次滑动，共找到 {len(elements)} 条数据")
        i += 1
        if len(elements) >= const_config.MAX_ELEMENTS:
            break
        if i>10000:
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

async def reload_page(page: Page):
    try:
        await page.reload()
        await page.wait_for_load_state('networkidle')  # 等待页面完全加载
        logger.info('页面重新加载成功')
    except Exception as e:
        logger.error(f'重新加载页面时出错: {e}')
async def check_page_status(page: Page):
    try:
        element = await page.query_selector('heml')
        if element is None:
            logger.error('页面元素丢失，可能需要重新加载')
            await reload_page(page)
            # 进行重新加载或其他处理
    except Exception as e:
        logger.error(f'检查页面状态时出错: {e}')


# 模拟用户移动鼠标，滑动
async def simulate_user_activity(page: Page):
    """模拟用户行为，包括随机移动鼠标和滚动页面"""
    width = await page.evaluate('window.innerWidth')
    height = await page.evaluate('window.innerHeight')

    # 随机移动鼠标
    for _ in range(random.randint(5, 10)):
        x = random.randint(0, width)
        y = random.randint(0, height)
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(1, 3))

    # 模拟页面滚动
    for _ in range(random.randint(2, 5)):
        await page.mouse.wheel(0, random.randint(100, 500))
        await asyncio.sleep(random.uniform(2, 5))

# 访问页面，增加延迟
async def fetch_page_content(page: Page, url: str):
    """访问页面并模拟用户行为"""
    await page.goto(url, timeout=1200000)
    await page.wait_for_load_state('networkidle')

    # 随机等待时间
    await asyncio.sleep(random.uniform(3, 6))

    # 进行用户行为模拟
    await simulate_user_activity(page)

    # 获取页面内容
    return await page.content()


async def scrape_article_content_and_images(url, context):
    page=None
    article_data = {'url': url}

    try:
        page = await context.new_page()
        await fetch_page_content(page, url)  # 设置页面加载超时时间
        print("到达页面")
        # await page.wait_for_load_state('networkidle')  # 等待网络空闲
        # await reload_page(page)


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
        max_attempts =1  # 最大尝试次数
        attempt = 0  # 当前尝试次数

        while attempt < max_attempts:
            try:
                await asyncio.sleep(random.uniform(2, 5))
                await fetch_page_content(page, new_url)
                # await page.goto(new_url, timeout=1200000)  # 设置页面加载超时时间
                await page.wait_for_timeout(2000)  # 等待2秒

                # 尝试获取作者信息
                try:
                    author_locator = page.get_by_test_id("authorName")
                    article_data['author'] = await author_locator.inner_text()
                    if not article_data['author']:
                        raise ValueError("作者信息为空")
                except Exception as e:
                    logger.error(f"获取作者信息失败: {e}")
                    article_data['author'] = None
                    await page.reload()  # 重新加载页面
                    attempt += 1
                    continue  # 重新开始循环

                # 尝试获取评论数量
                try:
                    comments_locator = page.locator("section").get_by_label("responses")
                    article_data['comments'] = await comments_locator.inner_text()
                except:
                    article_data['comments'] = None

                # 尝试获取点赞量
                try:
                    likes_locator = page.locator(
                        '#root > div > div > div > div > article > div > div > section > div > div>div>div>div>div>div>div>div>div>div>div>div div > div > p > button '
                    )
                    article_data['likes'] = await likes_locator.inner_text()
                except:
                    article_data['likes'] = None

                logger.info(f'作者: {article_data["author"]}')
                logger.info(f'评论数量: {article_data["comments"]}')
                logger.info(f'点赞量: {article_data["likes"]}')

                if article_data['author']:
                    article_data_list.append(article_data)
                    logger.info(f"这次生成的数据为{article_data}")
                    break  # 成功获取作者信息，退出循环
                else:
                    logger.info(f"未能获取到作者信息，第 {attempt + 1} 次重试")
                    attempt += 1

            except Exception as e:
                logger.error(f"在尝试获取文章内容和图片时出错: {e}")
                attempt += 1

        if attempt == max_attempts:
            logger.error(f"多次尝试后仍未能获取到有效的作者信息，放弃该页面 {url}")


    finally:
        if page:
            try:
                await page.close()
            except Exception as e:
                logger.error(f'关闭页面时出错: {e}')


async def run(playwright, keyword=None, refresh=False):
    user_data_dir=os.path.abspath('../User Data')
    try:
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            # user_data_dir=r'C:\Users\86157\AppData\Local\Google\Chrome\User Data',
            # user_data_dir=r'D:\pythonProject\MediumArticleFetcher\User Data',
            # user_data_dir=r'./User Data', user_data_dir=r'D:\pythonProject\MediumArticleFetcher\User Data',
            # user_data_dir=r'./User Data',
            headless=False,
            viewport={"width": 1280, "height": 720}
        )
        # print("看看能否ok")
        logger.info(user_data_dir)
        # print(f"User data directory: {os.path.abspath('./User Data')}")
        page = await context.new_page()
        await page.goto("https://medium.com/")
        # 输出整个页面的文本内容
        content = await page.content()
        print(content)  # 打印页面内容到控制台

        await page.wait_for_load_state("load")
        await page.wait_for_timeout(2000)
        if keyword is not None:
            await page.fill('[data-testid="headerSearchInput"]', keyword)
            await page.keyboard.press('Enter')
            await page.wait_for_load_state("load")
            logger.info(f'已输入关键字搜索{keyword}')
            await page.wait_for_timeout(3000)
        else:
            await page.reload()
            await page.wait_for_load_state("load")
            logger.info("页面已刷新")
        html_str = await scroll_to_bottom(page)

        soup = await create_soup(html_str)
        urls = get_urls(soup)
        # urls = [
        #     "https://freedium.cfd/https://medium.com/scuzzbucket/a-fly-in-the-wall-4048d0304351?source=explore---------0-110--------------------0b81d643_2feb_4454_a806_3095e9488345-------15",
        #     "https://freedium.cfd/https://medium.com/whitespectre/beyond-front-end-metrics-harnessing-backend-insights-for-scale-up-success-124f26add48a?source=explore---------1-108--------------------0b81d643_2feb_4454_a806_3095e9488345-------15",
        #     "https://freedium.cfd/https://medium.com/analysts-corner/define-your-end-goal-with-business-objectives-61b915459bd4?source=explore---------2-108--------------------0b81d643_2feb_4454_a806_3095e9488345-------15",
        #     "https://freedium.cfd/https://medium.com/imogenes-notebook/how-much-does-the-spinning-3c03316dd9fd?source=explore---------3-108--------------------0b81d643_2feb_4454_a806_3095e9488345-------15"
        #     # "https://medium.com/the-philosophical-inn/the-spooky-quote-by-bren"
        # ]

        content_tasks = [scrape_article_content_and_images(url, context) for url in urls]
        await asyncio.gather(*content_tasks)

    finally:
        # 在所有任务完成后再关闭 context
        await context.close()
        insert_articles_batch(article_data_list)
        logger.info("本次抓取结束")


if __name__ == "__main__":
    global_exception_handler.GlobalExceptionHandler.setup()
    asyncio.run(main())
