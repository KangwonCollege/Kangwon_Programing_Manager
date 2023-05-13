import datetime

from typing import NamedTuple


class WeekDayResponse(NamedTuple):
    Monday: datetime.date
    Sunday: datetime.date


def weekday(date: datetime.date) -> WeekDayResponse:
    monday_date = date + datetime.timedelta(days=date.weekday())
    sunday_date = monday_date + datetime.timedelta(days=7)
    return WeekDayResponse(monday_date, sunday_date)
