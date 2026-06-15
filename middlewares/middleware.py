from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import async_session_maker
from database import queries


class DatabaseMiddleware(BaseMiddleware):
    """Injects database session into every handler"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        async with async_session_maker() as session:
            data["session"] = session
            return await handler(event, data)


class ActiveUserMiddleware(BaseMiddleware):
    """Updates user last_active on each message"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, (Message, CallbackQuery)):
            user = event.from_user
            if user:
                session: AsyncSession = data.get("session")
                if session:
                    db_user = await queries.get_user(session, user.id)
                    if db_user:
                        await queries.update_last_active(session, user.id)
        return await handler(event, data)
