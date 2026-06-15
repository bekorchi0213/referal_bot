from handlers.start import router as start_router
from handlers.subscription import router as subscription_router
from handlers.user import router as user_router
from handlers.tasks import router as tasks_router
from handlers.bonuses import router as bonuses_router
from handlers.withdraw import router as withdraw_router
from handlers.admin import router as admin_router

__all__ = [
    "start_router",
    "subscription_router",
    "user_router",
    "tasks_router",
    "bonuses_router",
    "withdraw_router",
    "admin_router",
]
