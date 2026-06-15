from aiogram import Router, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import BOT_USERNAME, ADMIN_ID
from database import queries
from keyboards import main_menu_keyboard, subscription_check_keyboard
from utils.helpers import check_user_subscriptions, get_referral_link

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, bot: Bot, session: AsyncSession):
    user = message.from_user
    args = message.text.split()
    referrer_id = None

    if len(args) > 1:
        try:
            referrer_id = int(args[1])
            if referrer_id == user.id:
                referrer_id = None
        except ValueError:
            referrer_id = None

    # Check required channels
    channels = await queries.get_active_channels(session)
    if channels:
        not_subscribed = await check_user_subscriptions(bot, user.id, channels)
        if not_subscribed:
            await message.answer(
                "📢 <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:</b>\n\n"
                "Obuna bo'lgach, <b>✅ Tekshirish</b> tugmasini bosing!",
                reply_markup=subscription_check_keyboard(not_subscribed),
                parse_mode="HTML"
            )
            return

    # Check if user exists
    db_user = await queries.get_user(session, user.id)
    if not db_user:
        # Create new user
        db_user = await queries.create_user(
            session,
            telegram_id=user.id,
            full_name=user.full_name,
            username=user.username,
            referred_by=referrer_id
        )

        # Process referral
        if referrer_id:
            referrer = await queries.get_user(session, referrer_id)
            if referrer:
                result = await queries.process_referral(session, referrer_id, user.id)
                if result:
                    base_bonus, milestone_bonus = result
                    try:
                        bonus_text = (
                            f"🎉 <b>Yangi referal!</b>\n\n"
                            f"👤 {user.full_name} sizning havolangiz orqali ro'yxatdan o'tdi!\n"
                            f"💰 +{base_bonus} ball qo'shildi!"
                        )
                        if milestone_bonus:
                            bonus_text += f"\n🏆 Milestone bonus: +{milestone_bonus:,} ball!"
                        await bot.send_message(referrer_id, bonus_text, parse_mode="HTML")
                    except Exception:
                        pass

        await message.answer(
            f"🎉 <b>Xush kelibsiz, {user.first_name}!</b>\n\n"
            f"💎 Bonus Coin botiga xush kelibsiz!\n"
            f"Do'stlaringizni taklif qiling va bonus ball yig'ing!\n\n"
            f"🔗 Sizning havolangiz:\n"
            f"<code>{get_referral_link(BOT_USERNAME, user.id)}</code>",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"👋 <b>Qayta xush kelibsiz, {user.first_name}!</b>\n\n"
            f"💎 Ball: <b>{db_user.balance:,}</b>\n"
            f"👥 Referallar: <b>{db_user.referral_count}</b>",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
