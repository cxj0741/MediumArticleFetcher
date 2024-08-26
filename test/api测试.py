import random
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Query, Path
from starlette.middleware.cors import CORSMiddleware
from fetch import fetch_main  # 假设 fetch_main 是你的抓取逻辑函数
import asyncio
import logging

from logger_config import logger

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

            if keyword:
                await fetch_main(keyword=keyword)
                message = f"关键字 '{keyword}' 的数据抓取成功。"
            elif refresh:
                await fetch_main(refresh=True)
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
    # 如果没有提供 keyword，则默认执行刷新操作
    refresh = keyword is None
    return await fetch_data_internal(keyword=keyword, refresh=refresh)

@app.get("/api/fetch/{keyword}")
async def fetch_data_with_path(keyword: str = Path(..., description="Keyword for search")):
    return await fetch_data_internal(keyword=keyword, refresh=False)

@app.on_event("startup")
async def startup_event():
    global fetch_task

    async def periodic_fetch():
        global fetch_task
        while True:
            if fetch_task and not fetch_task.done():
                logging.info("等待当前任务完成")
                await fetch_task

            # 计算到当天午夜的时间
            now = datetime.now()
            tomorrow = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())

            # 随机生成一天中的一个时间点
            random_seconds = random.randint(0, 24 * 60 * 60)
            random_time = now + timedelta(seconds=random_seconds)

            # 如果生成的时间已经过去，则设置为明天的随机时间
            if random_time < now:
                random_time = tomorrow + timedelta(seconds=random_seconds)

            # 计算等待时间
            wait_time = (random_time - now).total_seconds()
            logging.info(f"下一次抓取将在 {random_time} 进行，等待 {wait_time} 秒")

            # 打印下一次抓取时间
            print(f"下一次抓取将在 {random_time} 进行，等待 {wait_time} 秒")

            await asyncio.sleep(wait_time)  # 等待随机时间

            fetch_task = asyncio.create_task(fetch_data_internal(refresh=True))
            await fetch_task

    asyncio.create_task(periodic_fetch())

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
