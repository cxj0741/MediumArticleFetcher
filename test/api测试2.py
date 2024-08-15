from fastapi import FastAPI, HTTPException, Query, Path
from starlette.middleware.cors import CORSMiddleware
from fetch import run
from playwright.async_api import async_playwright
import asyncio
import logging

from logger_config import logger
from test.api测试 import initialize_fetch

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
fetch_task = None

async def fetch_data_internal(keyword: str = None, refresh: bool = False):
    global fetch_in_progress
    if fetch_in_progress:
        return {"status": "error", "message": "当前操作正在进行中，请稍后再试。"}

    async with fetch_lock:
        if fetch_in_progress:
            return {"status": "error", "message": "当前操作正在进行中，请稍后再试。"}

        try:
            fetch_in_progress = True
            async with async_playwright() as playwright:
                if keyword:
                    await initialize_fetch()
                    message = f"关键字 '{keyword}' 的数据抓取成功。"
                elif refresh:
                    await run(playwright, refresh=True)
                    message = "数据刷新成功。"
                else:
                    message = "没有提供关键字或刷新选项。"

            return {"status": "success", "message": message}
        except asyncio.CancelledError:
            logging.info("抓取任务被取消")
            return {"status": "error", "message": "抓取任务已取消。"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            fetch_in_progress = False

@app.get("/api/fetch")
async def fetch_data(keyword: str = Query(None, description="Keyword for search")):
    # 如果没有提供keyword，则默认执行刷新操作
    refresh = keyword is None
    return await fetch_data_internal(keyword=keyword, refresh=refresh)

@app.get("/api/fetch/{keyword}")
async def fetch_data_with_path(keyword: str = Path(..., description="Keyword for search")):
    return await fetch_data_internal(keyword=keyword)

@app.on_event("startup")
async def startup_event():
    global fetch_task

    # async def fetch_on_startup():
    #     await fetch_data_internal(refresh=True)

    async def periodic_fetch():
        global fetch_task
        while True:
            if fetch_task and not fetch_task.done():
                logging.info("等待当前任务完成")
                await fetch_task
            fetch_task = asyncio.create_task(fetch_data_internal(refresh=True))
            # await asyncio.sleep(12 * 60 * 60)  # 等待12个小时
            await asyncio.sleep( 30 * 60)  # 等待12个小时

    # # 执行启动时抓取数据和定时任务
    # fetch_task = asyncio.create_task(fetch_on_startup())
    asyncio.create_task(periodic_fetch())

# @app.get("/api/stop")
# async def stop_fetch():
#     """停止当前抓取任务"""
#     global fetch_task, fetch_in_progress
#     if fetch_task and not fetch_task.done():
#         logging.info("取消抓取任务")
#         fetch_task.cancel()
#         fetch_in_progress = False  # 确保任务被取消时更新状态
#         try:
#             await fetch_task  # 等待任务完全取消
#         except asyncio.CancelledError:
#             logging.info("抓取任务已取消")
#         return {"status": "success", "message": "当前抓取任务已停止。"}
#     else:
#         logging.info("没有正在进行的抓取任务")
#         return {"status": "info", "message": "没有正在进行的抓取任务。"}

@app.get("/api/status")
async def get_status():
    """查询当前抓取状态"""
    if fetch_in_progress:
        return {"status": "info", "message": "当前抓取中"}
    else:
        return {"status": "info", "message": "当前空闲"}

if __name__ == '__main__':
    import uvicorn

    logger.info("开始记录日志")
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
