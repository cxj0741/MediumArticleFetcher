import httpx
import asyncio
# 数据中心的代理
async def fetch(url: str, proxies: dict) -> None:
    async with httpx.AsyncClient(proxies=proxies, timeout=180) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()  # 检查是否请求成功
            print("Response:", response.text)  # 打印响应内容
        except httpx.RequestError as e:
            print(f"请求失败: {e}")
        except httpx.HTTPStatusError as e:
            print(f"HTTP状态错误: {e}")

async def main():
    # url = 'https://httpbin.org/ip'
    url = 'https://medium.com/'
    username = 'cxjhzw_2MZmd'
    password = 'Lsm666666666+'
    proxy = 'dc.oxylabs.io:8000'  # 8000端口用于轮换代理
    proxies = {
        # 'https://': f'https://user-{username}:{password}@{proxy}'
        'https://': "https://customer-cxjhzw_DBcRk-cc-us:Lsm666666666+@pr.oxylabs.io:7777"
    }
    await fetch(url, proxies)

# 运行异步主函数
if __name__ == "__main__":
    asyncio.run(main())
