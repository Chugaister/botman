from bot.misc import *
from bot.keyboards import bot_action
import bot.keyboards.premium as kb


@dp.callback_query_handler(bot_action.filter(action="premium"))
async def premium_menu(cb: CallbackQuery, callback_data: dict):
    await cb.answer("In development ⏳")
