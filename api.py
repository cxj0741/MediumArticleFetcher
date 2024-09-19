import httpx
import random
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Query, Path
from starlette.middleware.cors import CORSMiddleware
from fetch import fetch_main  # 假设 fetch_main 是你的抓取逻辑函数
import asyncio
import logging
from pydantic import BaseModel, HttpUrl 
from logger_config import logger
from mongodb_config import get_articles  # 新增：导入 get_articles 函数

from article_parser import fetch_article_content, parse_article_data #通过medium网址获取文章

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

            # 随机生成一天中的两个不同时间点
            random_seconds_1 = random.randint(0, 24 * 60 * 60)
            random_seconds_2 = random.randint(0, 24 * 60 * 60)
            while random_seconds_2 == random_seconds_1:
                random_seconds_2 = random.randint(0, 24 * 60 * 60)

            # 确定两个随机时间点
            random_time_1 = now + timedelta(seconds=random_seconds_1)
            random_time_2 = now + timedelta(seconds=random_seconds_2)

            # 如果生成的时间已经过去，则设置为明天的随机时间
            if random_time_1 < now:
                random_time_1 = tomorrow + timedelta(seconds=random_seconds_1)
            if random_time_2 < now:
                random_time_2 = tomorrow + timedelta(seconds=random_seconds_2)

            # 确保random_time_1是较早的时间点
            if random_time_1 > random_time_2:
                random_time_1, random_time_2 = random_time_2, random_time_1

            # 打印并等待第一个时间点
            wait_time_1 = (random_time_1 - now).total_seconds()
            logging.info(f"下一次抓取将在 {random_time_1} 进行，等待 {wait_time_1} 秒")
            print(f"下一次抓取将在 {random_time_1} 进行，等待 {wait_time_1} 秒")
            await asyncio.sleep(wait_time_1)

            # 执行第一次抓取任务
            fetch_task = asyncio.create_task(fetch_data_internal(refresh=True))
            await fetch_task

            # 打印并等待第二个时间点
            wait_time_2 = (random_time_2 - datetime.now()).total_seconds()
            logging.info(f"第二次抓取将在 {random_time_2} 进行，等待 {wait_time_2} 秒")
            print(f"第二次抓取将在 {random_time_2} 进行，等待 {wait_time_2} 秒")
            await asyncio.sleep(wait_time_2)

            # 执行第二次抓取任务
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

@app.get("/api/articles")
async def api_get_articles(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query("", max_length=100)
):
    """
    获取文章数据的 API 接口，支持分页和搜索
    """
    logger.info(f"API request received: page={page}, limit={limit}, search='{search}'")
    result = get_articles(page, limit, search)
    logger.info(f"API response: {result}")
    return result

class UrlInput(BaseModel):
    url: HttpUrl

@app.post("/api/parse_article")
async def parse_article(url_input: UrlInput):
    """
    解析给定URL的文章内容
    """
    url = str(url_input.url)
    async with httpx.AsyncClient() as client:
        soup = await fetch_article_content(url, client=client)
        if soup:
            article_data = parse_article_data(soup)
            return article_data
        else:
            raise HTTPException(status_code=404, detail="无法获取文章内容")


@app.get("/api/parse_article")
async def parse_article(url: HttpUrl = Query(..., description="Article URL to parse")):
    async with httpx.AsyncClient() as client:
        soup = await fetch_article_content(str(url), client=client)
        if soup:
            article_data = parse_article_data(soup)
            return article_data
        else:
            raise HTTPException(status_code=404, detail="无法获取文章内容")

if __name__ == '__main__':
    import uvicorn

    logger.info("开始记录日志")
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
