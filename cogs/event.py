
import logging

import discord
from discord.ext.interaction import listener
from discord.ext.interaction import ApplicationContext
from discord.ext.interaction import Client

logger = logging.getLogger(__name__)
logger_command = logging.getLogger(__name__ + ".command")
logger_guild = logging.getLogger(__name__ + ".guild")


class Events:
    def __init__(self, bot: Client):
        self.bot = bot

    @listener()
    async def on_ready(self):
        logger.info(f"디스코드 봇 로그인이 완료되었습니다.")
        logger.info(f"디스코드봇 이름: {self.bot.user.name}")
        logger.info(f"디스코드봇 ID: {str(self.bot.user.id)}")
        logger.info(f"디스코드봇 버전: {discord.__version__}")
        print("------------")
        answer = ""

        total = 0
        for index, guild in enumerate(self.bot.guilds):
            answer += f"{index+1}번째: {guild.name} ({guild.id}): {guild.member_count}명\n"
            total += guild.member_count
        logger.info(f"방목록: \n{answer}\n방의 종합 멤버:{total}명")

    @listener()
    async def on_guild_join(self, guild):
        server_number = None
        for i in self.bot.guilds:
            if i.name == guild.name:
                server_number = self.bot.guilds.index(i) + 1
        if server_number is not None:
            logger_guild.info(
                guild.name + '에 가입이 확인되었습니다. 서버번호: ' + str(server_number) + '번, 서버멤버' + str(guild.member_count) + '명')
        return

    @listener()
    async def on_guild_remove(self, guild):
        logger_guild.info(guild.name + '로 부터 추방 혹은 차단되었습니다.')
        return

    @listener()
    async def on_interaction_command(self, ctx: ApplicationContext):
        if ctx.guild is not None:
            logger_command.info(f"({ctx.guild} | {ctx.channel} | {ctx.author}) {ctx.content}")
        else:
            logger_command.info(f"(DM채널 | {ctx.author}) {ctx.content}")


def setup(client: Client):
    client.add_interaction_cog(Events(client))
