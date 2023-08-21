# pylint: disable=too-many-public-methods,missing-function-docstring,
# pylint: disable=too-many-arguments,line-too-long,keyword-arg-before-vararg

"""
API module for mkr.org.ua

API docs can be found at https://mkr.org.ua/portal-api-docs.html
"""

import logging
from typing import List
from datetime import datetime, date as _date
from urllib.parse import urljoin

import pytz
import requests
from requests_cache import CachedSession

logger = logging.getLogger(__name__)
logger.info('Initializing api module')


class Api:
    """API wrapper for mkr.org.ua"""

    VERSION = '1.6.1'
    DEFAULT_LANGUAGE = 'uk'

    def __init__(self, url: str, timeout: int = None) -> None:
        """Creates an instance of the API wrapper
        
        :param url: URL of the API (see https://mkr.org.ua/api/v2/university/list)
        :param timeout: Timeout for requests (in seconds)
        """
        logger.info('Creating Api instance with url %s', url)

        self.url = url
        self.timeout = timeout
        self.session = requests.Session()

    def _make_request(self, path: str, method: str = 'GET',
                      json: dict = None, *req_args, **req_kwargs) -> requests.Response:

        self.session.headers.update({
            'Content-Type': 'application/json; charset=utf-8',
            'Accept-Language': req_kwargs.pop('language', self.DEFAULT_LANGUAGE),
        })

        res = self.session.request(
            method=method,
            url=urljoin(self.url, path),
            json=json,
            timeout=self.timeout,
            *req_args, **req_kwargs
        )

        res.raise_for_status()
        return res

    # /time-table
    def timetable_group(self, group_id: int, date_start: _date | str,
                        date_end: _date | str | None = None,
                        *req_args, **req_kwargs) -> List[dict]:
        """Returns the schedule for the group"""

        if isinstance(date_start, _date):
            date_start = date_start.isoformat()
        if date_end is None:
            date_end = date_start
        elif isinstance(date_end, _date):
            date_end = date_end.isoformat()

        return self._make_request('/time-table/group', 'POST', json={
            'groupId': group_id,
            'dateStart': date_start,
            'dateEnd': date_end
        }, *req_args, **req_kwargs).json()

    def timetable_student(self, student_id: int, date_start: _date | str,
                          date_end: _date | str | None = None,
                          *req_args, **req_kwargs) -> List[dict]:
        """Returns the schedule for the student"""

        if isinstance(date_start, _date):
            date_start = date_start.isoformat()
        if date_end is None:
            date_end = date_start
        elif isinstance(date_end, _date):
            date_end = date_end.isoformat()

        return self._make_request('/time-table/student', 'POST', json={
            'studentId': student_id,
            'dateStart': date_start,
            'dateEnd': date_end
        }, *req_args, **req_kwargs).json()

    def timetable_teacher(self, teacher_id: int, date_start: _date | str,
                          date_end: _date | str | None = None,
                          *req_args, **req_kwargs) -> List[dict]:
        """Returns the schedule for the teacher"""

        if isinstance(date_start, _date):
            date_start = date_start.isoformat()
        if date_end is None:
            date_end = date_start
        elif isinstance(date_end, _date):
            date_end = date_end.isoformat()

        return self._make_request('/time-table/teacher', 'POST', json={
            'teacherId': teacher_id,
            'dateStart': date_start,
            'dateEnd': date_end
        }, *req_args, **req_kwargs).json()

    def timetable_classroom(self, classroom_id: int, date_start: _date | str,
                            date_end: _date | str | None = None,
                            *req_args, **req_kwargs) -> List[dict]:
        """Returns audience schedule (when and what groups are in it)"""

        if isinstance(date_start, _date):
            date_start = date_start.isoformat()
        if date_end is None:
            date_end = date_start
        elif isinstance(date_end, _date):
            date_end = date_end.isoformat()

        return self._make_request('/time-table/classroom', 'POST', json={
            'classroomId': classroom_id,
            'dateStart': date_start.isoformat(),
            'dateEnd': date_end.isoformat()
        }, *req_args, **req_kwargs).json()

    def timetable_call_schedule(self, *req_args, **req_kwargs) -> List[dict]:
        """Returns the call schedule"""
        return self._make_request('/time-table/call-schedule', 'POST',
            *req_args, **req_kwargs).json()

    def timetable_ad(self, class_code: int, date: _date | str, *req_args, **req_kwargs) -> dict:
        """Returns an announcement for the current lesson\n
        Usually contains a lesson link in Teams/Zoom"""

        if isinstance(date, _date):
            date = date.isoformat()

        return self._make_request('/time-table/schedule-ad', 'POST', json={
            'r1': class_code,
            'r2': date
        }, *req_args, **req_kwargs).json()

    def timetable_free_classrooms(self, structure_id: int, corpus_id: int,
                                  lesson_number_start: int, lesson_number_end: int,
                                  date: datetime | str, *req_args, **req_kwargs) -> List[dict]:
        """Returns list of free classrooms
        Date format: `2023-02-23T10:26:00.000Z` or `datetime.datetime`"""

        if isinstance(date, datetime):
            date = date.astimezone(pytz.UTC).isoformat(sep='T', timespec='milliseconds') + 'Z'

        return self._make_request('/time-table/free-classroom', 'POST', json={
            'structureId': structure_id,
            'corpusId': corpus_id,
            'lessonNumberStart': lesson_number_start,
            'lessonNumberEnd': lesson_number_end,
            'date': date
        }, *req_args, **req_kwargs).json()

    # /list
    def list_structures(self, *req_args, **req_kwargs) -> List[dict]:
        """Returns list of structures"""
        return self._make_request('/list/structures', *req_args, **req_kwargs).json()

    def list_faculties(self, structure_id: int, *req_args, **req_kwargs) -> List[dict]:
        """Returns list of faculties"""
        return self._make_request('/list/faculties', 'POST', json={
            'structureId': structure_id
        }, *req_args, **req_kwargs).json()

    def list_courses(self, faculty_id: int, *req_args, **req_kwargs) -> List[dict]:
        """Returns list of courses"""
        return self._make_request('/list/courses', 'POST', json={
            'facultyId': faculty_id
        }, *req_args, **req_kwargs).json()

    def list_groups(self, faculty_id: int, course: int, *req_args, **req_kwargs) -> List[dict]:
        """Return list of groups"""
        return self._make_request('/list/groups', 'POST', json={
            'facultyId': faculty_id,
            'course': course
        }, *req_args, **req_kwargs).json()

    def list_chairs(self, structure_id: int, faculty_id: int,
                    *req_args, **req_kwargs) -> List[dict]:
        """Returns list of chairs"""
        return self._make_request('/list/chairs', 'POST', json={
            'structureId': structure_id,
            'facultyId': faculty_id
        }, *req_args, **req_kwargs).json()

    def list_teachers_by_chair(self, chair_id: int, *req_args, **req_kwargs) -> List[dict]:
        """Returns a list of teachers from the given chair"""
        return self._make_request('/list/teachers-by-chair', 'POST', json={
            'chairId': chair_id
        }, *req_args, **req_kwargs).json()

    def list_students_by_group(self, group_id: int, *req_args, **req_kwargs) -> List[dict]:
        """Returns a list of students from the given group"""
        return self._make_request('/list/students-by-group', 'POST', json={
            'groupId': group_id
        }, *req_args, **req_kwargs).json()

    # /other
    def search_teacher(self, name: str, *req_args, **req_kwargs) -> List[dict]:
        """Looking for a teacher by a fragment of his last name only\n
        Not case sensitive, returns an array of the first 50 teachers found"""
        return self._make_request('/other/search-teachers', 'POST', json={
            'name': name
        }, *req_args, **req_kwargs).json()

    # General
    def icon(self, *req_args, **req_kwargs) -> bytes:
        """Returns the university logo"""
        return self._make_request('/icon', *req_args, **req_kwargs).content

    def version(self, *req_args, **req_kwargs) -> dict:
        """Returns the version of the API"""
        return self._make_request('/version', *req_args, **req_kwargs).json()

    # Not implemented
    def timetable_universal(self, date: _date | str, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def user_info2(self, id_: int, *req_args, **req_kwargs) -> dict:
        raise NotImplementedError

    def user_info(self, *req_args, **req_kwargs) -> dict:
        raise NotImplementedError

    def user_change_password(self, password: str, new_password: str,
                             *req_args, **req_kwargs) -> None:
        raise NotImplementedError

    def user_change_password2(self, id_: int, new_password: str,
                              *req_args, **req_kwargs) -> None:
        raise NotImplementedError

    def user_delete(self, id_: int, *req_args, **req_kwargs) -> None:
        raise NotImplementedError

    def user_update2(self, id_: int, blocked: int, username: str,
                     email: str, *req_args, **req_kwargs) -> None:
        raise NotImplementedError

    def user_update(self, username: str, email: str, *req_args, **req_kwargs) -> None:
        raise NotImplementedError

    def user_create(self, id_: int, type_: int, username: str,
                    email: str, password: str, *req_args, **req_kwargs) -> dict:
        raise NotImplementedError

    def user_search_student(self, code: int, birthday: _date | str,
                            type_: int, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def user_search_teacher(self, inn: str, birthday: _date | str,
                            *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def user_change_account(self, type_: int, id_: int, *req_args, **req_kwargs) -> None:
        raise NotImplementedError

    def user_change_account2(self, id_: int, type_: int, new_id: int,
                             *req_args, **req_kwargs) -> None:
        raise NotImplementedError

    def inquiry_types(self, faculty_id: int, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def journal_student(self, year: int, semester: int, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def journal_full_discipline_journal(self, discipline_id: int, type_: int, year: int, semester: int, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def student_semester_list(self, only_active: bool, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def student_info(self, *req_args, **req_kwargs) -> dict:
        raise NotImplementedError

    def student_search_by_email(self, email: str, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def student_search(self, last_name: str, faculty_id: int, speciality_full_name: str, course: int, group_name: str, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def docs_get_new_docs(self, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def docs_mark_docs_as_read(self, docs: List[int], *req_args, **req_kwargs) -> None:
        raise NotImplementedError

    def docs_get_docs_on_control(self, count_days: int, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def org_dols(self, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def org_structures(self, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def org_faculties(self, structure_id: int, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def org_chairs(self, structure_id: int, faculty_id: int, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def org_teacher_identifiers(self, last_id: int, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def org_chair_info(self, chair_ids: List[int], *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def org_group_info(self, group_ids: List[int], *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def org_students(self, last_id: int, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def org_teachers(self, last_id: int, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def org_set_external_ids(self, external_ids: List[dict], *req_args, **req_kwargs) -> dict:
        raise NotImplementedError

    def login(self, username: str, password: str, app_key: str, *req_args, **req_kwargs) -> dict:
        raise NotImplementedError

    def auth_data(self, username: str, password: str, key: str, *req_args, **req_kwargs) -> dict:
        raise NotImplementedError

    def academ_disciplines(self, last_id: int, year: int, semester: int, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def academ_learning_plans(self, discipline_ids: List[int], year: int, semester: int, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def exam_sheets(self, year: int, semester: int, education_discipline_id: int, group_id: int, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def exam_statement_list(self, year: int, semester: int, education_discipline_id: int, group_id: int, *req_args, **req_kwargs) -> List[dict]:
        raise NotImplementedError

    def exam_set_date_enter(self, sheet_id: int, date_enter: _date | str, *req_args, **req_kwargs) -> None:
        raise NotImplementedError

    def exam_close(self, sheet_id: int, *req_args, **req_kwargs) -> None:
        raise NotImplementedError

    def exam_set_marks(self, sheet_id: int, marks: List[dict], *req_args, **req_kwargs) -> None:
        raise NotImplementedError


class CachedApi(Api):
    """API wrapper for mkr.org.ua with caching enabled"""

    def __init__(self, url: str, timeout: int = None, **cache_kwargs):
        super().__init__(url=url, timeout=timeout)

        self.session = CachedSession(
            cache_control=True,
            allowable_methods=['GET', 'POST'],
            match_headers=True,
            stale_if_error=True,
            **cache_kwargs
        )
