from core.database.models import User


class UserService:
    def __init__(self, session):
        self.session = session

    async def get_user(self, telegram_id: int) -> User:
        user = await self.session.get(User, telegram_id)

        return user

    async def create_user(self, telegram_id: int, role: int) -> User:
        user = User(telegram_id=telegram_id, role=role)
        self.session.add(user)
        await self.session.commit()

        return user

    # async def update_profile(self, user: User, data: UserCreate):
    #     for key, value in data.dict().items():
    #         setattr(user, key, value)
    #     await self.session.commit()
    #     return user
