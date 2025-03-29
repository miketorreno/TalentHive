# core/dependencies.py
from dependency_injector import containers, providers
from redis.asyncio import Redis
from core.database.session import AsyncSessionLocal


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    db_session = providers.Resource(AsyncSessionLocal)

    redis_client = providers.Singleton(Redis.from_url, url=config.redis_url)

    # user_service = providers.Factory(UserService, session=db_session)
