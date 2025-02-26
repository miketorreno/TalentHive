import os
import json
from datetime import timedelta
import redis


class RedisCache:
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_password = os.getenv("REDIS_PASS", None)

    def __init__(self):
        self.r = redis.StrictRedis(
            host=self.redis_host,
            port=6379,
            password=self.redis_password,
            decode_responses=True,
        )

    async def get_job(self, job_id: int):
        """
        Retrieves a job from the Redis cache.

        Args:
            job_id (int): The ID of the job to retrieve.

        Returns:
            dict or None: The job's details if it exists in the cache, None otherwise.
        """

        cached = self.r.get(f"job:{job_id}")
        if cached:
            return json.loads(cached)
        return None

    async def set_job(self, job_id: int, data: dict, ttl: int = 3600):
        """
        Stores a job in the Redis cache.

        Args:
            job_id (int): The ID of the job to store.
            data (dict): The job's details to store.
            ttl (int, optional): The number of seconds to store the job in the cache. Defaults to 3600.
        """

        self.r.setex(f"job:{job_id}", timedelta(seconds=ttl), json.dumps(data))

    async def invalidate_job(self, job_id: int):
        """
        Invalidates a job from the Redis cache.

        Args:
            job_id (int): The ID of the job to invalidate.
        """

        self.r.delete(f"job:{job_id}")


# Initialize cache
cache = RedisCache()
