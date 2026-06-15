from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import select, func, update, delete, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from config import REFERRAL_BONUS, REFERRAL_MILESTONES
from database.models import (
    User, Referral, Task, TaskCompletion,
    Withdrawal, Channel, Admin, PromoCode, PromoUsage
)


# ===================== USER QUERIES =====================

async def get_user(session: AsyncSession, telegram_id: int) -> Optional[User]:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    telegram_id: int,
    full_name: str,
    username: Optional[str] = None,
    referred_by: Optional[int] = None
) -> User:
    existing = await get_user(session, telegram_id)
    if existing:
        return existing
    try:
        user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
            referred_by=referred_by
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    except Exception:
        await session.rollback()
        return await get_user(session, telegram_id)


async def update_user_balance(session: AsyncSession, telegram_id: int, amount: int):
    await session.execute(
        update(User)
        .where(User.telegram_id == telegram_id)
        .values(balance=User.balance + amount, last_active=datetime.utcnow())
    )
    await session.commit()


async def update_last_active(session: AsyncSession, telegram_id: int):
    await session.execute(
        update(User)
        .where(User.telegram_id == telegram_id)
        .values(last_active=datetime.utcnow())
    )
    await session.commit()


async def get_all_users(session: AsyncSession) -> List[User]:
    result = await session.execute(select(User).where(User.is_active == True))
    return result.scalars().all()


async def get_top_users(session: AsyncSession, limit: int = 10) -> List[User]:
    result = await session.execute(
        select(User).order_by(desc(User.balance)).limit(limit)
    )
    return result.scalars().all()


async def get_users_count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count(User.id)))
    return result.scalar()


async def get_today_users_count(session: AsyncSession) -> int:
    today = datetime.utcnow().date()
    result = await session.execute(
        select(func.count(User.id)).where(
            func.date(User.created_at) == today
        )
    )
    return result.scalar()


async def get_active_users_count(session: AsyncSession) -> int:
    week_ago = datetime.utcnow() - timedelta(days=7)
    result = await session.execute(
        select(func.count(User.id)).where(User.last_active >= week_ago)
    )
    return result.scalar()


# ===================== REFERRAL QUERIES =====================

async def process_referral(session: AsyncSession, referrer_id: int, referred_id: int):
    # Check if referral already exists
    existing = await session.execute(
        select(Referral).where(
            and_(
                Referral.referrer_id == referrer_id,
                Referral.referred_id == referred_id
            )
        )
    )
    if existing.scalar_one_or_none():
        return None

    # Give base referral bonus
    bonus = REFERRAL_BONUS
    referral = Referral(
        referrer_id=referrer_id,
        referred_id=referred_id,
        bonus_given=bonus
    )
    session.add(referral)

    # Update referrer balance and count
    await session.execute(
        update(User)
        .where(User.telegram_id == referrer_id)
        .values(
            balance=User.balance + bonus,
            referral_count=User.referral_count + 1
        )
    )

    await session.commit()

    # Check milestone bonuses
    referrer = await get_user(session, referrer_id)
    milestone_bonus = REFERRAL_MILESTONES.get(referrer.referral_count, 0)
    if milestone_bonus:
        await update_user_balance(session, referrer_id, milestone_bonus)
        return bonus, milestone_bonus

    return bonus, 0


async def get_referral_count(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        select(func.count(Referral.id)).where(Referral.referrer_id == user_id)
    )
    return result.scalar()


async def get_total_referrals(session: AsyncSession) -> int:
    result = await session.execute(select(func.count(Referral.id)))
    return result.scalar()


# ===================== TASK QUERIES =====================

async def get_active_tasks(session: AsyncSession) -> List[Task]:
    result = await session.execute(
        select(Task).where(Task.is_active == True)
    )
    return result.scalars().all()


async def get_task(session: AsyncSession, task_id: int) -> Optional[Task]:
    result = await session.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def create_task(
    session: AsyncSession,
    title: str,
    description: str,
    reward: int,
    task_type: str = "simple"
) -> Task:
    task = Task(
        title=title,
        description=description,
        reward=reward,
        task_type=task_type
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def delete_task(session: AsyncSession, task_id: int):
    await session.execute(delete(Task).where(Task.id == task_id))
    await session.commit()


async def toggle_task(session: AsyncSession, task_id: int):
    task = await get_task(session, task_id)
    if task:
        await session.execute(
            update(Task).where(Task.id == task_id).values(is_active=not task.is_active)
        )
        await session.commit()


async def is_task_completed(session: AsyncSession, user_id: int, task_id: int) -> bool:
    result = await session.execute(
        select(TaskCompletion).where(
            and_(
                TaskCompletion.user_id == user_id,
                TaskCompletion.task_id == task_id
            )
        )
    )
    return result.scalar_one_or_none() is not None


async def complete_task(session: AsyncSession, user_id: int, task_id: int) -> int:
    task = await get_task(session, task_id)
    if not task:
        return 0

    already = await is_task_completed(session, user_id, task_id)
    if already:
        return 0

    completion = TaskCompletion(user_id=user_id, task_id=task_id)
    session.add(completion)
    await update_user_balance(session, user_id, task.reward)
    await session.commit()
    return task.reward


# ===================== WITHDRAWAL QUERIES =====================

async def create_withdrawal(
    session: AsyncSession,
    user_id: int,
    amount: int,
    card_number: str
) -> Withdrawal:
    # Deduct from balance first
    await session.execute(
        update(User)
        .where(User.telegram_id == user_id)
        .values(balance=User.balance - amount)
    )
    withdrawal = Withdrawal(
        user_id=user_id,
        amount=amount,
        card_number=card_number,
        status="pending"
    )
    session.add(withdrawal)
    await session.commit()
    await session.refresh(withdrawal)
    return withdrawal


async def get_pending_withdrawals(session: AsyncSession) -> List[Withdrawal]:
    result = await session.execute(
        select(Withdrawal).where(Withdrawal.status == "pending").order_by(Withdrawal.created_at)
    )
    return result.scalars().all()


async def get_withdrawal(session: AsyncSession, withdrawal_id: int) -> Optional[Withdrawal]:
    result = await session.execute(select(Withdrawal).where(Withdrawal.id == withdrawal_id))
    return result.scalar_one_or_none()


async def update_withdrawal_status(
    session: AsyncSession,
    withdrawal_id: int,
    status: str,
    admin_note: str = ""
):
    withdrawal = await get_withdrawal(session, withdrawal_id)
    if not withdrawal:
        return None

    if status == "rejected":
        # Refund balance
        await update_user_balance(session, withdrawal.user_id, withdrawal.amount)

    await session.execute(
        update(Withdrawal)
        .where(Withdrawal.id == withdrawal_id)
        .values(status=status, admin_note=admin_note, updated_at=datetime.utcnow())
    )
    await session.commit()
    return withdrawal


async def get_total_withdrawals(session: AsyncSession) -> int:
    result = await session.execute(
        select(func.sum(Withdrawal.amount)).where(Withdrawal.status == "approved")
    )
    return result.scalar() or 0


# ===================== CHANNEL QUERIES =====================

async def get_active_channels(session: AsyncSession) -> List[Channel]:
    result = await session.execute(
        select(Channel).where(Channel.is_active == True)
    )
    return result.scalars().all()


async def add_channel(
    session: AsyncSession,
    channel_id: str,
    channel_name: str,
    channel_link: str
) -> Channel:
    channel = Channel(
        channel_id=channel_id,
        channel_name=channel_name,
        channel_link=channel_link
    )
    session.add(channel)
    await session.commit()
    await session.refresh(channel)
    return channel


async def remove_channel(session: AsyncSession, channel_id: int):
    await session.execute(delete(Channel).where(Channel.id == channel_id))
    await session.commit()


async def get_channel(session: AsyncSession, channel_db_id: int) -> Optional[Channel]:
    result = await session.execute(select(Channel).where(Channel.id == channel_db_id))
    return result.scalar_one_or_none()


# ===================== ADMIN QUERIES =====================

async def is_admin(session: AsyncSession, telegram_id: int) -> bool:
    from config import ADMIN_IDS
    if telegram_id in ADMIN_IDS:
        return True
    result = await session.execute(
        select(Admin).where(Admin.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none() is not None


# ===================== PROMO QUERIES =====================

async def get_promo(session: AsyncSession, code: str) -> Optional[PromoCode]:
    result = await session.execute(
        select(PromoCode).where(
            and_(
                PromoCode.code == code,
                PromoCode.is_active == True
            )
        )
    )
    return result.scalar_one_or_none()


async def use_promo(session: AsyncSession, user_id: int, code: str) -> tuple:
    promo = await get_promo(session, code)
    if not promo:
        return False, "Promo kod topilmadi yoki faol emas!"

    if promo.expires_at and promo.expires_at < datetime.utcnow():
        return False, "Promo kodning muddati tugagan!"

    if promo.used_count >= promo.max_uses:
        return False, "Promo kod limitga yetdi!"

    # Check if user already used this promo
    existing = await session.execute(
        select(PromoUsage).where(
            and_(
                PromoUsage.user_id == user_id,
                PromoUsage.promo_id == promo.id
            )
        )
    )
    if existing.scalar_one_or_none():
        return False, "Siz bu promo kodni allaqachon ishlatgansiz!"

    usage = PromoUsage(user_id=user_id, promo_id=promo.id)
    session.add(usage)
    await session.execute(
        update(PromoCode).where(PromoCode.id == promo.id).values(used_count=PromoCode.used_count + 1)
    )
    await update_user_balance(session, user_id, promo.reward)
    await session.commit()
    return True, promo.reward


async def create_promo(
    session: AsyncSession,
    code: str,
    reward: int,
    max_uses: int = 1,
    expires_at: Optional[datetime] = None
) -> PromoCode:
    promo = PromoCode(
        code=code,
        reward=reward,
        max_uses=max_uses,
        expires_at=expires_at
    )
    session.add(promo)
    await session.commit()
    await session.refresh(promo)
    return promo


async def get_all_promos(session: AsyncSession) -> List[PromoCode]:
    result = await session.execute(select(PromoCode).order_by(desc(PromoCode.created_at)))
    return result.scalars().all()
