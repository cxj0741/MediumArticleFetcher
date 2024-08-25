import asyncio
import httpx
from bs4 import BeautifulSoup
import logging

# 设置日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_article_content_and_images(url: str):
    article_data = {'url': url}

    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()  # 检查HTTP状态码

            content = response.text
            soup = BeautifulSoup(content, 'html.parser')
            # print(soup)

            # 获取文章内容
            article = soup.find('article')
            # print(article)
            if article:
                content = article.get_text(separator='\n', strip=True)
                article_data['content'] = content

                # 获取文章中的图片链接
                images = article.find_all('img')
                # print(images)
                img_links = [img.get('src') for img in images]
                article_data['images'] = img_links
                print(article_data['images'])
            else:
                article_data['content'] = None
                article_data['images'] = None
                logger.info("没有找到文章内容")

    except httpx.RequestError as e:
        logger.error(f"请求错误: {e}")
        article_data['error'] = f"请求错误: {e}"
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP状态错误: {e}")
        article_data['error'] = f"HTTP状态错误: {e}"

    return article_data

async def main():
    url = r"https://readmedium.com/the-unbearable-triteness-of-being-openai-0c6c8b1df6af"  # 替换为你想要测试的URL
    article_data = await fetch_article_content_and_images(url)

    # 输出结果
    # if 'content' in article_data and article_data['content']:
    #     print("文章内容:")
    #     print(article_data['content'])
    # if 'images' in article_data and article_data['images']:
    #     print("\n图片链接:")
    #     for img in article_data['images']:
    #         print(img)

if __name__ == "__main__":
    asyncio.run(main())

