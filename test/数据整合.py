from playwright.async_api import async_playwright
from logger_config import logger

def remove_prefix(url, prefix="https://freedium.cfd/"):
    return url[len(prefix):] if url.startswith(prefix) else url

article_data_list = []


async def run(url):
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
            comments_locator=page.locator("section").get_by_label("responses")
            article_data['author'] = await author_locator.inner_text()
            article_data['comments'] = await comments_locator.inner_text()
            article_data['likes'] = await likes_locator.inner_text()

            logger.info(f'作者: {article_data["author"]}')
            logger.info(f'评论数量: {article_data["comments"]}')
            logger.info(f'点赞量: {article_data["likes"]}')

            article_data_list.append(article_data)
            print(article_data)

        except Exception as e:
            logger.error(f'Error processing URL {url}: {e}')

        finally:
            await context.close()
            await browser.close()


async def main():
    async with async_playwright() as playwright:
        urls = [
            # "https://freedium.cfd/https://medium.com/scuzzbucket/a-fly-in-the-wall-4048d0304351?source=explore---------0-110--------------------0b81d643_2feb_4454_a806_3095e9488345-------15",
            # "https://freedium.cfd/https://medium.com/whitespectre/beyond-front-end-metrics-harnessing-backend-insights-for-scale-up-success-124f26add48a?source=explore---------1-108--------------------0b81d643_2feb_4454_a806_3095e9488345-------15",
            # "https://freedium.cfd/https://medium.com/analysts-corner/define-your-end-goal-with-business-objectives-61b915459bd4?source=explore---------2-108--------------------0b81d643_2feb_4454_a806_3095e9488345-------15",
            # "https://freedium.cfd/https://medium.com/imogenes-notebook/how-much-does-the-spinning-3c03316dd9fd?source=explore---------3-108--------------------0b81d643_2feb_4454_a806_3095e9488345-------15"
            "https://medium.com/the-philosophical-inn/the-spooky-quote-by-bren"
        ]
        content_tasks = [run(url) for url in urls]
        await asyncio.gather(*content_tasks)

        # Process or save `article_data_list` here
        logger.info(f'所有文章数据: {article_data_list}')

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
