import datetime

import discord
from discord.ext import interaction

from config.config import get_config
from modules.meal.dormitoryMeal import DormitoryMeal
from modules.meal.mealResponse import MealResponse
from modules.meal.schoolMeal import SchoolMeal
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
            building: str,
            component_context: interaction.ComponentsContext = None,
            **kwargs
    ):
        data = await self.school_client.meal(date)
        dormitory_types = {
            "CC10": "천지관",
            "CC20": "백록관",
            "CC30": "두리관"
        }
        meal_info = getattr(data, dormitory_types[building], MealResponse())

        embed = discord.Embed(
            title="\U0001F371 학생 식당",
            description=f"{date}일자, {building} 식단표 입니다.",
            color=self.color,
        )

        embed.add_field(name="아침", value="\n".join(meal_info.breakfast), inline=True)
        embed.add_field(name="점심", value="\n".join(meal_info.lunch), inline=True)
        embed.add_field(name="저녁", value="\n".join(meal_info.dinner), inline=True)

        self.init_button()
        self.breakfast_button.style = 2
        self.breakfast_button.disabled = True
        self.lunch_button.style = 2
        self.lunch_button.disabled = True
        self.dinner_button.style = 2
        self.dinner_button.disabled = True

        meal_time = self.meal_time_initialization(date, dormitory_types[building])
        self.meal_button(meal_time)
        embed.set_footer(text=self.meal_footer(meal_time))

        component = await self.request_component(component_context, embeds=[embed])
        await self.response_component(component, date, building, **kwargs)
        return
