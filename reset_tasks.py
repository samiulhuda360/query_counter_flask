import redis

# Connect to Redis
r = redis.Redis(host='redis', port=6379)

# Clear all keys (task data) from Redis
r.flushall()

print("Task data reset successfully.")