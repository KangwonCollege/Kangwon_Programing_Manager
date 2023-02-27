import discord
from discord.ext import interaction
from typing import Optional

from config.config import get_config

parser = get_config()


class Authorization:
    def __init__(self, client: interaction.Client):
        self.client = client
        self.guild: Optional[discord.Guild] = None
        self.admin_role: Optional[discord.Role] = None
        self.member_role: Optional[discord.Role] = None

        self.color = int(parser.get("Color", "default"), 16)
        self.error_color = int(parser.get("Color", "error"), 16)
        self.warning_color = int(parser.get("Color", "warning"), 16)

        self.already_ticket_opened = discord.Embed(
            title="안내",
            description="티켓이 이미 열려있습니다. 만일 티켓이 닫혀있는데, 해당 안내 문구가 나왔을 경우 디스코드 봇 관리자에게 문의해주세요.",
            color=self.warning_color
        )
        self.ticket_mode_not_found = discord.Embed(
            title="에러",
            description="티켓을 생성하는 도중 에러가 발생하였습니다. 자세한 사항은 디스코드 개발자에게 문의해주시기 바랍니다.",
            color=self.error_color
        )
        self.ticket_close_not_found = discord.Embed(
            title="안내",
            description="닫으시려는 티켓을 찾을 수 없습니다.",
            color=self.warning_color
        )
        self.ticket_process = discord.Embed(
            title="티켓",
            description="정상적으로 티켓을 열었습니다. {ticket_channel} 를 참조해주세요.",
            color=self.color
        )

    @interaction.listener()
    async def on_ready(self):
        self.guild = self.client.get_guild(
            parser.getint('DEFAULT', 'guild_id')
        )
        self.admin_role = self.guild.get_role(
            parser.getint('DEFAULT', 'admin_role_id')
        )
        self.member_role = self.guild.get_role(
            parser.getint('DEFAULT', 'member_role_id')
        )

    @interaction.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != 1079386090433163394 or message.author == self.client.user:
            return

        if self.admin_role not in getattr(message.author, "roles", []):
            return

        if message.content.startswith("!M"):
            embed = discord.Embed(color=self.color)
            embed.set_author(
                icon_url=self.client.user.avatar.url,
                name="강원대학교 인증 시스템"
            )
            embed.description = (
                "강원대학교 재학생을 증명하기 위해 아래의 3가지 옵션 중에서 한가지를 선택해주세요.\n\n"
                "\U0001F4E7 `@kangwon.ac.kr`로 구성된 이메일을 통해 재학생을 인증합니다. (작업 중)\n"
                "\U0001F310 이름과 생년월일, 학번을 통해 재학생을 인증합니다. (작업 중)\n"
                "\U0001F39F 학생증(모바일 학생증 포함)을 통해 재학생을 인증합니다. "
                "수기로 진행하기 때문에 인증까지 다소 시간이 필요합니다.\n"
            )
            channel = interaction.MessageSendable(
                channel=message.channel, state=getattr(self.client, "_connection")
            )
            await channel.send(embed=embed, components=[
                interaction.ActionRow(components=[
                    interaction.Button(
                        custom_id="authorization_button_1",
                        emoji=discord.PartialEmoji(name="\U0001F4E7"),
                        style=2
                    ),
                    interaction.Button(
                        custom_id="authorization_button_2",
                        emoji=discord.PartialEmoji(name="\U0001F310"),
                        style=2,
                        disabled=True
                    ),
                    interaction.Button(
                        custom_id="authorization_button_other",
                        emoji=discord.PartialEmoji(name="\U0001F39F"),
                        style=2
                    )
                ])
            ])
        return

    @interaction.detect_component()
    async def authorization_button_other(self, component: interaction.ComponentsContext):
        if self.member_role in component.author.roles:
            await component.send("이미 재학생 인증을 받았습니다.", hidden=True)
            return
        category_channel_id = parser.getint('Ticket', 'authorization_channel_category_id')
        category_channel: discord.CategoryChannel = component.guild.get_channel(category_channel_id)

        for ticket_open_event in self.client.extra_events.get('on_ticket_open', []):
            channel: discord.TextChannel = await ticket_open_event(
                component=component,
                category_channel=category_channel,
                ticket_id='authorization',
                title="재학생인증-{member_name}"
            )
            break
        else:
            return

        embed = discord.Embed(color=self.color)
        embed.set_author(name="강원대학교 재학생 인증", icon_url=self.client.user.avatar.url)
        embed.description = (
            "다음 방법 중 한 가지 방법을 통하여 인증합니다.\n\n"
            "1. 학번과 이름이 보이는 실물 학생증 사진을 찍어 업로드해 주세요.\n"
            "2. K-Cloud 애플리케이션에 ID-card를 캡처하여 업로드해 주세요."
        )
        sending_channel = interaction.MessageSendable(
            channel=channel,
            state=getattr(self.client, "_connection")
        )
        await sending_channel.send(embed=embed, components=[
            interaction.ActionRow(components=[
                interaction.Button(
                    custom_id="authorization_success",
                    label="인증 확인",
                    emoji=discord.PartialEmoji(name="\U00002705"),
                    style=3
                ),
                interaction.Button(
                    custom_id="authorization_ticket_close",
                    label="티켓 닫기",
                    emoji=discord.PartialEmoji(name="\U0000274C"),
                    style=2
                )
            ])
        ])
        return

    @interaction.detect_component()
    async def authorization_ticket_close(self, component: interaction.ComponentsContext):
        await component.defer()
        return self.client.dispatch('ticket_close', component=component, ticket_id='authorization')

    @interaction.detect_component()
    async def authorization_success(self, component: interaction.ComponentsContext):
        if self.admin_role not in getattr(component.author, "roles", []):
            await component.send("인증 승인은 관리자만 할 수 있습니다.", hidden=True)
            return
        await component.send("인증 승인 확인하였습니다. 역할을 부여하고, 티켓을 종료합니다.")

        for ticket_member_info_event in self.client.extra_events.get('on_ticket_member_info', []):
            author: Optional[discord.Member] = await ticket_member_info_event(component=component, ticket_id='authorization')
            if author is not None:
                await author.add_roles(self.member_role, reason="학생증 인증 성공, 역할 수동 부여")
                break
        else:
            # 사용자를 찾지 못해 역할을 부여하지 못할 경우
            await component.send("사용자 정보를 조회하지 못하여 역할을 부여하지 못했습니다.", hidden=True)
            return
        self.client.dispatch('ticket_close', component=component, ticket_id='authorization')
        return


def setup(client: interaction.Client):
    return client.add_interaction_cog(Authorization(client))
