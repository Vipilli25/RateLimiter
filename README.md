# RateLimiter

A FastAPI-based web service demonstrating multiple rate limiting algorithms — fixed window, sliding window, and token bucket — using Redis for state management.  
The API proxies requests to the OpenWeather service, enforcing rate limits per user IP and globally to prevent abuse.

---

## Features

- **FastAPI** backend exposing `/weather` endpoint.
- **Three rate limiting algorithms** implemented with Redis:
  - Fixed Window
  - Sliding Window
  - Token Bucket (default limiter)
- Rate limits apply per user IP and globally for server protection.
- Token bucket fill rate dynamically adjusted using extracted usage features.
- Logs detailed request statistics and heuristics for rate limiting.
- Environment variable support via `.env` for API keys and configuration.
- Simple integration with OpenWeather API to fetch weather data.

---

## Architecture

- `main.py` (or your main FastAPI app file):
  - Exposes `/weather?city=<city_name>` endpoint.
  - Uses a token bucket rate limiter dependency for requests.
- `RateLimiter/token_bucket_rate_limiter.py`:
  - Implements token bucket algorithm with Redis.
- `Features/log_features.py`:
  - Extracts request timing features and heuristically adjusts rate limiter parameters.
- Redis stores counters, timestamps, and tokens per user and globally.

---

## Setup Instructions

### Prerequisites

- Python 3.8+
- Redis server running locally on default port (`6379`)
- OpenWeather API key ([Get one here](https://openweathermap.org/api))
- `pip` packages:
  - fastapi
  - uvicorn
  - requests
  - redis
  - python-dotenv

### Installation

1. Clone the repo:

   ```bash
   git clone https://github.com/Vipilli25/RateLimiter.git
   cd RateLimiter

2. Setup Environment Variables

Create a `.env` file in the root of your project directory and add the following environment variables:

    ```env
    OPENWEATHER_API_KEY=your_openweather_api_key_here
    OPENWEATHER_URL=https://api.openweathermap.org/data/2.5/weather
    REDIS_HOST=localhost
    REDIS_PORT=6379

3. Run the application  
    Ensure Redis is running and run FastAPI server:
      ```bash
      uvicorn main:app --reload
      
