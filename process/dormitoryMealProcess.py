import datetime
import discord
from discord.ext import interaction

from config.config import get_config
from modules.meal.dormitoryMeal import DormitoryMeal
from modules.meal.schoolMeal import SchoolMeal
from modules.meal.mealResponse import MealResponse
from process.processBase import ProcessBase
from utils.weekday import weekday

parser = get_config()


class DormitoryMealProcess(ProcessBase):
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
            building: str,
            component_context: interaction.ComponentsContext = None,
            **kwargs
    ):
        await self.context.defer()
        data = await self.dormitory_client.meal(date)
        dormitory_types = {
            "새롬관": "BTL1",
            "이롬관": "BTL2"
        }
        meal_info = getattr(data, dormitory_types[building], MealResponse())

        embed = discord.Embed(
            title="\U0001F371 기숙사 급식",
            description=f"{date}일자, {building} 식단표 입니다.",
            color=self.color,
        )

        embed.add_field(name="아침", value="\n".join(meal_info.breakfast), inline=True)
        embed.add_field(name="점심", value="\n".join(meal_info.lunch), inline=True)
        embed.add_field(name="저녁", value="\n".join(meal_info.dinner), inline=True)

        self.init_button()
        self.breakfast_button.style = 2
        self.breakfast_button.disabled = True
        self.breakfast_button.style = 2
        self.lunch_button.disabled = True
        self.breakfast_button.style = 2
        self.dinner_button.disabled = True

        meal_time_parent = self.meal_time[dormitory_types[building]]
        weekday_response = weekday(date)
        if weekday_response.Saturday == date:
            meal_time = meal_time_parent.weekend_saturday
        elif weekday_response.Sunday == date:
            meal_time = meal_time_parent.weekend_sunday
        else:
            meal_time = meal_time_parent.weekday

        if datetime.datetime.now().time() < meal_time.breakfast:
            self.breakfast_button.style = 4
        elif datetime.datetime.now().time() < meal_time.lunch:
            self.lunch_button.style = 4
        elif datetime.datetime.now().time() < meal_time.dinner:
            self.dinner_button.style = 4

        component = await self.request_component(component_context, embeds=[embed])
        return
