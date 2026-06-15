from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from config import MIN_WITHDRAW, ADMIN_ID
from database import queries
from keyboards import main_menu_keyboard, withdraw_confirm_keyboard, admin_withdrawal_keyboard
from states import WithdrawStates

router = Router()


@router.message(F.text == "💳 Mablag' yechish")
async def withdraw_handler(message: Message, session: AsyncSession, state: FSMContext):
    user = await queries.get_user(session, message.from_user.id)
    if not user:
        await message.answer("❌ Siz ro'yxatdan o'tmagansiz. /start bosing.")
        return

    if user.balance < MIN_WITHDRAW:
        await message.answer(
            f"❌ <b>Yechish uchun yetarli ball yo'q!</b>\n\n"
            f"💎 Joriy balansingiz: <b>{user.balance:,} ball</b>\n"
            f"📊 Minimal yechish: <b>{MIN_WITHDRAW:,} ball</b>\n\n"
            f"Hali <b>{MIN_WITHDRAW - user.balance:,} ball</b> yig'ishingiz kerak!",
            parse_mode="HTML"
        )
        return

    await message.answer(
        f"💳 <b>Mablag' yechish</b>\n\n"
        f"💎 Balans: <b>{user.balance:,} ball</b>\n"
        f"📊 Minimal: <b>{MIN_WITHDRAW:,} ball</b>\n\n"
        f"💳 Karta raqamingizni yuboring:\n"
        f"<i>(8 yoki 16 raqamli)</i>",
        parse_mode="HTML"
    )
    await state.set_state(WithdrawStates.waiting_card)


@router.message(WithdrawStates.waiting_card)
async def process_card_number(message: Message, state: FSMContext, session: AsyncSession):
    card = message.text.strip().replace(" ", "").replace("-", "")

    if not card.isdigit() or len(card) not in [8, 16]:
        await message.answer(
            "❌ Noto'g'ri karta raqami!\n"
            "Iltimos, 8 yoki 16 raqamli karta raqamini kiriting:"
        )
        return

    await state.update_data(card_number=card)

    user = await queries.get_user(session, message.from_user.id)
    await message.answer(
        f"✅ Karta: <code>{card}</code>\n\n"
        f"💰 Necha ball yechmoqchisiz?\n"
        f"<i>Maksimal: {user.balance:,} ball</i>",
        parse_mode="HTML"
    )
    await state.set_state(WithdrawStates.waiting_amount)


@router.message(WithdrawStates.waiting_amount)
async def process_withdraw_amount(message: Message, state: FSMContext, session: AsyncSession):
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Iltimos, to'g'ri raqam kiriting:")
        return

    user = await queries.get_user(session, message.from_user.id)

    if amount < MIN_WITHDRAW:
        await message.answer(
            f"❌ Minimal yechish miqdori: <b>{MIN_WITHDRAW:,} ball</b>",
            parse_mode="HTML"
        )
        return

    if amount > user.balance:
        await message.answer(
            f"❌ Balansda yetarli ball yo'q!\n"
            f"💎 Sizda: <b>{user.balance:,} ball</b>",
            parse_mode="HTML"
        )
        return

    data = await state.get_data()
    card = data["card_number"]

    await state.update_data(amount=amount)
    await state.set_state(WithdrawStates.confirm)

    await message.answer(
        f"📋 <b>Yechish so'rovi</b>\n\n"
        f"💳 Karta: <code>{card}</code>\n"
        f"💰 Miqdor: <b>{amount:,} ball</b>\n\n"
        f"Tasdiqlaysizmi?",
        reply_markup=withdraw_confirm_keyboard(amount),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("withdraw_confirm_"))
async def confirm_withdraw(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    card = data.get("card_number")
    amount = data.get("amount")

    if not card or not amount:
        await callback.answer("❌ Xato yuz berdi, qaytadan urinib ko'ring.", show_alert=True)
        await state.clear()
        return

    user = await queries.get_user(session, callback.from_user.id)
    if user.balance < amount:
        await callback.answer("❌ Yetarli ball yo'q!", show_alert=True)
        await state.clear()
        return

    withdrawal = await queries.create_withdrawal(session, user.telegram_id, amount, card)
    await state.clear()

    await callback.message.edit_text(
        f"✅ <b>So'rovingiz yuborildi!</b>\n\n"
        f"📋 So'rov #{withdrawal.id}\n"
        f"💳 Karta: <code>{card}</code>\n"
        f"💰 Miqdor: <b>{amount:,} ball</b>\n\n"
        f"⏳ Admin ko'rib chiqmoqda...\n"
        f"Natija sizga yuboriladi.",
        parse_mode="HTML"
    )

    # Notify admin
    try:
        await bot.send_message(
            ADMIN_ID,
            f"💸 <b>Yangi yechish so'rovi!</b>\n\n"
            f"📋 So'rov #{withdrawal.id}\n"
            f"👤 Foydalanuvchi: {user.full_name}\n"
            f"🆔 ID: <code>{user.telegram_id}</code>\n"
            f"💳 Karta: <code>{card}</code>\n"
            f"💰 Miqdor: <b>{amount:,} ball</b>",
            reply_markup=admin_withdrawal_keyboard(withdrawal.id),
            parse_mode="HTML"
        )
    except Exception:
        pass

    await callback.answer()


@router.callback_query(F.data == "withdraw_cancel")
async def cancel_withdraw(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    amount = data.get("amount")

    # Refund if already deducted - here we just clear state
    await state.clear()
    await callback.message.edit_text("❌ Yechish bekor qilindi.")
    await callback.answer()


# Admin approve/reject handlers
@router.callback_query(F.data.startswith("admin_approve_"))
async def admin_approve_withdrawal(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    from database.queries import is_admin
    if not await is_admin(session, callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    withdrawal_id = int(callback.data.split("_")[2])
    withdrawal = await queries.update_withdrawal_status(session, withdrawal_id, "approved", "Tasdiqlandi")

    if not withdrawal:
        await callback.answer("❌ So'rov topilmadi!", show_alert=True)
        return

    await callback.message.edit_text(
        callback.message.text + "\n\n✅ <b>TASDIQLANDI</b>",
        parse_mode="HTML"
    )

    try:
        await bot.send_message(
            withdrawal.user_id,
            f"✅ <b>To'lovingiz tasdiqlandi!</b>\n\n"
            f"📋 So'rov #{withdrawal.id}\n"
            f"💳 Karta: <code>{withdrawal.card_number}</code>\n"
            f"💰 Miqdor: <b>{withdrawal.amount:,} ball</b>\n\n"
            f"Pul tez orada kartangizga o'tkaziladi!",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await callback.answer("✅ Tasdiqlandi!")


@router.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject_withdrawal(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    from database.queries import is_admin
    if not await is_admin(session, callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    withdrawal_id = int(callback.data.split("_")[2])
    await state.update_data(reject_withdrawal_id=withdrawal_id)

    from states import AdminStates
    await state.set_state(AdminStates.waiting_reject_reason)
    await callback.message.answer("❌ Rad etish sababini yozing:")
    await callback.answer()


@router.message(WithdrawStates.confirm)
async def confirm_state_fallback(message: Message):
    await message.answer("Iltimos, yuqoridagi tugmalardan foydalaning.")
