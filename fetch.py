import asyncio
import time
import uuid

import gridfs
import pdfkit
from bs4 import BeautifulSoup
import const_config
from playwright.sync_api import sync_playwright
from logger_config import logger
from mongodb_config import db
import global_exception_handler

# 用于定位html中的具体信息
def create_soup(page_content):
    # 传入参数，实例化bs这个类
    soup = BeautifulSoup(page_content, 'lxml')
    return soup

# 用于滑动窗口
def scroll_to_bottom(page):
    # 然后将页面滚动到上次的位置
    # 多次调用滚动
    i=1
    # 创建一个列表来存储 HTML 代码
    html_str=''
    while True:
        page.mouse.wheel(0, const_config.SCROLL_DISTANCE) #水平方向和垂直方向进行滚动
        page.wait_for_timeout(1)  # 每次滚动后等待片刻
        # 查询特定选择器匹配的元素数量
        elements = page.query_selector_all(const_config.SELECTOR)
        logger.info(f"正在进行第{i + 1}次滑动，共找到 {len(elements)} 条数据")
        i+=1
        if len(elements) >=const_config.MAX_ELEMENTS: break
    # 获取匹配元素的父级元素
    # HTML
    # 代码
    # 获取前 100 个或全部累积的元素的父级元素 HTML 代码
    for index, element in enumerate(elements[:const_config.MAX_ELEMENTS], start=1):
        parent_html = element.evaluate('(element) => element.parentElement.outerHTML')
        html_str+=parent_html
        logger.info(f"第 {index} 条数据的父级元素 HTML: {parent_html}")

    return html_str

# 获取所有拼接以后的文章连接
def get_urls(soup):
    list_urls=[]
    find_all = soup.find_all('a')
    for a in find_all:
        href = a.get('href')
        if href is not None:
            logger.info(f'获取到的链接为{href}')
            new_href = const_config.FREE_URL_PREFIX+const_config.BASE_URL+href
            logger.info(f'拼接后到的链接为{new_href}')
            list_urls.append(new_href)
    return list_urls

# 根据文章链接获取pdf文本内容
def by_url_get_content(url):
    # 替换为你的 wkhtmltopdf 可执行文件的实际路径
    path_to_wkhtmltopdf = r'D:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    id=uuid.uuid4()
    output_path = f'D:\\articles\\article_{id}.pdf'
    config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
    pdfkit.from_url(url, output_path, configuration=config)

#   插入数据
    # 创建GridFS对象
    fs = gridfs.GridFS(db)

    # 将PDF文件存储到GridFS中
    with open(output_path, 'rb') as f:
        file_id = fs.put(f, filename=str(id))


def run(playwright) -> None:
    # 启动 Playwright 和持久化上下文
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=r'C:\Users\86157\AppData\Local\Google\Chrome\User Data',
        headless=False,  # 设置为 False 以打开浏览器窗口
        viewport={"width": 1280, "height": 720}  # 设置浏览器窗口大小
    )
    page = context.new_page()

    # 访问目标网站
    page.goto("https://medium.com/")

    # 等待页面加载完成
    page.wait_for_load_state("load")
    # 滑动保证数据加载并且获取
    html_str = scroll_to_bottom(page)
    # print(html_list)

    # 进行html的解析，获取到拼接之后的文章链接
    soup = create_soup(html_str)
    urls = get_urls(soup)
    # print(urls)

    # 获取每个url的文本内容并且插入数据库
    for url in urls:
        # 捕获异常确保url转pdf失败，继续执行下一次
        try:
            by_url_get_content(url)
            logger.info(f"将该{url}放入数据库成功")
        except Exception as e:
            logger.error(f'文章转pdf放入数据库出现错误：{e}')

    # page.wait_for_timeout(10000)
    # 清理
    context.close()

# 设置全局异常处理器
global_exception_handler.GlobalExceptionHandler.setup()

with sync_playwright() as playwright:
    run(playwright)
