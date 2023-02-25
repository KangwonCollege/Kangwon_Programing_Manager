
import datetime
import discord
from discord.ext import interaction

from config.config import get_config

parser = get_config()


class General:
    def __init__(self, bot):
        self.client: discord.AutoShardedClient = bot

        self.color = int(parser.get("Color", "default"), 16)
        self.error_color = int(parser.get("Color", "error"), 16)
        self.warning_color = int(parser.get("Color", "warning"), 16)

    @interaction.command(description='강원대학교 디스코드 봇의 핑(상태)을 확인합니다.')
    async def ping(self, ctx: interaction.ApplicationContext):
        datetime_now_for_read = datetime.datetime.now(tz=datetime.timezone.utc)
        response_ping_r = ctx.created_at - datetime_now_for_read
        response_ping_read = abs(round(response_ping_r.total_seconds() * 1000))
        first_latency = round(self.client.latency * 1000, 2)
        embed = discord.Embed(
            title="Pong!",
            description=f"클라이언트 핑상태: {first_latency}ms\n응답속도(읽기): {round(response_ping_read / 1000, 2)}ms",
            color=self.color)
        msg = await ctx.send(embed=embed)
        datetime_now_for_write = datetime.datetime.now(tz=datetime.timezone.utc)
        response_ping_w = datetime_now_for_write - msg.created_at
        response_ping_write = abs(round(response_ping_w.total_seconds() * 1000))
        embed = discord.Embed(
            title="Pong!",
            description=f"클라이언트 핑상태: {first_latency}ms\n"
                        f"응답속도(읽기/쓰기): {round(response_ping_read / 1000, 2)}ms/{round(response_ping_write / 1000, 2)}ms",
            color=self.color)
        await msg.edit(embed=embed)
        return


def setup(client: interaction.Client):
    return client.add_interaction_cog(General(client))
