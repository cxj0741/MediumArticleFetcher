from fastapi import FastAPI, HTTPException
from scraper import run_scraper

app = FastAPI()

@app.get("/refresh")
def refresh():
    try:
        run_scraper()
        return {"status": "success", "message": "Refreshed and fetched the latest 100 articles."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
def search(keyword: str):
    if not keyword:
        raise HTTPException(status_code=400, detail="Keyword is required")
    try:
        run_scraper(keyword)
        return {"status": "success", "message": f"Fetched the latest 100 articles for keyword: {keyword}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
