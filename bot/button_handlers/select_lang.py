import os
from telegram import Update
from telegram.ext import CallbackContext
from . import register_button_handler
from ..pages import more, lang_select
from ..settings import langs
from ..utils import parse_callback_query

@register_button_handler(r'^select.lang')
async def handler(update: Update, context: CallbackContext):
    lang_code = parse_callback_query(update.callback_query.data)['args']['lang']

    if not lang_code in langs:
        lang_code = os.getenv('DEFAULT_LANG')

    if lang_code == context._chat_data.lang_code:
        await update.callback_query.message.edit_text(**more.create_message(context))
        return

    context._chat_data.lang_code = lang_code
    await update.callback_query.message.edit_text(**lang_select.create_message(context))
