from bot.misc import *
from bot.keyboards import bot_action
import bot.keyboards.premium as kb


@dp.callback_query_handler(bot_action.filter(action="premium"))
async def premium_menu(cb: CallbackQuery, callback_data: dict):
    bot_dc = bots_db.get(int(callback_data["id"]))
    await cb.message.answer(
        "{text7}\nАби отримати преміум, зв'яжіться з адміністратором",
        reply_markup=kb.gen_premium_menu(bot_dc)
    )
    try:
        await cb.message.delete()
    except MessageCantBeDeleted:
        pass
