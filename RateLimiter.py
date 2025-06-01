import time
import redis
from fastapi import Request, HTTPException
from Features import log_features 

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Constants
USER_LIMIT = 5          # Max requests per user per time window
SERVER_BUCKET = 100     # Max requests the server can handle globally
TIME_WINDOW = 60        # Time window in seconds

def fixed_window_rate_limiter(request: Request):
    
    client_ip = request.client.host

    user_key = f"rate_limit:user:{client_ip}"
    server_key = "rate_limit:server"

    if not redis_client.exists(server_key):
        redis_client.set(server_key, SERVER_BUCKET, ex=TIME_WINDOW)

    server_count = redis_client.decr(server_key)
    if server_count < 0:
        redis_client.incr(server_key)
        raise HTTPException(status_code=429, detail="Server is overloaded. Try again later.")

    if not redis_client.exists(user_key):
        redis_client.set(user_key, USER_LIMIT, ex=TIME_WINDOW)

    user_count = redis_client.decr(user_key)
    if user_count < 0:
        redis_client.incr(user_key)
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

def sliding_window_rate_limiter(request: Request):
    current_time = int(time.time())
    client_ip = request.client.host

    server_key = "rate_limit:server"
    user_key = f"rate_limit:user:{client_ip}"

    # Check if server and user keys exist (server first)
    server_exists = redis_client.exists(server_key)
    user_exists = redis_client.exists(user_key)

    server_timestamps = []
    user_timestamps = []

    if server_exists:
        server_timestamps = redis_client.lrange(server_key, 0, -1)
        server_timestamps = [int(ts) for ts in server_timestamps if int(ts) > current_time - TIME_WINDOW]

    if user_exists:
        user_timestamps = redis_client.lrange(user_key, 0, -1)
        user_timestamps = [int(ts) for ts in user_timestamps if int(ts) > current_time - TIME_WINDOW]

    # Check rate limits (server first)
    if len(server_timestamps) >= SERVER_BUCKET:
        raise HTTPException(status_code=429, detail="Server overloaded. Try again later.")

    if len(user_timestamps) >= USER_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

    # Safely push new timestamp (server first, then user)
    pipe = redis_client.pipeline()

    pipe.lpush(server_key, current_time)
    if not server_exists:
        pipe.expire(server_key, TIME_WINDOW)   #setting expiration right after requested for first time

    pipe.lpush(user_key, current_time)
    if not user_exists:
        pipe.expire(user_key, TIME_WINDOW)

    pipe.execute()



# Constants
CAPACITY = 10       # Maximum tokens in the bucket
FILL_RATE = 5       # Tokens added per second

async def token_bucket_rate_limiter(request: Request):
    current_time = time.time()
    client_ip = request.client.host

    user_key = f"token_bucket:{client_ip}" 
    token_key = f"{user_key}:tokens"
    timestamp_key = f"{user_key}:timestamps"
    last_refill_key = f"{user_key}:last_refill_key"


    # Fetch existing tokens and last refill time
    tokens = redis_client.get(token_key)
    last_refill = redis_client.get(last_refill_key)

    tokens = float(tokens) if tokens else CAPACITY
    last_refill = float(last_refill) if last_refill else current_time


    # Refill tokens based on time passed (replace with any custom token refilling algorithm)
    elapsed = current_time - last_refill
    refill = elapsed * FILL_RATE
    tokens = min(CAPACITY, tokens + refill)

    # Update timestamp
    redis_client.set(last_refill_key, current_time)

    if tokens >= 1:
        tokens -= 1
        redis_client.set(token_key, tokens)

        redis_client.lpush(timestamp_key, current_time)
        redis_client.expire(timestamp_key, 10)  
    else:
        redis_client.set(token_key, tokens)
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    
    log_features(redis_client, user_key, client_ip)

