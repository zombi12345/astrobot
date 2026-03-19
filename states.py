from aiogram.fsm.state import StatesGroup, State

class NatalChartStates(StatesGroup):
    waiting_name = State()
    waiting_birth_date = State() 
    waiting_birth_time = State()
    waiting_birth_place = State()

class AIQuestionStates(StatesGroup):
    waiting_question = State()

class CompatibilityStates(StatesGroup):
    waiting_partner1 = State()
    waiting_partner2 = State()

class ProfileEditStates(StatesGroup):
    waiting_birth_date = State()
    waiting_birth_time = State()
    waiting_birth_place = State()

class AdminStatesGroup(StatesGroup):
    waiting_user_id = State()
    waiting_subscription_days = State()
    waiting_broadcast_message = State()