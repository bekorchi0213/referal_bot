from aiogram import Bot
from typing import List, Optional
from database.models import Channel

NOT_SUBSCRIBED_STATUSES = ("left", "kicked", "restricted")


async def check_user_subscriptions(bot: Bot, user_id: int, channels: List[Channel]) -> List[Channel]:
    """Returns list of channels user is NOT subscribed to"""
    not_subscribed = []
    for channel in channels:
        try:
            channel_id = channel.channel_id.strip()
            if channel_id.lstrip("-").isdigit():
                channel_id = int(channel_id)
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status in ("left", "kicked", "banned"):
                not_subscribed.append(channel)
        except Exception as e:
            print(f"Kanal xato [{channel.channel_id}]: {e}")
            not_subscribed.append(channel)
    return not_subscribed

def format_balance_text(user, referral_link: str) -> str:
    return (
        f"💰 <b>Balansim</b>\n\n"
        f"👤 ID: <code>{user.telegram_id}</code>\n"
        f"💎 Ball: <b>{user.balance:,}</b>\n"
        f"👥 Referallar: <b>{user.referral_count}</b>\n\n"
        f"🔗 Havola: <code>{referral_link}</code>"
    )


def format_referral_text(user, referral_link: str, total_bonus: int) -> str:
    return (
        f"👥 <b>Do'st taklif qilish</b>\n\n"
        f"🔗 Sizning havolangiz:\n"
        f"<code>{referral_link}</code>\n\n"
        f"📊 Taklif qilinganlar: <b>{user.referral_count}</b>\n"
        f"💰 Olingan bonuslar: <b>{total_bonus:,}</b> ball\n\n"
        f"🎯 <b>Bonus tizimi:</b>\n"
        f"├ Har bir referal: +100 ball\n"
        f"├ 10 referal: +1,000 ball\n"
        f"├ 50 referal: +7,000 ball\n"
        f"└ 100 referal: +20,000 ball"
    )


def format_rating_text(users: list, current_user_id: int) -> str:
    text = "🏆 <b>Top 10 Reyting</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, user in enumerate(users, 1):
        medal = medals[i - 1] if i <= 3 else f"{i}."
        you = " 👈" if user.telegram_id == current_user_id else ""
        name = user.full_name[:20]
        text += f"{medal} <b>{name}</b>{you}\n"
        text += f"   💎 {user.balance:,} ball | 👥 {user.referral_count} referal\n\n"
    return text


def format_task_type(task_type: str) -> str:
    types = {
        "simple": "🟢 Oddiy (50-100 ball)",
        "complex": "🔴 Murakkab (200-300 ball)",
        "weekly": "⭐ Haftalik Super Savol (1000 ball)"
    }
    return types.get(task_type, "📋 Topshiriq")


def get_referral_link(bot_username: str, user_id: int) -> str:
    return f"https://t.me/{bot_username}?start={user_id}"
