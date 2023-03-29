import asyncio
import logging
from telegram.ext import MessageHandler, CallbackQueryHandler
from settings import bot, tg_logger, LOG_CHAT_ID
from bot.button_handlers import *
from bot.button_handlers import handlers as button_handlers, register_button_handler
from bot.command_handlers import *
from bot.command_handlers import handlers as command_handlers
from bot.pages import menu, notification_feature_suggestion
from bot.notification_scheduler import scheduler
from bot.data import UserData, ChatData, Message
from bot import error_handler



error_handler.log_chat_id = LOG_CHAT_ID
logger = logging.getLogger()
logger.info('Starting application')

async def apply_data(upd, ctx):
    ctx._user_data = UserData(upd.effective_user.id)
    ctx._chat_data = ChatData(upd.effective_chat.id)
    if not ctx._chat_data.get('_accessible'):
        ctx._chat_data.set('_accessible', True)

async def btn_handler(upd, ctx):
    logger.info('[chat/{0} user/{1} msg/{2}] callback query: {3}'.format(
        upd.callback_query.message.chat.id,
        upd.callback_query.from_user.id,
        upd.callback_query.message.id,
        upd.callback_query.data))
    await apply_data(upd, ctx)

async def msg_handler(upd, ctx):
    logger.info('[chat/{0} user/{1} msg/{2}] message: {3}'.format(
        upd.message.chat.id,
        upd.message.from_user.id,
        upd.message.id,
        upd.message.text))
    await apply_data(upd, ctx)

@register_button_handler()
async def unsupported_btn_handler(upd, ctx):
    await upd.callback_query.answer(ctx._chat_data.get_lang()['alert.callback_query_unsupported'], show_alert=True)
    msg = await upd.callback_query.message.edit_text(**menu.create_message(ctx))
    ctx._chat_data.add_message(Message(msg.message_id, msg.date, 'menu', ctx._chat_data.get('lang_code')))

async def suggest_notif_feature(upd, ctx):
    if not ctx._chat_data.get('cl_notif_suggested') and ctx._chat_data.get('_created') == 0:
        await asyncio.sleep(1)
        msg = await upd.effective_message.reply_text(**notification_feature_suggestion.create_message(ctx))
        ctx._chat_data.add_message(Message(msg.message_id, msg.date, 'notification_feature_suggestion', ctx._chat_data.get('lang_code')))
        ctx._chat_data.set('cl_notif_suggested', True)

bot.add_handlers([CallbackQueryHandler(btn_handler), MessageHandler(None, msg_handler)])
bot.add_handlers(button_handlers + command_handlers, 10)
bot.add_handlers([CallbackQueryHandler(suggest_notif_feature), MessageHandler(None, suggest_notif_feature)], 15)
bot.add_handlers([CallbackQueryHandler(tg_logger.callback_query_handler), MessageHandler(None, tg_logger.message_handler)], 20)
bot.add_error_handler(error_handler.handler)


# Run notifications scheduler
scheduler.start()
# Run bot
bot.run_polling()
