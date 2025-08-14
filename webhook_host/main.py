# webhook_host/main.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
async def root():
    return JSONResponse(content={"message": "LINE Webhook FastAPI is running!"})
