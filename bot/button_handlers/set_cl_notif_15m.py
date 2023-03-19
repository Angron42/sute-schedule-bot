from telegram import Update
from telegram.ext import CallbackContext
from . import register_button_handler
from ..pages import settings
from ..utils import parse_callback_query

@register_button_handler('^set.cl_notif_15m')
async def handler(update: Update, context: CallbackContext):
    args = parse_callback_query(update.callback_query.data)['args']
    state = args['state'] == '1'
    context._chat_data.cl_notif_15m = state

    if state:
        context._chat_data.cl_notif_1m = False

    await update.callback_query.edit_message_text(**settings.create_message(context))
