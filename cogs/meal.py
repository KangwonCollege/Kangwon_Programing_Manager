import datetime

import discord
from discord.ext import interaction

from config.config import get_config
from process.dormitoryMealProcess import DormitoryMealProcess
from process.schoolMealProcess import SchoolMealProcess

parser = get_config()


class Meal:
    def __init__(self, client: discord.Client):
        self.client = client

    @interaction.command(name="학식")
    @interaction.option(name="건물", choices=[
        interaction.CommandOptionChoice("천지관", "CC10"),
        interaction.CommandOptionChoice("백록관", "CC20"),
        interaction.CommandOptionChoice("두리관", "CC30")
    ])
    async def school_meal(self, ctx: interaction.ApplicationContext, building: str):
        return

    @interaction.command(name="긱식")
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
        await client.content(
            date=datetime.date.today(),
            building=building
        )
        return


def setup(client: interaction.Client):
    return client.add_interaction_cog(Meal(client))