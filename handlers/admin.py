from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from config import ADMIN_ID
from database import queries
from keyboards import (
    admin_menu_keyboard,
    main_menu_keyboard,
    admin_channels_keyboard,
    admin_tasks_keyboard,
    admin_task_manage_keyboard,
    pending_withdrawals_keyboard
)
from states import AdminStates

router = Router()


async def check_admin(session: AsyncSession, user_id: int) -> bool:
    return await queries.is_admin(session, user_id)


@router.message(Command("admin"))
async def admin_panel(message: Message, session: AsyncSession):
    if not await check_admin(session, message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q!")
        return

    total_users = await queries.get_users_count(session)
    today_users = await queries.get_today_users_count(session)
    active_users = await queries.get_active_users_count(session)
    total_refs = await queries.get_total_referrals(session)
    total_withdraw = await queries.get_total_withdrawals(session)

    text = (
        f"🔧 <b>Admin Panel</b>\n\n"
        f"📊 <b>Statistika:</b>\n"
        f"├ Jami foydalanuvchilar: <b>{total_users:,}</b>\n"
        f"├ Bugungi yangilar: <b>{today_users:,}</b>\n"
        f"├ Faol (7 kun): <b>{active_users:,}</b>\n"
        f"├ Jami referallar: <b>{total_refs:,}</b>\n"
        f"└ Tasdiqlangan to'lovlar: <b>{total_withdraw:,} ball</b>"
    )
    await message.answer(text, reply_markup=admin_menu_keyboard(), parse_mode="HTML")


@router.message(F.text == "📊 Statistika")
async def admin_stats(message: Message, session: AsyncSession):
    if not await check_admin(session, message.from_user.id):
        return

    total_users = await queries.get_users_count(session)
    today_users = await queries.get_today_users_count(session)
    active_users = await queries.get_active_users_count(session)
    total_refs = await queries.get_total_referrals(session)
    total_withdraw = await queries.get_total_withdrawals(session)
    pending = await queries.get_pending_withdrawals(session)

    text = (
        f"📊 <b>Batafsil statistika</b>\n\n"
        f"👥 Foydalanuvchilar:\n"
        f"├ Jami: <b>{total_users:,}</b>\n"
        f"├ Bugun: <b>{today_users:,}</b>\n"
        f"└ Faol (7 kun): <b>{active_users:,}</b>\n\n"
        f"🔗 Referallar:\n"
        f"└ Jami: <b>{total_refs:,}</b>\n\n"
        f"💸 To'lovlar:\n"
        f"├ Tasdiqlangan: <b>{total_withdraw:,} ball</b>\n"
        f"└ Kutilmoqda: <b>{len(pending)}</b> ta so'rov"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "👤 Foydalanuvchilar")
async def admin_users(message: Message, session: AsyncSession):
    if not await check_admin(session, message.from_user.id):
        return

    top = await queries.get_top_users(session, 5)
    text = "👤 <b>Top 5 foydalanuvchi:</b>\n\n"
    for i, u in enumerate(top, 1):
        text += f"{i}. {u.full_name} — {u.balance:,} ball | {u.referral_count} ref\n"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "🔗 Referallar")
async def admin_referrals(message: Message, session: AsyncSession):
    if not await check_admin(session, message.from_user.id):
        return

    total = await queries.get_total_referrals(session)
    top = await queries.get_top_users(session, 5)

    text = (
        f"🔗 <b>Referallar statistikasi</b>\n\n"
        f"📊 Jami referallar: <b>{total:,}</b>\n\n"
        f"🏆 <b>Top 5 refererlar:</b>\n"
    )
    for i, u in enumerate(top, 1):
        text += f"{i}. {u.full_name} — {u.referral_count} referal\n"

    await message.answer(text, parse_mode="HTML")


# ==================== PAYMENTS ====================

@router.message(F.text == "💸 To'lovlar")
async def admin_payments(message: Message, session: AsyncSession):
    if not await check_admin(session, message.from_user.id):
        return

    pending = await queries.get_pending_withdrawals(session)
    if not pending:
        await message.answer("✅ Kutilayotgan to'lov so'rovlari yo'q!")
        return

    await message.answer(
        f"💸 <b>Kutilayotgan to'lovlar: {len(pending)} ta</b>\n\nSo'rovni tanlang:",
        reply_markup=pending_withdrawals_keyboard(pending),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("view_withdrawal_"))
async def view_withdrawal(callback: CallbackQuery, session: AsyncSession):
    if not await check_admin(session, callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!")
        return

    withdrawal_id = int(callback.data.split("_")[2])
    w = await queries.get_withdrawal(session, withdrawal_id)
    if not w:
        await callback.answer("❌ Topilmadi!", show_alert=True)
        return

    user = await queries.get_user(session, w.user_id)
    from keyboards import admin_withdrawal_keyboard
    sana = w.created_at.strftime("%d.%m.%Y %H:%M")
    nomi = user.full_name if user else "Noma'lum"
    await callback.message.answer(
        f"💸 <b>So'rov #{w.id}</b>\n\n"
        f"👤 Foydalanuvchi: {nomi}\n"
        f"🆔 ID: <code>{w.user_id}</code>\n"
        f"💳 Karta: <code>{w.card_number}</code>\n"
        f"💰 Miqdor: <b>{w.amount:,} ball</b>\n"
        f"📅 Sana: {sana}",
        reply_markup=admin_withdrawal_keyboard(w.id),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== CHANNELS ====================

@router.message(F.text == "📢 Kanallar")
async def admin_channels(message: Message, session: AsyncSession):
    if not await check_admin(session, message.from_user.id):
        return

    channels = await queries.get_active_channels(session)
    text = f"📢 <b>Majburiy kanallar ({len(channels)} ta)</b>\n\nQo'shish yoki o'chirish:"
    await message.answer(
        text,
        reply_markup=admin_channels_keyboard(channels),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "add_channel")
async def add_channel_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await check_admin(session, callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!")
        return
    await state.set_state(AdminStates.waiting_channel_id)
    await callback.message.answer(
        "📢 Kanal ID ni yuboring\n"
        "Misol: <code>-1001234567890</code> yoki <code>@kanalUsername</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminStates.waiting_channel_id)
async def process_channel_id(message: Message, state: FSMContext):
    await state.update_data(channel_id=message.text.strip())
    await state.set_state(AdminStates.waiting_channel_name)
    await message.answer("📝 Kanal nomini yuboring:")


@router.message(AdminStates.waiting_channel_name)
async def process_channel_name(message: Message, state: FSMContext):
    await state.update_data(channel_name=message.text.strip())
    await state.set_state(AdminStates.waiting_channel_link)
    await message.answer("🔗 Kanal havolasini yuboring (t.me/...):")


@router.message(AdminStates.waiting_channel_link)
async def process_channel_link(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    link = message.text.strip()
    if not link.startswith("http"):
        link = f"https://{link}"

    channel = await queries.add_channel(
        session,
        channel_id=data["channel_id"],
        channel_name=data["channel_name"],
        channel_link=link
    )
    await state.clear()
    await message.answer(
        f"✅ Kanal qo'shildi!\n\n"
        f"📢 {channel.channel_name}\n"
        f"🔗 {channel.channel_link}",
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("del_channel_"))
async def delete_channel(callback: CallbackQuery, session: AsyncSession):
    if not await check_admin(session, callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!")
        return

    channel_id = int(callback.data.split("_")[2])
    channel = await queries.get_channel(session, channel_id)
    if channel:
        await queries.remove_channel(session, channel_id)
        await callback.answer(f"✅ {channel.channel_name} o'chirildi!")
    else:
        await callback.answer("❌ Kanal topilmadi!")

    channels = await queries.get_active_channels(session)
    await callback.message.edit_reply_markup(
        reply_markup=admin_channels_keyboard(channels)
    )


# ==================== BROADCAST ====================

@router.message(F.text == "📣 Xabar yuborish")
async def broadcast_start(message: Message, state: FSMContext, session: AsyncSession):
    if not await check_admin(session, message.from_user.id):
        return
    await state.set_state(AdminStates.waiting_broadcast)
    await message.answer(
        "📣 Barcha foydalanuvchilarga yuboriladigan xabarni yozing:\n"
        "<i>(Matn, rasm, video qabul qilinadi)</i>",
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_broadcast)
async def process_broadcast(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    await state.clear()
    users = await queries.get_all_users(session)
    sent = 0
    failed = 0

    await message.answer(f"⏳ {len(users)} ta foydalanuvchiga yuborilmoqda...")

    for user in users:
        try:
            await message.copy_to(user.telegram_id)
            sent += 1
        except Exception:
            failed += 1

    await message.answer(
        f"✅ <b>Xabar yuborildi!</b>\n\n"
        f"✅ Muvaffaqiyatli: <b>{sent}</b>\n"
        f"❌ Xato: <b>{failed}</b>",
        parse_mode="HTML"
    )


# ==================== TASKS ====================

@router.message(F.text == "📝 Topshiriqlar")
async def admin_tasks(message: Message, session: AsyncSession):
    if not await check_admin(session, message.from_user.id):
        return

    tasks = await queries.get_active_tasks(session)
    await message.answer(
        f"📝 <b>Topshiriqlar ({len(tasks)} ta)</b>",
        reply_markup=admin_tasks_keyboard(tasks),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "add_task")
async def add_task_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await check_admin(session, callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!")
        return
    await state.set_state(AdminStates.waiting_task_title)
    await callback.message.answer("📝 Topshiriq nomini yuboring:")
    await callback.answer()


@router.message(AdminStates.waiting_task_title)
async def process_task_title(message: Message, state: FSMContext):
    await state.update_data(task_title=message.text.strip())
    await state.set_state(AdminStates.waiting_task_description)
    await message.answer("📝 Topshiriq tavsifini yuboring:")


@router.message(AdminStates.waiting_task_description)
async def process_task_description(message: Message, state: FSMContext):
    await state.update_data(task_description=message.text.strip())
    await state.set_state(AdminStates.waiting_task_reward)
    await message.answer(
        "💰 Mukofot miqdorini yuboring (ball):\n"
        "<i>Oddiy: 50-100 | Murakkab: 200-300 | Haftalik: 1000</i>",
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_task_reward)
async def process_task_reward(message: Message, state: FSMContext):
    try:
        reward = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Iltimos, raqam kiriting!")
        return
    await state.update_data(task_reward=reward)
    await state.set_state(AdminStates.waiting_task_type)
    await message.answer(
        "📊 Topshiriq turini tanlang:\n\n"
        "1 - 🟢 Oddiy (simple)\n"
        "2 - 🔴 Murakkab (complex)\n"
        "3 - ⭐ Haftalik super (weekly)"
    )


@router.message(AdminStates.waiting_task_type)
async def process_task_type(message: Message, state: FSMContext, session: AsyncSession):
    types = {"1": "simple", "2": "complex", "3": "weekly"}
    task_type = types.get(message.text.strip(), "simple")

    data = await state.get_data()
    task = await queries.create_task(
        session,
        title=data["task_title"],
        description=data["task_description"],
        reward=data["task_reward"],
        task_type=task_type
    )
    await state.clear()

    type_names = {"simple": "🟢 Oddiy", "complex": "🔴 Murakkab", "weekly": "⭐ Haftalik"}
    await message.answer(
        f"✅ <b>Topshiriq yaratildi!</b>\n\n"
        f"📝 {task.title}\n"
        f"💰 Mukofot: {task.reward:,} ball\n"
        f"📊 Tur: {type_names.get(task.task_type)}",
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_task_"))
async def admin_task_detail(callback: CallbackQuery, session: AsyncSession):
    if not await check_admin(session, callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!")
        return

    task_id = int(callback.data.split("_")[2])
    task = await queries.get_task(session, task_id)
    if not task:
        await callback.answer("❌ Topilmadi!")
        return

    status = "✅ Faol" if task.is_active else "❌ Nofaol"
    await callback.message.edit_text(
        f"📝 <b>{task.title}</b>\n\n"
        f"📖 {task.description}\n"
        f"💰 Mukofot: {task.reward:,} ball\n"
        f"📊 Holat: {status}",
        reply_markup=admin_task_manage_keyboard(task_id, task.is_active),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_task_"))
async def toggle_task(callback: CallbackQuery, session: AsyncSession):
    if not await check_admin(session, callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!")
        return

    task_id = int(callback.data.split("_")[2])
    await queries.toggle_task(session, task_id)
    task = await queries.get_task(session, task_id)
    status = "✅ Faol" if task.is_active else "❌ Nofaol"

    await callback.message.edit_text(
        f"📝 <b>{task.title}</b>\n\n"
        f"📖 {task.description}\n"
        f"💰 Mukofot: {task.reward:,} ball\n"
        f"📊 Holat: {status}",
        reply_markup=admin_task_manage_keyboard(task_id, task.is_active),
        parse_mode="HTML"
    )
    await callback.answer(f"Holat o'zgartirildi: {status}")


@router.callback_query(F.data.startswith("delete_task_"))
async def delete_task(callback: CallbackQuery, session: AsyncSession):
    if not await check_admin(session, callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!")
        return

    task_id = int(callback.data.split("_")[2])
    await queries.delete_task(session, task_id)
    await callback.message.edit_text("🗑 Topshiriq o'chirildi.")
    await callback.answer("✅ O'chirildi!")


@router.callback_query(F.data == "admin_tasks_back")
async def admin_tasks_back(callback: CallbackQuery, session: AsyncSession):
    tasks = await queries.get_active_tasks(session)
    await callback.message.edit_text(
        f"📝 <b>Topshiriqlar ({len(tasks)} ta)</b>",
        reply_markup=admin_tasks_keyboard(tasks),
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== PROMO CODES ====================

@router.message(F.text == "🎟 Bonuslar")
async def admin_bonuses(message: Message, session: AsyncSession, state: FSMContext):
    if not await check_admin(session, message.from_user.id):
        return

    promos = await queries.get_all_promos(session)
    text = f"🎟 <b>Promo kodlar ({len(promos)} ta)</b>\n\n"
    for p in promos[:10]:
        status = "✅" if p.is_active else "❌"
        text += f"{status} <code>{p.code}</code> — {p.reward:,} ball | {p.used_count}/{p.max_uses}\n"

    text += "\nYangi promo kod yaratish uchun kodni yuboring:"
    await state.set_state(AdminStates.waiting_promo_code)
    await message.answer(text, parse_mode="HTML")


@router.message(AdminStates.waiting_promo_code)
async def process_promo_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    if not code.replace("_", "").replace("-", "").isalnum():
        await message.answer("❌ Faqat harflar va raqamlar ishlatilsin!")
        return
    await state.update_data(promo_code=code)
    await state.set_state(AdminStates.waiting_promo_reward)
    await message.answer(f"✅ Kod: <code>{code}</code>\n\n💰 Mukofot miqdorini yuboring:", parse_mode="HTML")


@router.message(AdminStates.waiting_promo_reward)
async def process_promo_reward(message: Message, state: FSMContext):
    try:
        reward = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Raqam kiriting!")
        return
    await state.update_data(promo_reward=reward)
    await state.set_state(AdminStates.waiting_promo_max_uses)
    await message.answer(f"🔢 Necha marta ishlatilsin? (0 = cheksiz):")


@router.message(AdminStates.waiting_promo_max_uses)
async def process_promo_max_uses(message: Message, state: FSMContext, session: AsyncSession):
    try:
        max_uses = int(message.text.strip())
        if max_uses == 0:
            max_uses = 999999
    except ValueError:
        await message.answer("❌ Raqam kiriting!")
        return

    data = await state.get_data()
    promo = await queries.create_promo(
        session,
        code=data["promo_code"],
        reward=data["promo_reward"],
        max_uses=max_uses
    )
    await state.clear()
    await message.answer(
        f"✅ <b>Promo kod yaratildi!</b>\n\n"
        f"🎟 Kod: <code>{promo.code}</code>\n"
        f"💰 Mukofot: {promo.reward:,} ball\n"
        f"🔢 Limit: {promo.max_uses} marta",
        parse_mode="HTML"
    )


# ==================== REJECT REASON ====================

@router.message(AdminStates.waiting_reject_reason)
async def process_reject_reason(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    withdrawal_id = data.get("reject_withdrawal_id")
    reason = message.text.strip()

    withdrawal = await queries.update_withdrawal_status(session, withdrawal_id, "rejected", reason)
    await state.clear()

    await message.answer(f"✅ So'rov #{withdrawal_id} rad etildi.")

    if withdrawal:
        try:
            await bot.send_message(
                withdrawal.user_id,
                f"❌ <b>To'lov so'rovingiz rad etildi!</b>\n\n"
                f"📋 So'rov #{withdrawal.id}\n"
                f"💰 Miqdor: {withdrawal.amount:,} ball\n"
                f"📝 Sabab: {reason}\n\n"
                f"💎 Ball balansga qaytarildi.",
                parse_mode="HTML"
            )
        except Exception:
            pass


# ==================== BACK TO MAIN ====================

@router.message(F.text == "🔙 Asosiy menyu")
async def back_to_main(message: Message):
    await message.answer("🏠 Asosiy menyu:", reply_markup=main_menu_keyboard())
