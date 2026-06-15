from aiogram.fsm.state import StatesGroup, State


class WithdrawStates(StatesGroup):
    waiting_card = State()
    waiting_amount = State()
    confirm = State()


class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_channel_id = State()
    waiting_channel_name = State()
    waiting_channel_link = State()
    waiting_task_title = State()
    waiting_task_description = State()
    waiting_task_reward = State()
    waiting_task_type = State()
    waiting_promo_code = State()
    waiting_promo_reward = State()
    waiting_promo_max_uses = State()
    waiting_reject_reason = State()
