import httpx

async def get_gpt_summary_and_title(article_content):
    api_key = 'sk-SHmk1bH3mnEsBVP0E51eE94687A74a728d8d07253eA1257a'
    api_url = 'https://aiserver.marsyoo.com/v1/chat/completions'  # 完整的 API 端点可能需要附加路径

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

    async with httpx.AsyncClient() as client:
        response = await client.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        content = data['choices'][0]['message']['content']
        return content

# 在 asyncio 环境中调用
import asyncio

async def main():
    article_content = "这是文章内容的示例。"
    summary = await get_gpt_summary_and_title(article_content)
    print(summary)

if __name__ == '__main__':
    asyncio.run(main())
