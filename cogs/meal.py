import discord
from discord.ext import interaction
from typing import Optional

from config.config import get_config

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
        interaction.CommandOptionChoice("새롬관", "CC10"),
        interaction.CommandOptionChoice("이롬관", "CC20"),
    ])
    async def dormitory_meal(self, ctx: interaction.ApplicationContext, building: str):
        return


def setup(client: interaction.Client):
    return client.add_interaction_cog(Meal(client))