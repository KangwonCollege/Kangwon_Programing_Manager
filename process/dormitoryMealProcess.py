import datetime

import discord
from discord.ext import interaction

from config.config import get_config
from modules.dormitoryMeal import DormitoryMeal
from modules.schoolMeal import SchoolMeal
from process.processBase import ProcessBase

parser = get_config()


class DormitoryMealProcess(ProcessBase):
    def __init__(
            self,
            ctx: interaction.ApplicationContext,
            client: interaction.Client,
            dormitory_client: DormitoryMeal,
            school_client: SchoolMeal = None,
    ):
        self.context = ctx
        self.client = client

        self.color = int(parser.get("Color", "default"), 16)
        self.error_color = int(parser.get("Color", "error"), 16)
        self.warning_color = int(parser.get("Color", "warning"), 16)

        self.dormitory_client = dormitory_client
        if self.dormitory_client is None:
            self.dormitory_client = DormitoryMeal(loop=self.client.loop)
        self.school_client = school_client

    async def response_component(
            self,
            component_context: interaction.ComponentsContext | None = None,
            content: str = discord.utils.MISSING,
            embeds: list[discord.Embed] = None,
            attachments: list[discord.File] = discord.utils.MISSING,
            **kwargs
    ) -> interaction.ComponentsContext | None:
        await super(DormitoryMealProcess, self).response_component(component_context, content, embeds, attachments, **kwargs)
        return

    async def content(self, date: datetime.date):
        data = await self.dormitory_client.meal(date)
        mbed = discord.Embed(
            title="\U0001F371 기숙사 급식",
            description=f"{date}일자, 새롬관 식단표 입니다.",
            color=self.color,
        )
        return
