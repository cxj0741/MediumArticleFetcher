import asyncio
import logging
from logger_config import logger


async def scrape_article_content_and_images(url: str):
    # 模拟处理 URL 的逻辑
    if "fail" in url:  # 假设包含 "fail" 的 URL 会失败
        raise Exception("模拟处理失败的URL")
    else:
        logger.info(f"成功处理: {url}")
        # 在这里处理成功的URL逻辑

async def process_urls(urls):
    for url in urls:
        try:
            await scrape_article_content_and_images(url)
        except Exception as e:
            logger.error(f"处理 {url} 时发生错误: {e}")
            # 将失败的 URL 写入文本文件
            with open("failed_urls.txt", "a") as f:
                f.write(f"{url}\n")
            logger.info(f"已将失败的URL写入 failed_urls.txt: {url}")

if __name__ == "__main__":
    urls_to_process = [
        "https://example.com/article1",
        "https://example.com/fail-article2",  # 模拟失败的URL
        "https://example.com/article3",
        "https://example.com/fail-article4"   # 模拟失败的URL
    ]
    asyncio.run(process_urls(urls_to_process))
