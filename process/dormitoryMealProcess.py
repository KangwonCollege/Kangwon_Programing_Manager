import datetime

import discord
from discord.ext import interaction

from config.config import get_config
from modules.meal.dormitoryMeal import DormitoryMeal
from modules.meal.mealResponse import MealResponse
from modules.meal.schoolMeal import SchoolMeal
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

    @staticmethod
    def add_field_meal_info(meal_info: list[str] | None, meal_type: str, embed: discord.Embed) -> discord.Embed:
        if meal_info is not None:
            embed.add_field(name=meal_type, value="\n".join(meal_info), inline=True)
        else:
            embed.add_field(name=meal_type, value="정보 없음.", inline=True)
        return embed

    async def content(
            self,
            date: datetime.date,
            building: str,
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

        if meal_info.breakfast is None and meal_info.lunch is None and meal_info.dinner is None:
            embed.description += "\n\n해당 일자의 식단 정보가 존재하지 않습니다."
        else:
            embed = self.add_field_meal_info(meal_info.breakfast, "아침", embed)
            embed = self.add_field_meal_info(meal_info.lunch, "점심", embed)
            embed = self.add_field_meal_info(meal_info.dinner, "저녁", embed)

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
        if component is not None:
            await self.response_component(component, date, building, **kwargs)
        return
