from bot.misc import *
from bot.keyboards import bot_action
import bot.keyboards.premium as kb


@dp.callback_query_handler(bot_action.filter(action="premium"))
async def premium_menu(cb: CallbackQuery, callback_data: dict):
    bot_dc = await bots_db.getFromDB(int(callback_data["id"]))
    await cb.message.answer(
        "{text7}\nАби отримати преміум, зв'яжіться з адміністратором",
        reply_markup=kb.gen_premium_menu(bot_dc)
    )
    await safe_del_msg(cb.from_user.id, cb.message.message_id)
