import httpx
import asyncio

async def test_proxy(proxy: str):
    async with httpx.AsyncClient(proxies={"https://": proxy}, timeout=10) as client:
        try:
            response = await client.get("https://ip.oxylabs.io/location")
            response.raise_for_status()
            print(f"代理 {proxy} 工作正常")
            print(response.text)  # 打印响应内容以确认代理是否正常工作
        except httpx.RequestError as e:
            print(f"代理 {proxy} 请求失败: {e}")
        except httpx.HTTPStatusError as e:
            print(f"代理 {proxy} 请求失败，状态码: {e.response.status_code}")

async def main():
    # 端点生成器生成的代理端点
    proxy = "https://customer-cxjhzw_DBcRk:Lsm666666666+@pr.oxylabs.io:7777"
    # 'https://': "https://customer-cxjhzw_DBcRk:Lsm666666666+@pr.oxylabs.io:10000"
    await test_proxy(proxy)

if __name__ == "__main__":
    asyncio.run(main())
