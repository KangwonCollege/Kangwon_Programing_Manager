import datetime

import discord
from discord.ext import interaction

from modules.dormitoryMeal import DormitoryMeal
from modules.schoolMeal import SchoolMeal
from process.processBase import ProcessBase


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
        await super(DormitoryMeal, self).response_component(component_context, content, embeds, attachments, **kwargs)
        return

    async def content(self, date: datetime.date):
        data = await self.dormitory_client.meal(date)
        embed = discord.Embed()
        return
