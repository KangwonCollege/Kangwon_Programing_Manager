import datetime
import logging
import os
import random
import re
import copy
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Union

import aiosmtplib
import asyncio
import discord
from discord.ext import interaction
from jinja2 import Template

from config.config import get_config
from utils.directory import directory

parser = get_config()
logger = logging.getLogger(__name__)


class AuthorizationEmail:
    def __init__(self, client: interaction.Client):
        self.client = client
        self.guild: Optional[discord.Guild] = None

        self.color = int(parser.get("Color", "default"), 16)
        self.error_color = int(parser.get("Color", "error"), 16)
        self.warning_color = int(parser.get("Color", "warning"), 16)

        self.smtp_host = parser.get("Authorization_SMTP", "smtp_host")
        self.smtp_port = parser.getint("Authorization_SMTP", "smtp_port")
        self.smtp_id = parser.get("Authorization_SMTP", "smtp_user_id")
        self.smtp_password = parser.get("Authorization_SMTP", "smtp_password")

        self.email_verification_code = {}

        self.smtp_session = aiosmtplib.SMTP(
            hostname=self.smtp_host,
            port=self.smtp_port,
            use_tls=True
        )
        self.is_smtp_session_connect = False
        self.is_smtp_session_login = False

        self.email_not_found = discord.Embed(
            title="재학생 인증 실패",
            description="이메일 주소를 조회할 수 없습니다. 관리자에게 문의해주세요.",
            color=self.error_color
        )
        self.verification_code_not_found = discord.Embed(
            title="재학생 인증 실패",
            description="인증 코드를 조회할 수 없습니다. 관리자에게 문의해주세요.",
            color=self.error_color
        )
        self.email_request_not_found = discord.Embed(
            title="재학생 인증 실패",
            description="재학생 인증 세션을 찾을 수 없습니다. 다시 시도해주세요.",
            color=self.error_color
        )

        self.email_request_timeout = discord.Embed(
            title="재학생 인증",
            description="1분 이내에 이메일 인증을 이미 진행했습니다. 잠시 후에 다시 시도해주세요.",
            color=self.warning_color
        )
        self.email_refresh_timeout = discord.Embed(
            title="재학생 인증",
            description="인증 코드 재발송은 30초에 한 번씩 시도할 수 있습니다. 잠시만 기다려주세요.",
            color=self.warning_color
        )
        self.email_forbidden = discord.Embed(
            title="재학생 인증 실패",
            description="kangwon.ac.kr로 구성된 이메일을 통하여 검증할 수 있습니다.",
            color=self.warning_color
        )
        self.email_value_exception = discord.Embed(
            title="재학생 인증 실패",
            description="이메일을 전송하기 위한 값이 잘못되었습니다. 관리자에게 문의하세요.",
            color=self.error_color
        )
        self.email_response_exception = discord.Embed(
            title="재학생 인증 실패",
            description="이메일 발송이 거부되었습니다. 이메일 주소를 확인하시고 다시 요청해주세요.\n발송한 이메일 주소: {email_id}",
            color=self.warning_color
        )
        self.email_recipients_refused = discord.Embed(
            title="재학생 인증 실패",
            description="이메일 주소가 잘못되었습니다. 이메일 주소를 확인해주세요.\n발송한 이메일 주소: {email_id}",
            color=self.warning_color
        )
        self.bad_verification_code = discord.Embed(
            title="재학생 인증 실패",
            description="인증 코드가 다릅니다. 다시 시도해주세요.",
            color=self.warning_color
        )
        self.too_many_bad_verification_code = discord.Embed(
            title="재학생 인증 실패",
            description="인증 코드 실패 횟수(3회)를 초과했습니다. 다시 시도해주세요.",
            color=self.warning_color
        )
        self.email_success = discord.Embed(
            title="재학생 인증",
            description="{email_id}으로 이메일을 보냈습니다. `받은 메일함`을 확인해주세요.\n"
                        "이메일 인증코드를 확인하신 후, 아래의 \U0001F512 버튼을 눌러 인증코드를 입력해 재학생 인증을 진행하세요.\n\n"
                        "\U000026A0 받은 메일함에 인증 코드가 오지 않는다면, 스팸 메일함을 확인해주세요.\n"
                        "\U0001F4E7를 눌러 이메일 인증을 다시 받으실 수 있습니다.",
            color=self.color
        )
        self.email_resent_success = discord.Embed(
            title="재학생 인증",
            description="{email_id}으로 재발송하였습니다. `받은 메일함`을 확인해주세요.\n"
                        "이메일 인증코드를 확인하신 후, 아래의 \U0001F512 버튼을 눌러 인증코드를 입력해 재학생 인증을 진행하세요.\n\n"
                        "\U000026A0 받은 메일함에 인증 코드가 오지 않는다면, 스팸 메일함을 확인해주세요.\n"
                        "\U0001F4E7를 눌러 이메일 인증을 다시 받으실 수 있습니다.",
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
        self.is_smtp_session_login = False
        self.is_smtp_session_connect = False

    @interaction.detect_component()
    async def authorization_button_1(self, component: interaction.ComponentsContext):
        if parser.getint('DEFAULT', 'member_role_id') in [x.id for x in component.author.roles]:
            await component.send("이미 재학생 인증을 받았습니다.", hidden=True)
            return

        if component.author.id in self.email_verification_code:
            created_at = self.email_verification_code[component.author.id]["created_at"]
            last_created_total_second = abs((datetime.datetime.now() - created_at).total_seconds())
            if last_created_total_second < 60:
                await component.send(embed=self.email_request_timeout)
                return
            else:
                self.email_verification_code.pop(component.author.id)

        await component.modal(
            custom_id="email_authorization_request",
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

    async def _send_email(
            self,
            context: Union[interaction.ModalContext, interaction.ComponentsContext],
            email_id: str,
            refresh: bool = False
    ) -> Optional[str]:
        with open(os.path.join(directory, "assets", "verification.html"), mode='r', encoding='utf8') as file:
            tmpl1 = Template(file.read())
        with open(os.path.join(directory, "assets", "verification.txt"), mode='r', encoding='utf8') as file:
            tmpl2 = Template(file.read())

        await self.smtp_session_connect()
        if not self.is_smtp_session_login:
            await self.smtp_session.login(self.smtp_id, self.smtp_password)
            self.is_smtp_session_login = True

        authorization_code = str(random.randint(0, 999999)).zfill(6)

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
        try:
            await self.smtp_session.send_message(message)
        except ValueError:
            embed = copy.copy(self.email_value_exception)
            embed.description = self.email_value_exception.description.format(
                email_id=email_id
            )
            await context.edit(embed=embed)
            return
        except aiosmtplib.SMTPResponseException:
            embed = copy.copy(self.email_value_exception)
            embed.description = self.email_response_exception.description.format(
                email_id=email_id
            )
            await context.edit(embed=embed)
            return
        except aiosmtplib.SMTPRecipientsRefused:
            embed = copy.copy(self.email_value_exception)
            embed.description = self.email_recipients_refused.description.format(
                email_id=email_id
            )
            await context.edit(embed=embed)
            return

        if context.author.id not in self.email_verification_code:
            self.email_verification_code[context.author.id] = {
                "verification_code": authorization_code,
                "email_id": email_id,
                "created_at": datetime.datetime.now(),
                "last_sent": datetime.datetime.now(),
                "failed_count": 0
            }
            logging.info("이메일 발송: {} / 인증 코드: {}".format(email_id, authorization_code))
        else:
            self.email_verification_code[context.author.id]["last_sent"] = datetime.datetime.now()
            self.email_verification_code[context.author.id]["verification_code"] = authorization_code
            logging.info("이메일 재발송: {} / 인증 코드: {}".format(email_id, authorization_code))

        if refresh:
            # self.email_resent_success.description = self.email_resent_success.description.format(email_id=email_id)
            embed = copy.copy(self.email_resent_success)
            embed.description = self.email_resent_success.description.format(email_id=email_id)
        else:
            # self.email_success.description = self.email_success.description.format(email_id=email_id)
            embed = copy.copy(self.email_success)
            embed.description = self.email_success.description.format(email_id=email_id)

        await context.edit(
            embed=embed,
            components=[
                interaction.ActionRow(components=[
                    interaction.Button(
                        custom_id="email_verification_button",
                        emoji=discord.PartialEmoji(name="\U0001F512"),
                        style=2
                    ),
                    interaction.Button(
                        custom_id="refresh_verification_button",
                        emoji=discord.PartialEmoji(name="\U0001F4E7"),
                        style=2
                    )
                ])
            ]
        )
        return authorization_code

    @interaction.listener()
    async def on_modal(self, context: interaction.ModalContext):
        if context.custom_id == "email_authorization_request":
            await context.defer(hidden=True)

            for component in context.components:
                if component.custom_id == "authorization_email_id":
                    email_id = component.value
                    break
            else:
                await context.edit(embed=self.email_not_found)
                return

            regex = "^[a-zA-Z0-9.+_-]+@kangwon.ac.kr"
            if not bool(re.match(regex, email_id)):
                await context.edit(embed=self.email_forbidden)
                return

            await self._send_email(context, email_id)
        elif context.custom_id == "email_authorization_response":
            for component in context.components:
                if component.custom_id == "verification_code":
                    verification_code = component.value
                    break
            else:
                await context.send(embed=self.verification_code_not_found)
                return

            data = self.email_verification_code.get(context.author.id)
            logging.info("{} 인증 시도(시도/정답): {}/{}".format(
                data["email_id"], data["verification_code"], verification_code
            ))
            if data["verification_code"] == verification_code:
                self.email_verification_code.pop(context.author.id)
                await context.send("재학생 인증이 완료되었습니다. 역할을 부여합니다.", hidden=True)
                self.client.dispatch(
                    'grant_permission_author',
                    author=context.author,
                    reason=f"{data['email_id']} 학생증 인증 성공, 역할 자동 부여"
                )
                return
            else:
                if self.email_verification_code[context.author.id]['failed_count'] >= 3:
                    await context.send(embed=self.too_many_bad_verification_code, hidden=True)
                    self.email_verification_code.pop(context.author.id)
                    return
                self.email_verification_code[context.author.id]['failed_count'] += 1
                await context.send(embed=self.bad_verification_code, hidden=True)
        return

    @interaction.detect_component()
    async def refresh_verification_button(self, component: interaction.ComponentsContext):
        if component.author.id not in self.email_verification_code:
            await component.send(embed=self.email_request_not_found, hidden=True)
            return

        last_sent_delta = datetime.datetime.now() - self.email_verification_code[component.author.id]['last_sent']
        if last_sent_delta.total_seconds() < 30:
            await component.send(embed=self.email_refresh_timeout, hidden=True)
            return
        email_id = self.email_verification_code[component.author.id]['email_id']
        await component.defer(hidden=True)
        await self._send_email(component, email_id, True)
        return

    @interaction.detect_component()
    async def email_verification_button(self, component: interaction.ComponentsContext):
        if component.author.id not in self.email_verification_code:
            await component.send(embed=self.email_request_not_found, hidden=True)
            return
        await component.modal(
            custom_id="email_authorization_response",
            components=[
                interaction.ActionRow(components=[
                    interaction.TextInput(
                        custom_id="verification_code",
                        placeholder="012345",
                        style=1,
                        required=True,
                        label="인증 코드",
                        min_length=6,
                        max_length=6
                    )
                ])
            ],
            title="이메일에 받은 인증코드(6자리)를 입력해주세요."
        )
        return


def setup(client: interaction.Client):
    return client.add_interaction_cog(AuthorizationEmail(client))
