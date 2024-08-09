from fastapi import FastAPI, HTTPException, Query, Path
from starlette.middleware.cors import CORSMiddleware
from fetch import run
from playwright.async_api import async_playwright
import asyncio

app = FastAPI()

# CORS配置
origins = [
    "http://localhost:3000",  # React开发服务器的URL
    "http://localhost:3001",  # React开发服务器的URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局锁和状态变量
fetch_lock = asyncio.Lock()
fetch_in_progress = False

# 无参数或Query参数访问
@app.get("/api/fetch")
async def fetch_data(keyword: str = Query(None, description="Keyword for search")):
    global fetch_in_progress
    if fetch_in_progress:
        return {"status": "error", "message": "当前操作正在进行中，请稍后再试。"}

    async with fetch_lock:
        if fetch_in_progress:
            return {"status": "error", "message": "当前操作正在进行中，请稍后再试。"}

        try:
            fetch_in_progress = True
            async with async_playwright() as playwright:
                # 根据是否提供了关键字来决定是刷新还是搜索
                if keyword:
                    await run(playwright, keyword=keyword)
                    message = f"关键字 '{keyword}' 的数据抓取成功。"
                else:
                    await run(playwright, refresh=True)
                    message = "数据抓取成功。"

            return {"status": "success", "message": message}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            fetch_in_progress = False

# 带路径参数访问
@app.get("/api/fetch/{keyword}")
async def fetch_data_with_path(keyword: str = Path(..., description="Keyword for search")):
    global fetch_in_progress
    if fetch_in_progress:
        return {"status": "error", "message": "当前操作正在进行中，请稍后再试。"}

    async with fetch_lock:
        if fetch_in_progress:
            return {"status": "error", "message": "当前操作正在进行中，请稍后再试。"}

        try:
            fetch_in_progress = True
            async with async_playwright() as playwright:
                await run(playwright, keyword=keyword)
                message = f"关键字 '{keyword}' 的数据抓取成功。"

            return {"status": "success", "message": message}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            fetch_in_progress = False

@app.on_event("startup")
async def startup_event():
    async def fetch_on_startup():
        global fetch_in_progress
        async with fetch_lock:
            fetch_in_progress = True
            async with async_playwright() as playwright:
                await run(playwright, refresh=True)
            fetch_in_progress = False

    asyncio.create_task(fetch_on_startup())

@app.on_event("startup")
async def startup_event():
    async def periodic_fetch():
        global fetch_in_progress
        while True:
            async with fetch_lock:
                fetch_in_progress = True
                async with async_playwright() as playwright:
                    await run(playwright, refresh=True)
                fetch_in_progress = False
            await asyncio.sleep(12 * 60 * 60)  # 等待12个小时

    asyncio.create_task(periodic_fetch())

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
