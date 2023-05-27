import asyncio
import copy
import datetime
import logging
from typing import Callable
from typing import Protocol

import discord
from discord.ext import interaction

from config.config import get_config

logger = logging.getLogger(__name__)
parser = get_config()


class UrlSupport(Protocol):
    url: str


class LoggingReceive:
    def __init__(self, bot: interaction.Client):
        self.bot = bot

        self.color = int(parser.get("Color", "default"), 16)
        self.error_color = int(parser.get("Color", "error"), 16)
        self.warning_color = int(parser.get("Color", "warning"), 16)

        self.embed = discord.Embed(title="{0} 로그", colour=self.color)
        self.guild_id = parser.getint('DEFAULT', 'guild_id')
        self.deleted_logging_channel_id = parser.getint('Logging', 'deleted_logging_channel')
        self.edited_logging_channel_id = parser.getint('Logging', 'edited_logging_channel')

        self.guild = None
        self.deleted_logging_channel = None
        self.edited_logging_channel = None

        self.deleted_logging_channel_sendable = None
        self.edited_logging_channel_sendable = None

    @interaction.listener()
    async def on_ready(self):
        self.guild: discord.Guild = self.bot.get_guild(self.guild_id)
        self.deleted_logging_channel = self.guild.get_channel(self.deleted_logging_channel_id)
        self.edited_logging_channel = self.guild.get_channel(self.edited_logging_channel_id)

        self.deleted_logging_channel_sendable = interaction.MessageSendable(
            getattr(self.bot, "_connection"),
            self.deleted_logging_channel
        )
        self.edited_logging_channel_sendable = interaction.MessageSendable(
            getattr(self.bot, "_connection"),
            self.edited_logging_channel
        )

    def attachment_name(self, attachment: discord.Attachment) -> str:
        if attachment.content_type.startswith('image'):
            file_name = "사진"
        elif attachment.content_type.startswith('audio'):
            file_name = "오디오"
        elif attachment.content_type.startswith('video'):
            file_name = "영상"
        elif attachment.content_type.startswith('text'):
            file_name = "텍스트"
        else:
            file_name = "파일"
        return self.hyperlink(file_name, attachment.url)

    @staticmethod
    def hyperlink(name: str, url: str) -> str:
        return f"[{name}]({url})"

    @staticmethod
    def timestamp(time: int | float) -> str:
        return "<t:{0}:R>".format(int(time))

    @staticmethod
    def multi_items_with_image(
            objs: list[UrlSupport],
            item_format: Callable[[UrlSupport], str],
            embed: discord.Embed,
            image_mode: bool = True
    ) -> str:
        field = []
        for obj in objs:
            field.append(item_format(obj))
            if embed.image.url is None and image_mode:
                embed.set_image(url=obj.url)
        return " ".join(field)

    @staticmethod
    def embed__author(embed: discord.Embed, author: discord.User | discord.Member):
        embed.set_author(name=embed.title, icon_url=author.avatar.url)
        embed.title = None

        embed.add_field(name="사용자", value="{0}({1})".format(author.mention, author.id), inline=False)

    @staticmethod
    def embed__content(content: str):
        # Embed field.value limits is 1024 characters.
        # But, Message Content can be over 1024 characters. (If user have nitro, it will be 4000 characters.)
        if len(content) > 1024:
            content = content[0:1020] + "..."
        return content

    def embed__time(self, embed: discord.Embed, created_at: datetime.datetime, edited_at: datetime.datetime | None):
        embed.add_field(name="보낸 날짜", value=self.timestamp(created_at.timestamp()), inline=True)
        if edited_at is not None:
            embed.add_field(name="수정 날짜", value=self.timestamp(edited_at.timestamp()), inline=True)

    async def deleted_message_item(self, message: discord.Message, original_message: discord.Message = None):
        if message.author.bot or message.author.id == self.bot.user.id:
            return

        embed = copy.copy(self.embed)
        embed.title = embed.title.format("메시지 삭제")
        self.embed__author(embed, message.author)

        if message.content is not None:
            embed.add_field(name="내용", value=self.embed__content(message.content), inline=False)

        attachment_field = self.multi_items_with_image(
            message.attachments,
            lambda attachment: self.attachment_name(attachment),
            embed
        )
        if len(attachment_field) > 0:
            embed.add_field(name="파일", value=" ".join(attachment_field), inline=False)

        stickers_field = self.multi_items_with_image(
            message.stickers,
            lambda stickers: self.hyperlink(stickers.name, stickers.url),
            embed
        )
        if len(attachment_field) > 0:
            embed.add_field(name="파일", value=" ".join(attachment_field), inline=False)

        if len(stickers_field) > 0:
            embed.add_field(name="스티커", value=" ".join(stickers_field), inline=False)
        self.embed__time(embed, message.created_at, message.edited_at)
        if original_message is None:
            original_message = await self.deleted_logging_channel_sendable.send(embed=embed)
        else:
            original_message = await original_message.edit(embed=embed)
        return original_message

    @staticmethod
    def bulk_message_selection(messages: list[discord.Message]) -> list[interaction.ActionRow]:
        return [
            interaction.ActionRow(components=[
                interaction.Selection(custom_id="deleted_message_selection", options=[
                    interaction.Options(
                        label="종합 대시보드",
                        value="dashboard"
                    )
                ] + [
                    interaction.Options(
                        label=f"{index + 1}번째, {str(message.author)}의 메시지",
                        value=f"{index}_message",
                    ) for index, message in enumerate(messages[0:50])
                    if not message.author.bot
                ], min_values=1, max_values=1)
            ])
        ]

    async def deleted_message_total(self, messages: list[discord.Message], original_message: discord.Message = None):
        embed = copy.copy(self.embed)
        embed.title = embed.title.format("\U0001F5D2 메시지 대량 삭제")

        author_fields = []
        bot_member_field = []
        for message in messages:
            if message.author.bot and message.author not in bot_member_field:
                bot_member_field.append(message.author)
                continue

            if message.author.mention not in author_fields:
                author_fields.append(message.author.mention)

        author_list_comment = ""
        for index, author_message in enumerate(author_fields):
            if len(author_list_comment + author_message + f" 외 {len(author_fields) - index}명") > 1024:
                author_list_comment += f" 외 {len(author_fields) - index}명"
                break
            author_list_comment += ", " + author_message

        embed.add_field(
            name="삭제된 메시지 (봇 / 사용자)",
            value=f"{len(messages)}개 ({len(bot_member_field)}명/{len(author_fields) - len(bot_member_field)}명)",
            inline=False
        )
        embed.add_field(name="사용자 목록", value=author_list_comment.lstrip(", "), inline=False)

        components = self.bulk_message_selection(messages)

        if original_message is None:
            original_message = await self.deleted_logging_channel_sendable.send(embed=embed, components=components)
        else:
            original_message = await original_message.edit(embed=embed)
        return original_message

    @interaction.listener()
    async def on_message_delete(self, message: discord.Message):
        if (
                message.channel.id == self.deleted_logging_channel_id or
                message.channel.id == self.edited_logging_channel_id
        ):
            return
        await self.deleted_message_item(message, None)
        return

    @interaction.listener()
    async def on_bulk_message_delete(self, messages: list[discord.Message]):
        if len(messages) <= 0:
            return

        if (
                messages[0].channel.id == self.deleted_logging_channel_id or
                messages[0].channel.id == self.edited_logging_channel_id
        ):
            return

        response_component_id = "dashboard"
        original_message = None
        while True:
            if response_component_id == "dashboard":
                original_message = await self.deleted_message_total(messages, original_message)
            elif response_component_id.endswith('_message'):
                index_message = response_component_id.rstrip('_message')
                original_message = await self.deleted_message_item(messages[int(index_message) - 1], original_message)
            else:
                break

            try:
                component_response: interaction.ComponentsContext = await self.bot.wait_for_component(
                    custom_id='deleted_message_selection',
                    check=(
                        lambda x: x.message.id == original_message.id and
                                  x.component_type == interaction.Selection.TYPE
                    ), timeout=300
                )
                await component_response.defer_update()
            except asyncio.TimeoutError:
                try:
                    _components = self.bulk_message_selection(messages)
                    _components[0].components[0].disabled = True
                    editable = interaction.MessageEditable(original_message.channel, original_message.id)
                    await editable.edit(embeds=original_message.embeds, components=_components)
                except discord.NotFound:
                    pass
                break
            else:
                response_component_id = component_response.values[0]
        return

    @staticmethod
    def multi_items_before_and_after(before_field: str, after_field: str, title: str, embed: discord.Embed):
        if len(before_field) <= 0:
            embed.add_field(
                name=title,
                value=(
                        f"{title} 없음 ▶ " +
                        " ".join(after_field)
                ), inline=False
            )
        elif len(after_field) <= 0:
            embed.add_field(
                name=title,
                value=(
                        " ".join(before_field) +
                        f" ▶ {title} 삭제됨"
                ), inline=False
            )
        else:
            embed.add_field(
                name=title,
                value=(
                        " ".join(before_field) +
                        " ▶ " +
                        " ".join(after_field)
                ), inline=False
            )

    @interaction.listener()
    async def on_message_edit(self, before_message: discord.Message, after_message: discord.Message | None):
        if before_message.author.bot or before_message.author.id == self.bot.user.id or after_message is None:
            return

        if (
                before_message.channel.id == self.deleted_logging_channel_id or
                before_message.channel.id == self.edited_logging_channel_id
        ):
            return

        embed = copy.copy(self.embed)
        embed.title = embed.title.format("메시지 수정")
        self.embed__author(embed, before_message.author)

        if before_message.content is not None:
            embed.add_field(name="원본 내용", value=self.embed__content(before_message.content), inline=True)
        else:
            embed.add_field(name="원본 내용", value="내용 없음.", inline=False)

        if after_message.content is not None:
            embed.add_field(name="수정 내용", value=self.embed__content(before_message.content), inline=True)
        else:
            embed.add_field(name="원본 내용", value="내용 삭제됨.", inline=False)
        embed.add_field(name="메시지 위치", value="[링크]({0})".format(after_message.jump_url), inline=True)

        if len(before_message.attachments) > 0 or len(before_message.attachments) > 0:
            before_attachment_field = self.multi_items_with_image(
                before_message.attachments,
                lambda attachment: self.attachment_name(attachment),
                embed, False
            )
            after_attachment_field = self.multi_items_with_image(
                after_message.attachments,
                lambda attachment: self.attachment_name(attachment),
                embed, False
            )
            self.multi_items_before_and_after(before_attachment_field, after_attachment_field, "파일", embed)

        if len(before_message.stickers) > 0 or len(before_message.stickers) > 0:
            before_stickers_field = self.multi_items_with_image(
                before_message.stickers,
                lambda stickers: self.hyperlink(stickers.name, stickers.url),
                embed, False
            )
            after_stickers_field = self.multi_items_with_image(
                after_message.stickers,
                lambda stickers: self.hyperlink(stickers.name, stickers.url),
                embed, False
            )
            self.multi_items_before_and_after(before_stickers_field, after_stickers_field, "스티커", embed)

        self.embed__time(embed, before_message.created_at, after_message.edited_at)
        await self.edited_logging_channel_sendable.send(embed=embed)
        return


def setup(client: interaction.Client):
    return client.add_interaction_cog(LoggingReceive(client))
