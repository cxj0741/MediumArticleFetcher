from fastapi import FastAPI, HTTPException, Query
from starlette.middleware.cors import CORSMiddleware
from fetch import run
from playwright.async_api import async_playwright
import asyncio

app = FastAPI()

# 允许跨域请求的来源
origins = [
    "http://localhost:3000",  # React开发服务器的URL
    "http://localhost:3001",  # React开发服务器的URL
]

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/fetch")
async def fetch_data(keyword: str = Query(None, description="Keyword for search")):
    try:
        async with async_playwright() as playwright:
            # 根据是否提供了关键字来决定是刷新还是搜索
            if keyword:
                await run(playwright, keyword=keyword)
                message = f"Data fetched successfully for keyword: {keyword}."
            else:
                await run(playwright, refresh=True)
                message = "Data fetched successfully with refresh."

        return {"status": "success", "message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 保证服务启动，可以自动执行抓取数据代码
@app.on_event("startup")
async def startup_event():
    async def fetch_on_startup():
        async with async_playwright() as playwright:
            await run(playwright, refresh=True)

    asyncio.create_task(fetch_on_startup())

@app.on_event("startup")
async def startup_event():
    async def periodic_fetch():
        while True:
            async with async_playwright() as playwright:
                await run(playwright, refresh=True)
            await asyncio.sleep(12 * 60 * 60)  # 等待12个小时

    asyncio.create_task(periodic_fetch())

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")