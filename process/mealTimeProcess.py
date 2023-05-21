import datetime
import json
import os
from abc import ABCMeta
from typing import Any

from discord.ext import interaction

from modules.meal.dormitoryMeal import DormitoryMeal
from modules.meal.schoolMeal import SchoolMeal
from modules.mealTimeModel import MealType
from modules.mealTimeModel import OperatingTime
from modules.mealTimeModel import Week
from process.processBase import ProcessBase
from utils.directory import directory
from utils.weekday import weekday


class MealTimeProcess(ProcessBase, metaclass=ABCMeta):
    def __init__(
            self,
            ctx: interaction.ApplicationContext,
            client: interaction.Client,
            dormitory_client: DormitoryMeal = None,
            school_client: SchoolMeal = None,
            **kwargs
    ):
        super(MealTimeProcess, self).__init__(
            ctx,
            client,
            dormitory_client,
            school_client,
            dormitory_process=kwargs.get('dormitory_process'),
            school_process=kwargs.get('school_process')
        )

        with open(os.path.join(directory, "data", "meal_time.json")) as file:
            self.meal_time_json = json.load(file)

        self.meal_time = dict()
        for key, value in self.meal_time_json.items():
            self.meal_time[key] = Week(**{
                week_key: MealType(**{
                    operating_key: OperatingTime(**operating_value)
                    for operating_key, operating_value in meal_type_info.items() if operating_value is not None
                }) for week_key, meal_type_info in value.items() if meal_type_info is not None
            })
        self.meal_time_now = None
        return

    @staticmethod
    def _optional_safe(obj: Any, key: str, default: Any = None):
        return (
            getattr(obj, key) if getattr(obj, key, None) is not None
            else default
        )

    def meal_time_safe(self, meal_time: MealType, meal_type: str):
        return self._optional_safe(meal_time, meal_type, datetime.time())

    @staticmethod
    def _separate_meal_week(date: datetime.date, meal_time_parent: Week) -> MealType | None:
        weekday_response = weekday(date)
        if weekday_response.Saturday == date:
            meal_time = meal_time_parent.weekend_saturday
        elif weekday_response.Sunday == date:
            meal_time = meal_time_parent.weekend_sunday
        else:
            meal_time = meal_time_parent.weekday
        return meal_time

    def meal_time_initialization(self, date: datetime.date, building: str):
        meal_time_parent = self.meal_time[building]
        self.meal_time_now = meal_time = self._separate_meal_week(date, meal_time_parent)
        return meal_time

    def meal_button(self, meal_time: MealType | None = None):
        if meal_time is None:
            meal_time = self.meal_time_now

        now_time = datetime.datetime.now().time()
        if now_time < self.meal_time_safe(meal_time, "breakfast"):
            self.breakfast_button.style = 4
        elif now_time < self.meal_time_safe(meal_time, "lunch"):
            self.lunch_button.style = 4
        elif now_time < self.meal_time_safe(meal_time, "dinner"):
            self.dinner_button.style = 4

    def meal_footer(self, meal_time: MealType | None = None) -> str | None:
        if meal_time is None:
            meal_time = self.meal_time_now

        now_time = datetime.datetime.now().time()
        if now_time <= self.meal_time_safe(meal_time, "breakfast"):  # meal.breakfast will not None
            return (
                f"아침: {meal_time.breakfast.start_hours}시 {meal_time.breakfast.start_minutes}분"
                f" ~ {meal_time.breakfast.end_hours}시 {meal_time.breakfast.end_minutes}분"
            )
        elif now_time <= self.meal_time_safe(meal_time, "lunch"):
            return (
                f"점심: {meal_time.lunch.start_hours}시 {meal_time.lunch.start_minutes}분"
                f" ~ {meal_time.lunch.end_hours}시 {meal_time.lunch.end_minutes}분"
            )
        elif now_time <= self.meal_time_safe(meal_time, "dinner"):
            return (
                f"점심: {meal_time.dinner.start_hours}시 {meal_time.dinner.start_minutes}분"
                f" ~ {meal_time.dinner.end_hours}시 {meal_time.dinner.end_minutes}분"
            )
        elif now_time > self.meal_time_safe(meal_time, "dinner"):
            return "운영 종료"
        return "알 수 없음"
