from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import BOT_USERNAME
from database import queries
from keyboards import main_menu_keyboard, subscription_check_keyboard
from utils.helpers import check_user_subscriptions, get_referral_link

router = Router()


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, bot: Bot, session: AsyncSession):
    user = callback.from_user
    channels = await queries.get_active_channels(session)

    not_subscribed = await check_user_subscriptions(bot, user.id, channels)

    if not_subscribed:
        await callback.answer("❌ Hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
        await callback.message.edit_reply_markup(
            reply_markup=subscription_check_keyboard(not_subscribed)
        )
        return

    # User is subscribed - register if new
    db_user = await queries.get_user(session, user.id)
    if not db_user:
        db_user = await queries.create_user(
            session,
            telegram_id=user.id,
            full_name=user.full_name,
            username=user.username
        )

    await callback.message.delete()
    await callback.message.answer(
        f"✅ <b>Obuna tasdiqlandi!</b>\n\n"
        f"Xush kelibsiz, {user.first_name}! 🎉\n"
        f"💎 Ball: <b>{db_user.balance:,}</b>\n\n"
        f"🔗 Sizning havolangiz:\n"
        f"<code>{get_referral_link(BOT_USERNAME, user.id)}</code>",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
