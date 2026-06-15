from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database import queries
from keyboards import tasks_keyboard, task_detail_keyboard
from utils.helpers import format_task_type

router = Router()


@router.message(F.text == "📋 Kunlik topshiriq")
async def tasks_handler(message: Message, session: AsyncSession):
    user = await queries.get_user(session, message.from_user.id)
    if not user:
        await message.answer("❌ Siz ro'yxatdan o'tmagansiz. /start bosing.")
        return

    tasks = await queries.get_active_tasks(session)
    if not tasks:
        await message.answer(
            "📋 <b>Kunlik topshiriqlar</b>\n\n"
            "⏳ Hozircha faol topshiriqlar yo'q. Keyinroq keling!",
            parse_mode="HTML"
        )
        return

    # Get completed task IDs for this user
    completed_ids = []
    for task in tasks:
        if await queries.is_task_completed(session, user.telegram_id, task.id):
            completed_ids.append(task.id)

    total_available = sum(t.reward for t in tasks if t.id not in completed_ids)

    text = (
        f"📋 <b>Kunlik topshiriqlar</b>\n\n"
        f"✅ Bajarilgan: <b>{len(completed_ids)}/{len(tasks)}</b>\n"
        f"💰 Mavjud ball: <b>+{total_available:,}</b>\n\n"
        f"Topshiriqni tanlang:"
    )
    await message.answer(
        text,
        reply_markup=tasks_keyboard(tasks, completed_ids),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("task_"))
async def task_detail_callback(callback: CallbackQuery, session: AsyncSession):
    task_id = int(callback.data.split("_")[1])
    user = await queries.get_user(session, callback.from_user.id)
    task = await queries.get_task(session, task_id)

    if not task:
        await callback.answer("❌ Topshiriq topilmadi!", show_alert=True)
        return

    is_completed = await queries.is_task_completed(session, user.telegram_id, task_id)

    type_emoji = {"simple": "🟢", "complex": "🔴", "weekly": "⭐"}.get(task.task_type, "📋")
    status_text = "✅ Bajarilgan" if is_completed else "⏳ Bajarilmagan"

    text = (
        f"{type_emoji} <b>{task.title}</b>\n\n"
        f"📝 {task.description}\n\n"
        f"💰 Mukofot: <b>+{task.reward:,} ball</b>\n"
        f"📊 Turi: {format_task_type(task.task_type)}\n"
        f"📌 Holat: {status_text}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=task_detail_keyboard(task_id, is_completed),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("complete_task_"))
async def complete_task_callback(callback: CallbackQuery, session: AsyncSession):
    task_id = int(callback.data.split("_")[2])
    user = await queries.get_user(session, callback.from_user.id)

    reward = await queries.complete_task(session, user.telegram_id, task_id)
    if reward == 0:
        await callback.answer("❌ Topshiriq allaqachon bajarilgan!", show_alert=True)
        return

    await callback.answer(f"✅ Barakalla! +{reward} ball qo'shildi!", show_alert=True)

    task = await queries.get_task(session, task_id)
    type_emoji = {"simple": "🟢", "complex": "🔴", "weekly": "⭐"}.get(task.task_type, "📋")

    text = (
        f"{type_emoji} <b>{task.title}</b>\n\n"
        f"📝 {task.description}\n\n"
        f"💰 Mukofot: <b>+{task.reward:,} ball</b>\n"
        f"📊 Turi: {format_task_type(task.task_type)}\n"
        f"📌 Holat: ✅ Bajarilgan"
    )
    await callback.message.edit_text(
        text,
        reply_markup=task_detail_keyboard(task_id, True),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_to_tasks")
async def back_to_tasks_callback(callback: CallbackQuery, session: AsyncSession):
    user = await queries.get_user(session, callback.from_user.id)
    tasks = await queries.get_active_tasks(session)

    completed_ids = []
    for task in tasks:
        if await queries.is_task_completed(session, user.telegram_id, task.id):
            completed_ids.append(task.id)

    total_available = sum(t.reward for t in tasks if t.id not in completed_ids)

    text = (
        f"📋 <b>Kunlik topshiriqlar</b>\n\n"
        f"✅ Bajarilgan: <b>{len(completed_ids)}/{len(tasks)}</b>\n"
        f"💰 Mavjud ball: <b>+{total_available:,}</b>\n\n"
        f"Topshiriqni tanlang:"
    )
    await callback.message.edit_text(
        text,
        reply_markup=tasks_keyboard(tasks, completed_ids),
        parse_mode="HTML"
    )
    await callback.answer()
