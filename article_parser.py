import asyncio
import httpx
from bs4 import BeautifulSoup
import logging
import re

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 重试请求函数
async def retry_request(func, *args, **kwargs):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except httpx.RequestError as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(f"请求失败，正在重试 ({attempt + 1}/{max_retries}): {e}")
            await asyncio.sleep(1)

# 请求文章内容并返回解析后的 BeautifulSoup 对象
async def fetch_article_content(url, timeout=300, client=None):
    url="https://www.freedium.cfd/"+url
    print("1111111111111111111111111111111111111111")
    """通过URL获取文章内容并返回BeautifulSoup对象。

    Args:
        url (str): 文章的URL。
        timeout (int): 请求超时时间。
        client (httpx.AsyncClient): 异步HTTP客户端。

    Returns:
        BeautifulSoup: 解析后的文章内容。
    """
    try:
        if client is None:
            async with httpx.AsyncClient() as client:
                response = await retry_request(client.get, url=url, timeout=timeout)
        else:
            response = await retry_request(client.get, url=url, timeout=timeout)
        content = response.text
        soup = BeautifulSoup(content, 'html.parser')
        return soup
    except httpx.RequestError as e:
        logger.error(f"请求错误: {e}")
        return None

def clean_text(text):
    # 去除多余的空行，但保留段落结构
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 去除行首和行尾的空白字符
    text = '\n'.join(line.strip() for line in text.split('\n'))
    return text.strip()

def parse_article_data(soup, article_data={}):
    print(soup)
    """解析文章内容并提取文本和图片链接。"""
    main_content = soup.find(class_='main-content')
    if main_content:
        # 获取文本内容，保留换行符
        content = main_content.get_text(separator='\n', strip=True)
        # 清理文本
        content = clean_text(content)
        article_data['content'] = content
        logger.info("文本内容全文已生成并格式化")

        # 查找所有图片，包括懒加载的图片
        images = soup.find_all('img')
        img_links = []
        for img in images:
            src = img.get('src') or img.get('data-src')
            if src:
                img_links.append(src)
        
        article_data['images'] = img_links
        logger.info(f"找到 {len(img_links)} 个图片链接")
    else:
        article_data['content'] = None
        article_data['images'] = None
        logger.info("没有找到主要内容")
    
    return article_data
  
    

async def main():
    # url = "https://www.freedium.cfd/https://medium.com/@beingpax/why-fabric-ai-can-change-the-way-you-use-ai-973e725354da"
    # url = "https://www.freedium.cfd/https://medium.com/crows-feet/i-may-never-find-a-full-time-job-again-84fd220cd965"
    url = "https://www.freedium.cfd/https://medium.com/stackademic/10-extremely-useful-front-end-libraries-you-might-have-been-looking-for-ce652e244505"
    async with httpx.AsyncClient() as client:
        soup = await fetch_article_content(url, client=client)
        if soup:
            article_data = parse_article_data(soup)
            print(article_data)
        else:
            print("无法获取文章内容")

# 使用异步运行时来执行 main 函数
if __name__ == "__main__":
    asyncio.run(main())