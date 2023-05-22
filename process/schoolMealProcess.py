import datetime

import discord
from discord.ext import interaction

from config.config import get_config
from modules.meal.dormitoryMeal import DormitoryMeal
from modules.meal.mealResponse import MealResponse
from modules.meal.schoolMeal import SchoolMeal
from modules.meal.schoolMealType import SchoolMealType
from process.mealTimeProcess import MealTimeProcess

parser = get_config()


class SchoolMealProcess(MealTimeProcess):
    def __init__(
            self,
            ctx: interaction.ApplicationContext,
            client: interaction.Client,
            dormitory_client: DormitoryMeal = None,
            school_client: SchoolMeal = None,
            **kwargs
    ):
        super(SchoolMealProcess, self).__init__(
            ctx,
            client,
            dormitory_client,
            school_client,
            dormitory_process=kwargs.get('dormitory_process'),
            school_process=self
        )
        self.context = ctx
        self.client = client

        self.color = int(parser.get("Color", "default"), 16)
        self.error_color = int(parser.get("Color", "error"), 16)
        self.warning_color = int(parser.get("Color", "warning"), 16)

    async def content(
            self,
            date: datetime.date,
            building: SchoolMealType,
            component_context: interaction.ComponentsContext = None,
            meal_type: str | None = None,
            **kwargs
    ):
        meal_time = self.meal_time_initialization(date, building.value)
        now_time = datetime.datetime.now().time()

        # if now_time < self.meal_time_safe(meal_time, "breakfast"):
        #     self.breakfast_button.style = 4
        if meal_type is None or self._optional_safe(meal_time, meal_type, None) is None:
            if now_time < self.meal_time_safe(meal_time, "lunch"):
                meal_type = "lunch"
            elif now_time < self.meal_time_safe(meal_time, "dinner"):
                meal_type = "dinner"
            else:
                meal_type = "breakfast"
        data = await self.school_client.meal(building, date)
        school_types = {
            SchoolMealType.CheonJi: "천지관",
            SchoolMealType.BaekNok: "백록관",
            SchoolMealType.Duri: "두리관"
        }
        # meal_info = getattr(data, dormitory_types[building], MealResponse())

        embed = discord.Embed(
            title="\U0001F371 학생 식당",
            description=f"{date}일자, {school_types[building]} 식단표 입니다.",
            color=self.color,
        )

        unknown_restaurant_count = 0
        for restaurant_name, meal_data in data.items():
            if getattr(meal_data, meal_type, None) is None:
                # embed.add_field(name=restaurant_name, value="알 수 없음.", inline=True)
                unknown_restaurant_count += 1
                continue
            embed.add_field(name=restaurant_name, value="\n".join(getattr(meal_data, meal_type)), inline=True)

        if (
                self._optional_safe(meal_time, "breakfast", None) is None and
                self._optional_safe(meal_time, "lunch", None) is None and
                self._optional_safe(meal_time, "dinner", None) is None
        ):
            embed.description += "\n\n해당 일자에는 학생 식당을 운영하지 않습니다."
        elif len(data) == unknown_restaurant_count:
            embed.description += "\n\n해당 일자의 식단 정보가 존재하지 않습니다."

        self.init_button()
        if self._optional_safe(meal_time, "breakfast", None) is None:
            self.breakfast_button.style = 2
            self.breakfast_button.disabled = True
        if self._optional_safe(meal_time, "lunch", None) is None:
            self.lunch_button.style = 2
            self.lunch_button.disabled = True
        if self._optional_safe(meal_time, "dinner", None) is None:
            self.dinner_button.style = 2
            self.dinner_button.disabled = True

        self.meal_button(meal_time)
        embed.set_footer(text=self.meal_footer(meal_time))

        # current button
        if meal_type == 'breakfast':
            self.breakfast_button.style = 3
            self.breakfast_button.disabled = True
        elif meal_type == 'lunch':
            self.lunch_button.style = 3
            self.lunch_button.disabled = True
        elif meal_type == 'dinner':
            self.dinner_button.style = 3
            self.dinner_button.disabled = True

        component = await self.request_component(component_context, embeds=[embed])
        if component is not None:
            await self.response_component(component, date, building, meal_type=meal_type, **kwargs)
        return
