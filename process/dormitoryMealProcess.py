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


class DormitoryMealProcess(MealTimeProcess):
    def __init__(
            self,
            ctx: interaction.ApplicationContext,
            client: interaction.Client,
            dormitory_client: DormitoryMeal = None,
            school_client: SchoolMeal = None,
            **kwargs
    ):
        super(DormitoryMealProcess, self).__init__(
            ctx,
            client,
            dormitory_client,
            school_client,
            dormitory_process=self,
            school_process=kwargs.get('school_process')
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
            **kwargs
    ):
        data = await self.dormitory_client.meal(date)
        dormitory_types = {
            "새롬관": "BTL1",
            "이룸관": "BTL2"
        }
        meal_info = getattr(data, dormitory_types[building], MealResponse())

        embed = discord.Embed(
            title="\U0001F371 기숙사 급식",
            description=f"{date}일자, {building} 식단표 입니다.",
            color=self.color,
        )

        self.init_button()
        meal_time = self.meal_time_initialization(date, building.value())
        self.meal_button(meal_time)
        embed.set_footer(text=self.meal_footer(meal_time))

        component = await self.request_component(component_context, embeds=[embed])
        await self.response_component(component, date, building, **kwargs)
        return
