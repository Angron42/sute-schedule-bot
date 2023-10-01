# pylint: disable=redefined-outer-name

"""
This module contains all bot pages.
"""

import os
import random
import logging
from datetime import date as _date, timedelta
from functools import lru_cache

from babel.dates import format_date
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.helpers import escape_markdown
from requests.exceptions import RequestException, HTTPError

from lib.api import utils as api_utils
from lib.api.exceptions import HTTPApiException
from lib.teacher_loader.schemas import Teacher
from bot.data import ContextManager, ChatDataManager, groups_cache
from bot.utils import array_split, clean_html, timeformatter, lessontime
from settings import api, langs, teacher_finder, TELEGRAM_SUPPORTED_HTML_TAGS

logger = logging.getLogger(__name__)


def access_denied(ctx: ContextManager) -> dict:
    """Access denied page"""

    buttons = [[
        InlineKeyboardButton(text=ctx.lang.get('button.menu'),
                             callback_data='open.menu')
    ]]

    return {
        'text': ctx.lang.get('alert.no_permissions'),
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def admin_panel(ctx: ContextManager) -> dict:
    """Admin panel page"""

    buttons = [
        [InlineKeyboardButton(text=ctx.lang.get('button.admin.clear_cache'),
                              callback_data='admin.clear_cache')],
        [InlineKeyboardButton(text=ctx.lang.get('button.admin.get_logs'),
                              callback_data='admin.get_logs')],
        [InlineKeyboardButton(text=ctx.lang.get('button.admin.clear_logs'),
                              callback_data='admin.clear_logs')],
        [InlineKeyboardButton(text=ctx.lang.get('button.back'),
                              callback_data='open.menu')]
    ]

    return {
        'text': ctx.lang.get('page.admin_panel'),
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def api_unavaliable(ctx: ContextManager) -> dict:
    """API unavaliable page"""

    buttons = [[
        InlineKeyboardButton(text=ctx.lang.get('button.menu'),
                             callback_data='open.menu'),
        InlineKeyboardButton(text=ctx.lang.get('button.write_me'),
                             url='https://t.me/cubicbyte')
    ]]

    return {
        'text': ctx.lang.get('page.api_unavaliable'),
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def calls(ctx: ContextManager, back_btn: str = 'open.menu') -> dict:
    """Calls page"""

    try:
        schedule_section = _get_calls_section_text()
    except HTTPApiException:
        return api_unavaliable(ctx)

    buttons = [[
        InlineKeyboardButton(text=ctx.lang.get('button.back'),
                             callback_data=back_btn),
    ]]

    return {
        'text': ctx.lang.get('page.calls').format(schedule=schedule_section),
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def classes_notification(chat_data: ChatDataManager, day: dict, remaining: str) -> dict:
    """Classes notification page"""

    buttons = [[
        InlineKeyboardButton(text=chat_data.lang.get('button.open_schedule'),
                             callback_data=f'open.schedule.day#date={day["date"]}'),
        InlineKeyboardButton(text=chat_data.lang.get('button.settings'),
                             callback_data='open.settings')
    ]]

    return {
        'text': chat_data.lang.get('page.classes_notification').format(
            remaining=remaining,
            schedule=_get_notification_schedule_section(day)),
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def course_list(ctx: ContextManager, structure_id: int, faculty_id: int) -> dict:
    """Course list page"""

    try:
        courses = api.list_courses(faculty_id, language=ctx.chat_data.get('lang_code'))
    except HTTPApiException:
        return api_unavaliable(ctx)

    buttons = [[
        InlineKeyboardButton(
            text=ctx.lang.get('button.back'),
            callback_data=f'select.schedule.structure#structureId={structure_id}')
    ]]

    for course in courses:
        buttons.append([
            InlineKeyboardButton(
                text=str(course['course']),
                callback_data='select.schedule.course#'
                    + f'structureId={structure_id}&'
                    + f'facultyId={faculty_id}&'
                    + f'course={course["course"]}')
        ])

    return {
        'text': ctx.lang.get('page.course'),
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def faculty_list(ctx: ContextManager, structure_id: int) -> dict:
    """Faculty list page"""

    try:
        faculties = api.list_faculties(structure_id, language=ctx.chat_data.get('lang_code'))
        structures = api.list_structures(language=ctx.chat_data.get('lang_code'))
    except HTTPApiException:
        return api_unavaliable(ctx)

    buttons = []

    if len(structures) > 1:
        buttons.append([
            InlineKeyboardButton(
                text=ctx.lang.get('button.back'),
                callback_data='open.select_group')
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text=ctx.lang.get('button.back'),
                callback_data='open.menu')
        ])

    for faculty in faculties:
        buttons.append([
            InlineKeyboardButton(
                text=faculty['fullName'],
                callback_data='select.schedule.faculty#'
                    + f'structureId={structure_id}&'
                    + f'facultyId={faculty["id"]}')
        ])

    return {
        'text': ctx.lang.get('page.faculty'),
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def greeting(ctx: ContextManager) -> dict:
    """Greeting page"""

    return {
        'text': ctx.lang.get('page.greeting'),
        'parse_mode': 'MarkdownV2'
    }


def group_list(ctx: ContextManager, structure_id: int, faculty_id: int, course: int) -> dict:
    """Group list page"""

    try:
        groups = api.list_groups(faculty_id, course, language=ctx.chat_data.get('lang_code'))
    except HTTPApiException:
        return api_unavaliable(ctx)
    
    # Save groups to cache
    groups_cache.add_groups_to_cache(groups, faculty_id, course)

    buttons = [[
        InlineKeyboardButton(
            text=ctx.lang.get('button.back'),
            callback_data='select.schedule.faculty#'
                + f'structureId={structure_id}&'
                + f'facultyId={faculty_id}')
    ]]

    group_btns = []
    for group in groups:
        group_btns.append(
            InlineKeyboardButton(
                text=group['name'],
                callback_data=f'select.schedule.group#groupId={group["id"]}')
        )

    # Make many 3-wide button rows like this: [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    buttons.extend(array_split(group_btns, 3))

    return {
        'text': ctx.lang.get('page.group'),
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def info(ctx: ContextManager) -> dict:
    """Info page"""

    try:
        api_ver = escape_markdown(api.version()['name'], version=2)
    except RequestException:
        api_ver = ctx.lang.get('text.unknown')

    message_text = ctx.lang.get('page.info').format(
        api_ver=api_ver,
        api_ver_supported=escape_markdown(api.VERSION, version=2)
    )

    buttons = [[
        InlineKeyboardButton(text=ctx.lang.get('button.back'),
                             callback_data='open.more'),
        InlineKeyboardButton(text=ctx.lang.get('button.menu'),
                             callback_data='open.menu')
    ]]

    return {
        'text': message_text,
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2',
        'disable_web_page_preview': True
    }


def invalid_group(ctx: ContextManager) -> dict:
    """Invalid group page"""

    buttons = [[
        InlineKeyboardButton(text=ctx.lang.get('button.select_group'),
                             callback_data='open.select_group'),
        InlineKeyboardButton(text=ctx.lang.get('button.menu'),
                             callback_data='open.menu')
    ]]

    return {
        'text': ctx.lang.get('page.invalid_group'),
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def lang_selection(ctx: ContextManager) -> dict:
    """Language selection page"""

    buttons = []

    for lang_name, lang in langs.items():
        buttons.append([
            InlineKeyboardButton(text=lang.get('lang_name'),
                                 callback_data=f'select.lang#lang={lang_name}')
        ])

    buttons.append([
        InlineKeyboardButton(text=ctx.lang.get('button.back'),
                             callback_data='open.settings'),
        InlineKeyboardButton(text=ctx.lang.get('button.menu'),
                             callback_data='open.menu')
    ])

    return {
        'text': ctx.lang.get('page.lang_select').format(
            lang=ctx.lang.get('lang_name')),
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def left(ctx: ContextManager, back_btn: str = 'open.menu') -> dict:
    """Left page"""

    if ctx.chat_data.get('group_id') is None:
        return invalid_group(ctx)

    try:
        schedule = api.timetable_group(ctx.chat_data.get('group_id'), _date.today())
        rem_time = lessontime.get_calls_status(schedule[0]['lessons'])
    except HTTPApiException:
        return api_unavaliable(ctx)

    buttons = [[
        InlineKeyboardButton(text=ctx.lang.get('button.back'), callback_data=back_btn),
        InlineKeyboardButton(text=ctx.lang.get('button.refresh'), callback_data=f'open.left#rnd={random.random()}')
    ]]

    # If there is no classes
    if rem_time is None or rem_time['status'] == 'ended':
        page_text = ctx.lang.get('page.left.no_more')

    else:
        time_formatted = timeformatter.format_time(
            lang_code=ctx.chat_data.get('lang_code'),
            time=rem_time['time'], depth=2
        )

        # Lesson is going
        if rem_time['status'] == 'going':
            page_text = ctx.lang.get('page.left.to_end').format(
                left=escape_markdown(time_formatted, version=2)
            )

        # Classes is not started yet or it's break
        else:
            page_text = ctx.lang.get('page.left.to_start').format(
                left=escape_markdown(time_formatted, version=2)
            )

    return {
        'text': page_text,
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def menu(ctx: ContextManager) -> dict:
    """Menu page"""

    buttons = [[
        InlineKeyboardButton(text=ctx.lang.get('button.schedule'),
                             callback_data='open.schedule.today')
    ], [
        InlineKeyboardButton(text=ctx.lang.get('button.settings'),
                             callback_data='open.settings'),
        InlineKeyboardButton(text=ctx.lang.get('button.more'),
                             callback_data='open.more')
    ]]

    # If user is admin, then add "control panel" button
    if ctx.user_data.get('admin'):
        buttons.append([
            InlineKeyboardButton(text=ctx.lang.get('button.admin.panel'),
                                 callback_data='admin.open_panel')
        ])

    return {
        'text': ctx.lang.get('page.menu'),
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def more(ctx: ContextManager) -> dict:
    """More page"""

    buttons = [[
        InlineKeyboardButton(text=ctx.lang.get('button.calls'),
                             callback_data='open.calls'),
        InlineKeyboardButton(text=ctx.lang.get('button.left'),
                             callback_data='open.left')
    ], [
        InlineKeyboardButton(text=ctx.lang.get('button.students_list'),
                             callback_data='open.students_list')
    ], [
        InlineKeyboardButton(text=ctx.lang.get('button.info'),
                             callback_data='open.info')
    ], [
        InlineKeyboardButton(text=ctx.lang.get('button.back'),
                             callback_data='open.menu')
    ]]

    return {
        'text': ctx.lang.get('page.more'),
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def schedule(ctx: ContextManager, date: _date | str) -> dict:
    """Schedule page"""

    # Create "date_str" and "date" variables
    if isinstance(date, _date):
        date_str = date.isoformat()
    else:
        date_str = date
        date = _date.fromisoformat(date_str)

    # Get schedule
    try:
        schedule = api.timetable_group(
                ctx.chat_data.get('group_id'), date,
                language=ctx.chat_data.get('lang_code'))

    except HTTPError as err:
        if err.response.status_code == 422:
            return invalid_group(ctx)
        return api_unavaliable(ctx)

    except HTTPApiException:
        return api_unavaliable(ctx)

    # Find schedule of current day
    cur_day_schedule = None
    for day in schedule:
        if day['date'] == date_str:
            cur_day_schedule = day
            break

    # "no lessons" page
    if cur_day_schedule is None \
            or len(cur_day_schedule['lessons']) == 0 \
            or _is_day_empty(cur_day_schedule):
        return empty_schedule(ctx, date)

    # Schedule page
    return day_schedule(ctx, date, cur_day_schedule)


def day_schedule(ctx: ContextManager, date: _date, day: dict) -> dict:
    """Schedule page"""

    lang = ctx.lang

    msg_text = ctx.lang.get('page.schedule').format(
        date=_get_localized_date(ctx, date),
        schedule=_create_schedule_section(ctx, day)
    )

    # Create buttons
    buttons = [
        InlineKeyboardButton(text=lang.get('button.navigation.day_previous'),
                             callback_data='open.schedule.day#date='
                             + (date - timedelta(days=1)).isoformat()),
        InlineKeyboardButton(text=lang.get('button.navigation.day_next'),
                             callback_data='open.schedule.day#date='
                             + (date + timedelta(days=1)).isoformat()),
        InlineKeyboardButton(text=lang.get('button.navigation.week_previous'),
                             callback_data='open.schedule.day#week&date='
                             + (date - timedelta(days=7)).isoformat()),
        InlineKeyboardButton(text=lang.get('button.navigation.week_next'),
                             callback_data='open.schedule.day#week&date='
                             + (date + timedelta(days=7)).isoformat()
                             + f'&rnd={random.random()}'),  # Needed to prevent "Message is not modified" error
        InlineKeyboardButton(text=lang.get('button.menu'), callback_data='open.menu')
    ]

    # "Today" button
    if date != _date.today():
        buttons.append(InlineKeyboardButton(
            text=lang.get('button.navigation.today'),
            callback_data='open.schedule.today'
        ))

    # Split buttons into 2-wide rows
    buttons = array_split(buttons, 2)

    # "Additional info" button
    if _check_extra_text(day):
        buttons.insert(0, [InlineKeyboardButton(
            text=lang.get('button.schedule.extra'),
            callback_data='open.schedule.extra#date=' + date.isoformat()
        )])


    return {
        'text': msg_text,
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2',
        'disable_web_page_preview': True
    }


def empty_schedule(ctx: ContextManager, date: _date, schedule: list[dict] | None = None) -> dict:
    """Empty schedule page"""

    lang = ctx.lang

    if schedule is None:
        date_start, date_end = api_utils.get_date_range(date)
        try:
            schedule = api.timetable_group(
                    ctx.chat_data.get('group_id'), date_start, date_end,
                    language=ctx.chat_data.get('lang_code'))

        except HTTPError as err:
            if err.response.status_code == 422:
                return invalid_group(ctx)
            return api_unavaliable(ctx)

        except HTTPApiException:
            return api_unavaliable(ctx)

    # Number of days you need to skip to reach a day with lessons
    skip_left = _count_no_lesson_days(schedule, date, direction_right=False)
    skip_right = _count_no_lesson_days(schedule, date, direction_right=True)
    if skip_right is None:
        skip_right = (_date.fromisoformat(schedule[-1]['date']) - date).days + 1
    if skip_left is None:
        skip_left = (date - _date.fromisoformat(schedule[0]['date'])).days + 1

    # Decide whether to show the "today" button, and also
    # decide the "next" and "previous" buttons skip values
    next_day_date = date + timedelta(days=skip_right)
    prev_day_date = date - timedelta(days=skip_left)
    next_week_date = date + timedelta(days=7)
    prev_week_date = date - timedelta(days=7)
    enable_today_button = not next_day_date > _date.today() > prev_day_date

    # If there are no lessons for multiple days
    # Then combine all the days without lessons into one page
    if skip_left > 1 or skip_right > 1:
        msg_text = lang.get('page.schedule.empty.multiple_days').format(
            dateStart=_get_localized_date(ctx, prev_day_date + timedelta(days=1)),
            dateEnd=  _get_localized_date(ctx, next_day_date - timedelta(days=1)),
        )

        next_week_date = max(next_week_date, next_day_date)
        prev_week_date = min(prev_week_date, prev_day_date)
    else:
        # If no lessons for only one day
        msg_text = lang.get('page.schedule.empty').format(date=_get_localized_date(ctx, date))

    # Create buttons
    buttons = [
        InlineKeyboardButton(text=lang.get('button.navigation.day_previous'),
                             callback_data='open.schedule.day#date='
                             + prev_day_date.isoformat()),
        InlineKeyboardButton(text=lang.get('button.navigation.day_next'),
                             callback_data='open.schedule.day#date='
                             + next_day_date.isoformat()),
        InlineKeyboardButton(text=lang.get('button.navigation.week_previous'),
                             callback_data='open.schedule.day#week&date='
                             + prev_week_date.isoformat()),
        InlineKeyboardButton(text=lang.get('button.navigation.week_next'),
                             callback_data='open.schedule.day#week&date='
                             + next_week_date.isoformat()
                             + f'&rnd={random.random()}'),  # Needed to prevent "Message is not modified" error
        InlineKeyboardButton(text=lang.get('button.menu'), callback_data='open.menu')
    ]

    if enable_today_button:
        buttons.append(InlineKeyboardButton(
            text=lang.get('button.navigation.today'),
            callback_data='open.schedule.today'
        ))

    # Split buttons into 2-wide rows
    buttons = array_split(buttons, 2)


    return {
        'text': msg_text,
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def schedule_extra(ctx: ContextManager, date: _date | str) -> dict:
    """Schedule extra information page"""

    if isinstance(date, _date):
        date_str = date.isoformat()
    else:
        date_str = date
        date = _date.fromisoformat(date)

    # Get schedule
    try:
        schedule = api.timetable_group(ctx.chat_data.get('group_id'), date_str,
                                       language=ctx.chat_data.get('lang_code'))
    except HTTPApiException:
        return api_unavaliable(ctx)

    # Find schedule of current day
    cur_day_schedule = None
    for day in schedule:
        if day['date'] == date_str:
            cur_day_schedule = day
            break

    if cur_day_schedule is None:
        return empty_schedule(ctx, schedule, date, date, date)

    page_text = ''

    try:
        for lesson in cur_day_schedule['lessons']:
            for period in lesson['periods']:
                if period['extraText']:
                    extra_text = api.timetable_ad(
                        period['r1'], date_str,
                        language=ctx.chat_data.get('lang_code'))['html']
                    extra_text = clean_html(extra_text, tags_whitelist=TELEGRAM_SUPPORTED_HTML_TAGS)
                    extra_text = extra_text.strip()
                    page_text += f'\n\n<b>{lesson["number"]})</b> {extra_text}'

    except HTTPError as err:
        if err.response.status_code == 403:
            return forbidden(ctx, back_btn='open.schedule.day#date=' + date_str)
        if err.response.status_code == 404:
            return not_found(ctx, back_btn='open.schedule.day#date=' + date_str)
        return api_unavaliable(ctx)
    except HTTPApiException:
        return api_unavaliable(ctx)

    return {
        'text': ctx.lang.get('page.schedule.extra').format(page_text[2:]),
        'reply_markup': InlineKeyboardMarkup([[
            InlineKeyboardButton(text=ctx.lang.get('button.back'),
                                 callback_data='open.schedule.day#date=' + date_str)
        ]]),
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }


def settings(ctx: ContextManager) -> dict:
    """Settings menu page"""

    lang = ctx.lang
    cl_notif_15m = ctx.chat_data.get('cl_notif_15m')
    cl_notif_1m = ctx.chat_data.get('cl_notif_1m')

    # Mark settings as seen
    if not ctx.chat_data.get('seen_settings'):
        ctx.chat_data.set('seen_settings', True)

    # Get chat group name
    if ctx.chat_data.get('group_id') is not None:
        res = groups_cache.get_group(group_id=ctx.chat_data.get('group_id'))
        if res is None:
            group = lang.get('text.unknown')
        else:
            group = escape_markdown(res['name'], version=2)
    else:
        group = lang.get('text.not_selected')

    buttons = [[
        InlineKeyboardButton(
            text=lang.get('button.select_group'),
            callback_data='open.select_group'),
        InlineKeyboardButton(
            text=lang.get('button.select_lang'),
            callback_data='open.select_lang')
    ], [
        InlineKeyboardButton(
            text=lang.get('button.settings.cl_notif_15m'),
            callback_data=f'set.cl_notif#time=15m&state={int(not cl_notif_15m)}')
    ], [
        InlineKeyboardButton(
            text=lang.get('button.settings.cl_notif_1m'),
            callback_data=f'set.cl_notif#time=1m&state={int(not cl_notif_1m)}')
    ], [
        InlineKeyboardButton(
            text=lang.get('button.back'),
            callback_data='open.menu')
    ]]

    def get_icon(setting: bool) -> str:
        return '✅' if setting else '❌'

    page_text = lang.get('page.settings').format(
        group_id=group,
        cl_notif_15m=get_icon(cl_notif_15m),
        cl_notif_1m=get_icon(cl_notif_1m)
    )

    return {
        'text': page_text,
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def statistic(ctx: ContextManager) -> dict:
    """Statistic page"""

    chat_dir = os.path.join(os.getenv('LOGS_PATH'), 'telegram', 'chats', str(ctx.update.effective_chat.id))

    # Get first message date and message count
    with open(os.path.join(chat_dir, 'messages.txt'), encoding='utf-8') as file:
        messages = 0
        for messages, line in enumerate(file):
            if messages == 0:
                first_msg_date = line[1:line.index(']')]

    # Get number of button clicks
    with open(os.path.join(chat_dir, 'cb_queries.txt'), encoding='utf-8') as file:
        clicks = 0
        for clicks, _ in enumerate(file):
            pass

    message_text = '*Statistic*\n\n'
    message_text += f'This chat ID: {ctx.update.effective_chat.id}\n'
    message_text += f'Your ID: {ctx.update.effective_user.id}\n'
    message_text += f'Messages: {messages}\n'
    message_text += f'Button clicks: {clicks}\n'
    message_text += f'First message: {escape_markdown(first_msg_date, version=2)}'

    buttons = [[
        InlineKeyboardButton(text=ctx.lang.get('button.menu'),
                             callback_data='open.menu'),
        InlineKeyboardButton(text='How Did We Get Here?',
                             url='https://github.com/cubicbyte/dteubot')
    ]]

    return {
        'text': message_text,
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def structure_list(ctx: ContextManager) -> dict:
    """Structures list menu page"""

    try:
        structures = api.list_structures(language=ctx.chat_data.get('lang_code'))
    except HTTPApiException:
        return api_unavaliable(ctx)

    # If there is only one structure, show faculties page
    if len(structures) == 1:
        return faculty_list(ctx, structures[0]['id'])

    buttons = [[
        InlineKeyboardButton(text=ctx.lang.get('button.back'), callback_data='open.menu')
    ]]

    for structure in structures:
        buttons.append([
            InlineKeyboardButton(
                text=structure['fullName'],
                callback_data=f'select.schedule.structure#structureId={structure["id"]}')
        ])

    return {
        'text': ctx.lang.get('page.structure'),
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def error(ctx: ContextManager) -> dict:
    """Error page"""

    return {
        'text': ctx.lang.get('page.error'),
        'reply_markup': InlineKeyboardMarkup([[
            InlineKeyboardButton(text=ctx.lang.get('button.menu'), callback_data='open.menu')
        ]]),
        'parse_mode': 'MarkdownV2'
    }


def notification_feature_suggestion(ctx: ContextManager) -> dict:
    buttons = [[
        InlineKeyboardButton(text=ctx.lang.get('text.try_it'),
                             callback_data='set.cl_notif#time=15m&state=1&suggestion'),
        InlineKeyboardButton(text=ctx.lang.get('text.no_thanks'),
                             callback_data='close_page#page=notification_feature_suggestion')
    ]]

    return {
        'text': ctx.lang.get('page.notification_feature_suggestion'),
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def forbidden(ctx: ContextManager, back_btn: str | None = None) -> dict:
    """Forbidden page"""

    buttons = []

    if back_btn is None:
        buttons.append([
            InlineKeyboardButton(text=ctx.lang.get('button.menu'), callback_data='open.menu')
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text=ctx.lang.get('button.back'), callback_data=back_btn)
        ])

    return {
        'text': ctx.lang.get('page.forbidden'),
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def not_found(ctx: ContextManager, back_btn: str | None = None) -> dict:
    """Page when something is not found"""

    buttons = []

    if back_btn is None:
        buttons.append([
            InlineKeyboardButton(text=ctx.lang.get('button.menu'), callback_data='open.menu')
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text=ctx.lang.get('button.back'), callback_data=back_btn)
        ])

    return {
        'text': ctx.lang.get('page.not_found'),
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def students_list(ctx: ContextManager) -> dict:
    """Students list page"""

    # Get students
    try:
        students = api.list_students_by_group(
            group_id=ctx.chat_data.get('group_id'),
            language=ctx.chat_data.get('lang_code'),
        )
    except HTTPApiException as err:
        if err.response.status_code == 422:
            return invalid_group(ctx)
        return api_unavaliable(ctx)

    # Create page text
    page_text = ''

    for i, student in enumerate(students, start=1):
        # 1) Full name\n
        name = escape_markdown(student['lastName'], version=2)
        name += ' ' + escape_markdown(student['firstName'], version=2)
        name += ' ' + escape_markdown(student['secondName'], version=2)

        page_text += f'*{i}\\)* {name}\n'

    # Get group name
    group = groups_cache.get_group(group_id=ctx.chat_data.get('group_id'))
    if group is None:
        group_name = ctx.lang.get('text.unknown')
    else:
        group_name = escape_markdown(group['name'], version=2)

    page_text = ctx.lang.get('page.students_list').format(
        group=group_name,
        students=page_text,
    )

    # Prevent too long message error
    if len(page_text) > 4096:
        page_text = page_text[:4093] + '...'

    return {
        'text': page_text,
        'reply_markup': InlineKeyboardMarkup([[
            InlineKeyboardButton(text=ctx.lang.get('button.back'), callback_data='open.more')
        ]]),
        'parse_mode': 'MarkdownV2'
    }



def _get_calls_section_text() -> str:
    """
    Get calls section text in the calls page

    ## Example:
    ```
    1) 08:20 - 09:40
    2) 10:05 - 11:25
    3) 12:05 - 13:25
    4) 13:50 - 15:10
    5) 15:25 - 16:45
    6) 17:00 - 18:20
    7) 18:30 - 19:50
    8) 19:55 - 21:40
    ```
    """

    parts = []

    for call in api.timetable_call_schedule():
        number = call['number']
        time_start = call['timeStart']
        time_end = call['timeEnd']

        parts.append(f'`{number})` *{time_start}* `-` *{time_end}*')

    return '\n'.join(parts)


def _get_notification_schedule_section(day: dict) -> str:
    """
    Creates a schedule section for the notification page

    ## Example:
    ```
    2) ІнМов за ПроСпр[КонсЕкз]
    3) "В" МатемЛогіка[КонсЕкз]
    ```
    """
    str_format = '`{0})` *{1}*`[{2}]`\n'
    section = ''

    for lesson in day['lessons']:
        for period in lesson['periods']:
            section += str_format.format(
                lesson['number'],
                escape_markdown(period['disciplineShortName'], version=2),
                escape_markdown(period['typeStr'], version=2))

    return section[:-1]


def _count_no_lesson_days(
        schedule: list[dict],
        date: _date,
        direction_right=True) -> int | None:
    """
    Counts the number of days without lessons
    """

    if not direction_right:
        schedule = reversed(schedule)

    for day in schedule:
        day_date = _date.fromisoformat(day['date'])
        if direction_right:
            if day_date > date and not _is_day_empty(day):
                days_timedelta = day_date - date
                break
        else:
            if day_date < date and not _is_day_empty(day):
                days_timedelta = date - day_date
                break
    else:
        return None

    return days_timedelta.days


def _is_day_empty(day: dict[str, any]) -> bool:
    """Check if the day schedule is empty (no lessons or all lessons are hidden)"""

    if len(day['lessons']) == 0:
        return True

    for lesson in day['lessons']:
        for period in lesson['periods']:
            if 'приховано' in period['disciplineShortName'].lower():
                return True

    return False


def _get_localized_date(ctx: ContextManager, date: _date) -> str:
    """
    Returns a localized date string

    Example:
    --------
    📅 18 трав. 2023 р. [П'ятниця] 📅
    """

    date_localized = escape_markdown(format_date(
        date, locale=ctx.chat_data.get('lang_code')), version=2)
    week_day_localized = ctx.lang.get('text.time.week_day.' + str(date.weekday()))
    full_date_localized = f"*{date_localized}* `[`*{week_day_localized}*`]`"

    return full_date_localized


def _create_schedule_section(ctx: ContextManager, day: dict) -> str:
    """
    Creates a schedule section for the schedule page

    ## Example:
    ```
    ———— 10:05 ——— 11:25 ————
      ІнМов за ПроСпр[КонсЕкз]
    2 Онлайн
      Кулаженко Олена Петрiвна +1
    ———— 12:05 ——— 13:25 ————
      "В" МатемЛогіка[КонсЕкз]
    3 Онлайн
      Котляр Валерій Юрійович
    —――—――——―—―――—―—―――――――――
    ```
    """

    schedule_section = ''

    for lesson in day['lessons']:
        for period in lesson['periods']:
            # Prevent page break on unexpected behavior
            if not period['disciplineShortName']:
                period['disciplineShortName'] = 'Unknown discipline'
            if not period['typeStr']:
                period['typeStr'] = '?'
            if not period['timeStart']:
                period['timeStart'] = '??:??'
            if not period['timeEnd']:
                period['timeEnd'] = '??:??'

            # Escape ONLY USED api result not to break telegram markdown
            # DO NOT DELETE COMMENTS
            # period['disciplineFullName'] = escape_markdown(period['disciplineFullName'], version=2)
            period['disciplineShortName'] = escape_markdown(period['disciplineShortName'], version=2)
            period['typeStr'] = escape_markdown(period['typeStr'], version=2)
            period['classroom'] = escape_markdown(period['classroom'], version=2)
            period['timeStart'] = escape_markdown(period['timeStart'], version=2)
            period['timeEnd'] = escape_markdown(period['timeEnd'], version=2)
            # period['teachersName'] = escape_markdown(period['teachersName'], version=2)
            # period['teachersNameFull'] = escape_markdown(period['teachersNameFull'], version=2)
            # period['chairName'] = escape_markdown(period['chairName'], version=2)
            # period['dateUpdated'] = escape_markdown(period['dateUpdated'], version=2)
            # period['groups'] = escape_markdown(period['groups'], version=2)

            # Get teacher name
            teacher_name = period['teachersNameFull']
            multiple_teachers = ', ' in teacher_name
            if multiple_teachers:
                teacher_name = teacher_name.split(', ')[0]
            teacher_name = escape_markdown(teacher_name, version=2)

            # Add teacher page link if teacher page is found
            teacher = _find_teacher(teacher_name)
            if teacher:
                teacher_name = f'[{teacher_name}]({teacher.page_link})'

            # If there are multiple teachers, display the first one and add +n to the end
            if multiple_teachers:
                count = str(period['teachersNameFull'].count(','))
                teacher_name += ' \\+' + count

            period['teachersNameFull'] = teacher_name

            schedule_section += ctx.lang.get('text.schedule.period').format(
                **period,
                lessonNumber=lesson['number']
            )

    schedule_section += '`—――—―``―——``―—―``――``—``―``—``――――``――``―――`'
    return schedule_section


def _check_extra_text(day: dict) -> bool:
    """Checks if the day schedule has extra text, like zoom links, etc."""

    for lesson in day['lessons']:
        for period in lesson['periods']:
            if period['extraText']:
                return True

    return False


@lru_cache(maxsize=1024)
def _find_teacher(name: str) -> Teacher | None:
    """Find teacher by name and log if not found"""

    if teacher_finder is None:
        return None

    teacher = teacher_finder.find_safe(name)

    if teacher is None:
        logger.warning(f'Could not find teacher "{name}"')

    return teacher
