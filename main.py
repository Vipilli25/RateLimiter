from fastapi import FastAPI, Depends, HTTPException, Request
import requests, uvicorn
from dotenv import load_dotenv
import os

from RateLimiter import token_bucket_rate_limiter

load_dotenv()

app = FastAPI()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENWEATHER_URL = os.getenv("OPENWEATHER_URL")

@app.get("/weather")
async def get_weather(city: str, request: Request, _: None = Depends(token_bucket_rate_limiter)):
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }
    
    response = requests.get(OPENWEATHER_URL, params=params)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return response.json()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
