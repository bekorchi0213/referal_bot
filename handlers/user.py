from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import BOT_USERNAME
from database import queries
from keyboards import main_menu_keyboard
from utils.helpers import (
    format_balance_text,
    format_referral_text,
    format_rating_text,
    get_referral_link
)

router = Router()


@router.message(F.text == "💰 Balansim")
async def balance_handler(message: Message, session: AsyncSession):
    user = await queries.get_user(session, message.from_user.id)
    if not user:
        await message.answer("❌ Siz ro'yxatdan o'tmagansiz. /start bosing.")
        return

    referral_link = get_referral_link(BOT_USERNAME, user.telegram_id)
    text = format_balance_text(user, referral_link)
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "👥 Do'st taklif qilish")
async def referral_handler(message: Message, session: AsyncSession):
    user = await queries.get_user(session, message.from_user.id)
    if not user:
        await message.answer("❌ Siz ro'yxatdan o'tmagansiz. /start bosing.")
        return

    referral_link = get_referral_link(BOT_USERNAME, user.telegram_id)

    # Total bonus from referrals
    referral_bonus = user.referral_count * 100
    text = format_referral_text(user, referral_link, referral_bonus)

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "🏆 Reyting")
async def rating_handler(message: Message, session: AsyncSession):
    top_users = await queries.get_top_users(session, limit=10)
    text = format_rating_text(top_users, message.from_user.id)
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "❓ Yordam")
async def help_handler(message: Message):
    text = (
        "❓ <b>Yordam</b>\n\n"
        "🤖 <b>BonusCoin Bot</b> - Do'stlarni taklif qilib ball yig'ing!\n\n"
        "📌 <b>Qoidalar:</b>\n"
        "├ Do'stingizni havolangiz orqali taklif qiling\n"
        "├ Har bir taklif uchun 100 ball oling\n"
        "├ Kunlik topshiriqlarni bajaring\n"
        "├ 10,000 ball yig'ib pul yechib oling\n\n"
        "💎 <b>Milestone bonuslari:</b>\n"
        "├ 10 referal → +1,000 ball\n"
        "├ 50 referal → +7,000 ball\n"
        "└ 100 referal → +20,000 ball\n\n"
        "📞 <b>Admin bilan bog'lanish:</b>\n"
        "└ @admin (yoki /admin)\n\n"
        "📋 <b>Shartlar:</b>\n"
        "├ Bir foydalanuvchi faqat bir marta referal sifatida hisoblanadi\n"
        "├ Minimal yechish: 10,000 ball\n"
        "└ To'lovlar 1-3 ish kuni ichida amalga oshiriladi"
    )
    await message.answer(text, parse_mode="HTML")
