import discord
import os
import json
from discord.ext import interaction
from typing import Optional

from config.config import get_config
from utils.directory import directory

parser = get_config()


class Ticket:
    def __init__(self, client: interaction.Client):
        self.client = client
        self.guild: Optional[discord.Guild] = None

        self.color = int(parser.get("Color", "default"), 16)
        self.error_color = int(parser.get("Color", "error"), 16)
        self.warning_color = int(parser.get("Color", "warning"), 16)

        self.already_ticket_opened = discord.Embed(
            title="안내",
            description="티켓이 이미 열려있습니다. 만약 열린 티켓이 없는 경우, 관리자에게 문의해주세요.",
            color=self.warning_color
        )
        self.ticket_mode_not_found = discord.Embed(
            title="에러",
            description="티켓을 생성하는 도중 에러가 발생하였습니다. 자세한 사항은 디스코드 개발자에게 문의해주시기 바랍니다.",
            color=self.error_color
        )
        self.ticket_close_not_found = discord.Embed(
            title="안내",
            description="닫으려는 티켓을 찾을 수 없습니다.",
            color=self.warning_color
        )

        self.already_ticket_opened.description += "\n```WARNING CODE: TICKET-ALREADY-OPENED(01)\n```"
        self.ticket_close_not_found.description += "```\nWARNING CODE: TICKET-NOT-FOUND\n```"
        self.ticket_mode_not_found.description += "```\nERROR CODE: TICKET-MODE-NOT-FOUND\n"

        self.ticket = {}
        with open(os.path.join(directory, "data", "ticket.json"), "r", encoding='utf-8') as file:
            self.ticket = json.load(fp=file)

    @staticmethod
    def conversion_template(name: str, guild: discord.Guild, member: discord.Member):
        return name.format(
            guild=guild.name,
            guild_id=guild.id,
            member=str(member),
            member_name=member.name,
            member_tag=member.discriminator,
            member_id=member.id
        )

    def ticket_save(self):
        with open(os.path.join(directory, "data", "ticket.json"), "w", encoding='utf-8') as file:
            json.dump(self.ticket, fp=file, indent=4)

    @interaction.listener()
    async def on_ticket_open(
            self,
            component: interaction.ComponentsContext,
            category_channel: discord.CategoryChannel,
            ticket_id: str = "ticket",
            title: str = "티켓-{member_name}"
    ) -> Optional[discord.TextChannel]:
        await component.defer(hidden=True)
        if component.author.id in [x.get('author', 0) for x in self.ticket.get(ticket_id, [])]:
            await component.edit(embed=self.already_ticket_opened)
            return
        ticket_channel = await category_channel.create_text_channel(
            name=self.conversion_template(title, component.guild, component.author),
            overwrites={
                self.client.user: discord.PermissionOverwrite(
                    read_message_history=True,
                    send_messages=True,
                    embed_links=True,
                    attach_files=True,
                    add_reactions=True,
                    view_channel=True
                ),
                component.author: discord.PermissionOverwrite(
                    read_message_history=True,
                    send_messages=True,
                    attach_files=True,
                    add_reactions=True,
                    view_channel=True
                ),
                component.guild.default_role: discord.PermissionOverwrite(
                    read_message_history=False,
                    send_messages=False,
                    view_channel=False
                )
            }
        )
        await component.edit(
            content="정상적으로 티켓을 열었습니다. {ticket_channel} 를 확인해주세요.".format(
                ticket_channel=ticket_channel.mention
            )
        )

        if ticket_id not in self.ticket:
            self.ticket[ticket_id] = []

        self.ticket[ticket_id].append({
            "channel": ticket_channel.id,
            "guild": component.guild.id,
            "author": component.author.id
        })
        self.ticket_save()
        return ticket_channel

    @interaction.listener()
    async def on_ticket_member_info(
            self,
            component: interaction.ComponentsContext,
            ticket_id: str = 'ticket'
    ) -> Optional[discord.Member]:
        for ticket in self.ticket.get(ticket_id, []):
            if ticket.get('channel', 0) == component.channel.id:
                author = ticket.get('author', 0)
                break
        else:
            return
        return component.guild.get_member(author)

    @interaction.listener()
    async def on_ticket_close(
            self,
            component: interaction.ComponentsContext,
            ticket_id: str = 'ticket'
    ):
        guild = component.guild
        for _data in self.ticket.get(ticket_id, []):
            if _data.get("channel") == component.channel.id:
                ticket = _data
                break
        else:
            await component.send(
                embed=self.ticket_close_not_found,
                hidden=True
            )
            return

        if guild is None:
            guild = self.client.get_guild(ticket.get("guild"))
        author = guild.get_member(ticket.get("author"))
        channel: discord.TextChannel = guild.get_channel(ticket.get("channel"))

        await channel.delete()
        position = self.ticket.get(ticket_id, []).index(ticket)
        self.ticket.get(ticket_id, []).pop(position)
        self.ticket_save()
        return


def setup(client: interaction.Client):
    return client.add_interaction_cog(Ticket(client))
