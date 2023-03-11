from telegram import Update
from telegram.ext import CallbackContext
from . import register_button_handler
from ..pages import schedule
from ..utils import parse_callback_query

@register_button_handler(r'^open.schedule.day')
async def handler(update: Update, context: CallbackContext):
    date = parse_callback_query(update.callback_query.data)['args']['date']
    await update.callback_query.message.edit_text(**schedule.create_message(context, date=date))
