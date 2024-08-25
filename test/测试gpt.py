import asyncio
import os
import random
import httpx
from logger_config import logger


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

# 异步调用
async def process_failed_url(url, count, temp_failed_urls, permanent_failures):
    try:
        # 在这里处理 URL
        print(f"重新处理 URL: {url} (失败次数: {count})")
        await scrape_article_content_and_images(url)  # 异步调用抓取函数
        temp_failed_urls.pop(url, None)  # 将处理成功的 URL 清除
    except Exception as e:
        # 处理失败，重新记录失败 URL，并增加失败次数
        if count < 5:
            temp_failed_urls[url] = count + 1
        else:
            # 将失败次数达到最大值的 URL 写入永久失败列表
            permanent_failures.append(f"{url},{count}")



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
            # 记录调试信息
            url = kwargs.get('url', '未知URL')
            json_payload = kwargs.get('json', '无负载')
            headers = kwargs.get('headers', '无头部信息')
            logger.debug(f"发起请求: {url} with payload: {json_payload} and headers: {headers}")

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


# async def get_gpt_summary_and_title(client, article_content):
#     # api_key = 'sk-ozYXQPQjeu0xCHFg0a1f329dA2194689931b8a6a6809558c'
#     api_key = 'sk-snwSSPc5VkLWd6mU3cBd8e27211d46338a4c5fC7C52d651c'
#     api_url = 'https://aiserver.marsyoo.com/v1/chat/completions'
#
#
#
#     # api_url = 'https://api.ezchat.top/v1/chat/completions'
#
#     headers = {
#         'Authorization': f'Bearer {api_key}',
#         'Content-Type': 'application/json',
#     }
#     payload = {
#         'model': 'gpt-3.5-turbo',
#         'messages': [
#             {
#                 'role': 'system',
#                 'content': '你是一个帮助生成文章标题和摘要的助手。'
#             },
#             {
#                 'role': 'user',
#                 'content': f"请为以下文章生成一个标题和摘要(摘要就是1-3个概括文章的关键字)：\n\n{article_content}"
#             }
#         ],
#         'max_tokens': 100
#     }
#
#     try:
#         response = await retry_request(
#             client.post,
#             max_retries=5,
#             retry_delay=(1, 3),
#             url=api_url,
#             json=payload,
#             headers=headers
#         )
#         # response= await client.post(url=api_url, headers=headers, json=payload)
#         response.raise_for_status()
#         data = response.json()
#         content = data['choices'][0]['message']['content']
#
#         # 清理返回内容，去掉多余的标签
#         lines = content.split('\n')
#         title = lines[0].strip() if lines else ''
#         summary = ' '.join([line.strip() for line in lines[1:] if line.strip()]) if len(lines) > 1 else ''
#
#         # 去掉可能存在的“标题：”或“摘要：”等多余标识
#         title = title.replace('标题：', '').replace('标题:', '').strip()
#         summary = summary.replace('摘要：', '').replace('摘要:', '').strip()
#
#         return title, summary
#     except httpx.RequestError as e:
#         print(f"获取 GPT 响应时发生错误: {e}")
#         return None, None
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
        'max_tokens': 250
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

async def main():
    article_content = """
       ...（省略的文章内容）...
       """
    async with httpx.AsyncClient() as client:
        title, summary = await get_gpt_summary_and_title(client, article_content)
        print("Title:", title)
        print("Summary:", summary)


if __name__ == '__main__':
    asyncio.run(main())
