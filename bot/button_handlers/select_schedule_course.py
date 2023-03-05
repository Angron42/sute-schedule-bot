import telebot.types
import logging
from ..settings import bot, chat_configs
from ..pages import select_group

logger = logging.getLogger(__name__)

@bot.callback_query_handler(func=lambda call: call.query == 'select.schedule.course')
def handler(call: telebot.types.CallbackQuery):
    logger.debug('Handling callback query')
    structureId = int(call.args['structureId'])
    facultyId = int(call.args['facultyId'])
    course = int(call.args['course'])
    bot.edit_message_text(**select_group.create_message(call.message.lang_code, structureId, facultyId, course), chat_id=call.message.chat.id, message_id=call.message.message_id)
