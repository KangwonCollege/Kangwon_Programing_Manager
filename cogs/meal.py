import datetime

import discord
from discord.ext import interaction

from config.config import get_config
from modules.meal.schoolMealType import SchoolMealType
from process.dormitoryMealProcess import DormitoryMealProcess
from process.schoolMealProcess import SchoolMealProcess
from utils.find_enum import find_enum

parser = get_config()


class Meal:
    def __init__(self, client: discord.Client):
        self.client = client

    @interaction.command(name="긱식", description="기숙사 식당의 식단표를 불러옵니다.")
    @interaction.option(name="건물", choices=[
        interaction.CommandOptionChoice("새롬관", "새롬관"),
        interaction.CommandOptionChoice("이룸관", "이룸관"),
    ])
    async def dormitory_meal(self, ctx: interaction.ApplicationContext, building: str):
        await ctx.defer()
        client = DormitoryMealProcess(
            ctx=ctx,
            client=self.client,
            school_process=SchoolMealProcess(ctx, self.client)
        )
        client.school_process.dormitory_process = client
        await client.content(
            date=datetime.date.today(),
            building=building
        )
        return

    @interaction.command(name="학식", description="학생 식당의 식단표를 불러옵니다.")
    @interaction.option(name="건물", choices=[
        interaction.CommandOptionChoice("천지관", "CC10"),
        interaction.CommandOptionChoice("백록관", "CC20"),
        interaction.CommandOptionChoice("두리관", "CC30"),
    ])
    async def student_meal(self, ctx: interaction.ApplicationContext, building: str):
        await ctx.defer()
        client = SchoolMealProcess(
            ctx=ctx,
            client=self.client,
            dormitory_process=DormitoryMealProcess(ctx, self.client)
        )
        client.dormitory_process.school_process = client
        _building = find_enum(SchoolMealType, building)
        await client.content(
            date=datetime.date.today(),
            building=_building
        )
        return


def setup(client: interaction.Client):
    return client.add_interaction_cog(Meal(client))