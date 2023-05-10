import discord
from discord.ext import interaction
from typing import Optional

from config.config import get_config

parser = get_config()


class StudyEmoji:
    def __init__(self, client: interaction.Client):
        self.client = client
        self.guild: Optional[discord.Guild] = None
        self.channel_id: Optional[int] = 0

    @interaction.listener()
    async def on_ready(self):
        self.guild = self.client.get_guild(
            parser.getint('DEFAULT', 'guild_id')
        )
        self.channel_id = parser.getint('StudyEmoji', 'channel_id')

    @interaction.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        thread = self.guild.get_thread(payload.message_id)
        if thread is None:
            return

        channel_id = thread.parent_id
        member = payload.member
        if member is None:
            member = await self.guild.fetch_member(payload.user_id)

        if channel_id == self.channel_id:
            await thread.send(f"{member.mention}님이 온라인 스터디에 참여합니다!")
        return

    @interaction.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        thread = self.guild.get_thread(payload.message_id)
        if thread is None:
            return

        channel_id = thread.parent_id
        member = payload.member
        if member is None:
            member = await self.guild.fetch_member(payload.user_id)

        if channel_id != self.channel_id:
            return

        async for message in thread.history(limit=None):
            if message.author.id != self.client.user.id:
                continue

            if message.content == f"{member.mention}님이 온라인 스터디에 참여합니다!":
                await message.delete()
                break
        return


def setup(client: interaction.Client):
    return client.add_interaction_cog(StudyEmoji(client))
