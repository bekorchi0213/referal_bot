from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database import queries
from keyboards import cancel_keyboard, main_menu_keyboard

router = Router()


@router.message(F.text == "🎁 Bonuslar")
async def bonuses_handler(message: Message, session: AsyncSession):
    user = await queries.get_user(session, message.from_user.id)
    if not user:
        await message.answer("❌ Siz ro'yxatdan o'tmagansiz. /start bosing.")
        return

    text = (
        f"🎁 <b>Bonuslar</b>\n\n"
        f"💎 Joriy balansingiz: <b>{user.balance:,} ball</b>\n\n"
        f"🎟 <b>Promo kod aktivlashtirish</b>\n"
        f"Promo kodingizni yuboring:\n\n"
        f"Misol: <code>BONUS2024</code>"
    )
    await message.answer(
        text,
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("❌ Bekor qilindi")


@router.message(F.text & ~F.text.startswith("/"))
async def promo_code_handler(message: Message, session: AsyncSession, state: FSMContext):
    current_state = await state.get_state()
    # Only handle promo code if no active FSM state and message looks like a promo code
    if current_state is not None:
        return

    text = message.text.strip().upper()

    # Check if text might be a promo code (no spaces, alphanumeric)
    if len(text) < 4 or len(text) > 20 or not text.replace("_", "").replace("-", "").isalnum():
        return

    # Try to use as promo code
    success, result = await queries.use_promo(session, message.from_user.id, text)
    if success:
        await message.answer(
            f"✅ <b>Promo kod muvaffaqiyatli aktivlashtirildi!</b>\n\n"
            f"💰 +{result:,} ball qo'shildi!\n\n"
            f"Balansingiz: <b>{(await queries.get_user(session, message.from_user.id)).balance:,} ball</b>",
            parse_mode="HTML"
        )
    else:
        pass  # Not a promo code, ignore silently
