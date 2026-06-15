from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ===================== REPLY KEYBOARDS =====================

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Balansim"), KeyboardButton(text="👥 Do'st taklif qilish")],
            [KeyboardButton(text="📋 Kunlik topshiriq"), KeyboardButton(text="🏆 Reyting")],
            [KeyboardButton(text="🎁 Bonuslar"), KeyboardButton(text="💳 Mablag' yechish")],
            [KeyboardButton(text="❓ Yordam")],
        ],
        resize_keyboard=True
    )
    return keyboard


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="👤 Foydalanuvchilar")],
            [KeyboardButton(text="🔗 Referallar"), KeyboardButton(text="💸 To'lovlar")],
            [KeyboardButton(text="📢 Kanallar"), KeyboardButton(text="📣 Xabar yuborish")],
            [KeyboardButton(text="📝 Topshiriqlar"), KeyboardButton(text="🎟 Bonuslar")],
            [KeyboardButton(text="🔙 Asosiy menyu")],
        ],
        resize_keyboard=True
    )
    return keyboard


# ===================== INLINE KEYBOARDS =====================

def subscription_check_keyboard(channels: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        builder.button(text=f"📢 {ch.channel_name}", url=ch.channel_link)
    builder.button(text="✅ Tekshirish", callback_data="check_subscription")
    builder.adjust(1)
    return builder.as_markup()


def withdraw_confirm_keyboard(amount: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"withdraw_confirm_{amount}")
    builder.button(text="❌ Bekor qilish", callback_data="withdraw_cancel")
    builder.adjust(2)
    return builder.as_markup()


def admin_withdrawal_keyboard(withdrawal_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"admin_approve_{withdrawal_id}")
    builder.button(text="❌ Rad etish", callback_data=f"admin_reject_{withdrawal_id}")
    builder.adjust(2)
    return builder.as_markup()


def tasks_keyboard(tasks: list, completed_task_ids: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for task in tasks:
        status = "✅" if task.id in completed_task_ids else "📋"
        type_emoji = {"simple": "🟢", "complex": "🔴", "weekly": "⭐"}.get(task.task_type, "📋")
        builder.button(
            text=f"{status} {type_emoji} {task.title} (+{task.reward} ball)",
            callback_data=f"task_{task.id}"
        )
    builder.adjust(1)
    return builder.as_markup()


def task_detail_keyboard(task_id: int, is_completed: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if not is_completed:
        builder.button(text="✅ Bajarildim", callback_data=f"complete_task_{task_id}")
    builder.button(text="🔙 Orqaga", callback_data="back_to_tasks")
    builder.adjust(1)
    return builder.as_markup()


def admin_channels_keyboard(channels: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        builder.button(
            text=f"❌ {ch.channel_name}",
            callback_data=f"del_channel_{ch.id}"
        )
    builder.button(text="➕ Kanal qo'shish", callback_data="add_channel")
    builder.adjust(1)
    return builder.as_markup()


def admin_tasks_keyboard(tasks: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for task in tasks:
        status = "✅" if task.is_active else "❌"
        builder.button(
            text=f"{status} {task.title}",
            callback_data=f"admin_task_{task.id}"
        )
    builder.button(text="➕ Topshiriq qo'shish", callback_data="add_task")
    builder.adjust(1)
    return builder.as_markup()


def admin_task_manage_keyboard(task_id: int, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    toggle_text = "❌ O'chirish" if is_active else "✅ Yoqish"
    builder.button(text=toggle_text, callback_data=f"toggle_task_{task_id}")
    builder.button(text="🗑 O'chirish", callback_data=f"delete_task_{task_id}")
    builder.button(text="🔙 Orqaga", callback_data="admin_tasks_back")
    builder.adjust(2)
    return builder.as_markup()


def pending_withdrawals_keyboard(withdrawals: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for w in withdrawals:
        builder.button(
            text=f"#{w.id} - {w.amount} ball",
            callback_data=f"view_withdrawal_{w.id}"
        )
    builder.adjust(1)
    return builder.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Bekor qilish", callback_data="cancel")
    return builder.as_markup()
