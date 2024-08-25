import httpx
import asyncio

username = 'cxjhzw_2MZmd'
password = 'Lsm666666666+'
proxy = 'dc.oxylabs.io:8000'

proxies = {
    "https://": f'https://user-{username}:{password}@{proxy}'
}

async def test_proxy():
    async with httpx.AsyncClient(proxies=proxies, timeout=10) as client:
        try:
            # response = await client.get("https://ip.oxylabs.io/location")
            response = await client.get("https://medium.com/")
            response.raise_for_status()
            print(f"代理 {proxies} 工作正常")
            print(response.text)
        except httpx.RequestError as e:
            print(f"代理 {proxies} 请求失败: {e}")
        except httpx.HTTPStatusError as e:
            print(f"代理 {proxies} 请求失败，状态码: {e.response.status_code}")
            print(f"响应内容: {e.response.text}")
        except Exception as e:
            print(f"代理 {proxies} 请求失败，未知错误: {e}")

async def main():
    await test_proxy()

if __name__ == "__main__":
    asyncio.run(main())
