import asyncio
import os
import random
import discord
import aiosmtplib
from discord.ext import interaction
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from jinja2 import Template

from config.config import get_config
from utils.directory import directory

parser = get_config()


class AuthorizationEmail:
    def __init__(self, client: interaction.Client):
        self.client = client
        self.guild: Optional[discord.Guild] = None
        self.admin_role: Optional[discord.Role] = None
        self.member_role: Optional[discord.Role] = None

        self.color = int(parser.get("Color", "default"), 16)
        self.error_color = int(parser.get("Color", "error"), 16)
        self.warning_color = int(parser.get("Color", "warning"), 16)

        self.smtp_host = parser.get("Authorization_SMTP", "smtp_host")
        self.smtp_port = parser.getint("Authorization_SMTP", "smtp_port")
        self.smtp_id = parser.get("Authorization_SMTP", "smtp_user_id")
        self.smtp_password = parser.get("Authorization_SMTP", "smtp_password")

        self.smtp_session = aiosmtplib.SMTP(
            hostname=self.smtp_host,
            port=self.smtp_port,
            use_tls=True
        )
        self.is_smtp_session_connect = False

        self.email_not_found = discord.Embed(
            title="재학생 인증 실패",
            description="이메일 주소를 조회할 수 없습니다. 관리자에게 문의해주세요.",
            color=self.error_color
        )
        self.email_success = discord.Embed(
            title="재학생 인증",
            description="{email_id}으로 이메일을 보냈습니다. `받은 메일함`을 확인해주세요.\n"
                        "\U000026A0 받은 메일함에 인증 코드가 오지 않는다면, 스팸 메일함을 확인해주세요.",
            color=self.color
        )

    async def smtp_session_connect(self):
        if self.is_smtp_session_connect:
            return
        await self.smtp_session.connect()
        self.is_smtp_session_connect = True
        self.client.loop.create_task(self.timeout_smtp_session_close())

    async def timeout_smtp_session_close(self):
        await asyncio.sleep(300)
        await self.smtp_session.quit()
        self.is_smtp_session_connect = False

    @interaction.detect_component()
    async def authorization_button_1(self, component: interaction.ComponentsContext):
        await component.modal(
            custom_id="email_authorization",
            components=[
                interaction.ActionRow(components=[
                    interaction.TextInput(
                        custom_id="authorization_email_id",
                        placeholder="홍길동@kangwon.ac.kr",
                        style=1,
                        required=True,
                        label="이메일 주소"
                    )
                ])
            ],
            title="재학생 인증 받을 이메일 주소를 입력해주세요."
        )
        return

    @interaction.listener()
    async def on_modal(self, context: interaction.ModalContext):
        if context.custom_id == "email_authorization":
            await context.defer(hidden=True)

            for component in context.components:
                if component.custom_id == "authorization_email_id":
                    email_id = component.value
                    break
            else:
                await context.edit(embed=self.email_not_found)
                return

            with open(os.path.join(directory, "assets", "verification.html"), mode='r', encoding='utf8') as file:
                tmpl1 = Template(file.read())
            with open(os.path.join(directory, "assets", "verification.txt"), mode='r', encoding='utf8') as file:
                tmpl2 = Template(file.read())

            await self.smtp_session_connect()
            await self.smtp_session.login(self.smtp_id, self.smtp_password)

            authorization_code = random.randrange()

            message = MIMEMultipart()
            message['Subject'] = "재학생 인증 코드: {authorization_code}".format(authorization_code=authorization_code)
            message['From'] = self.smtp_id + "@gmail.com"
            message['To'] = email_id

            part1 = MIMEText(tmpl1.render(
                verification_code=authorization_code,
                author=f'{context.author.name}#{context.author.discriminator}'
            ), 'html')
            part2 = MIMEText(tmpl2.render(verification_code=authorization_code), 'plain')

            message.attach(part1)
            message.attach(part2)
            await self.smtp_session.send_message(message)
            await context.edit(embed=self.email_success)
        return


def setup(client: interaction.Client):
    return client.add_interaction_cog(AuthorizationEmail(client))
