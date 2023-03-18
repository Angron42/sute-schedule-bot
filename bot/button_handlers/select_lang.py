import os
from telegram import Update
from telegram.ext import CallbackContext
from . import register_button_handler
from ..pages import lang_selection, more
from ..settings import langs
from ..utils import parse_callback_query

@register_button_handler('^select.lang')
async def handler(update: Update, context: CallbackContext):
    lang_code = parse_callback_query(update.callback_query.data)['args']['lang']

    if not lang_code in langs:
        lang_code = os.getenv('DEFAULT_LANG')

    if lang_code == context._chat_data.lang_code:
        await update.callback_query.edit_message_text(**more.create_message(context))
        return

    context._chat_data.lang_code = lang_code
    await update.callback_query.edit_message_text(**lang_selection.create_message(context))
