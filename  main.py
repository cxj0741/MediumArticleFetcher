import uvicorn

if __name__ == "__main__":
    # reload=True：启用自动重载功能。在代码更改时，uvicorn 会自动重新启动服务器，
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
