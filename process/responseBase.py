import asyncio
import copy
import json
import os
from abc import ABCMeta
from abc import abstractmethod

import discord
from discord.ext import interaction


class ResponseBase(metaclass=ABCMeta):
    def __init__(self, ctx: interaction.ApplicationContext, client: interaction.Client):
        self.context = ctx
        self.client = client
        self.init_button()

    def check_component(self, original_message: discord.Message, component: interaction.ComponentsContext) -> bool:
        return (
                component.custom_id
                and component.message.id == original_message.id
                and component.channel.id == self.context.channel.id
        )

    @abstractmethod
    def init_button(self):
        pass

    @abstractmethod
    async def request_component(
            self,
            component_context: interaction.ComponentsContext | None = None,
            content: str = discord.utils.MISSING,
            embeds: list[discord.Embed] = None,
            attachments: list[discord.File] = discord.utils.MISSING,
            components: list[interaction.ActionRow] = None,
            **kwargs
    ) -> interaction.ComponentsContext | None:
        if embeds is None:
            embeds = []

        _components = [self.buttons]
        if components is not None:
            _components += components

        if component_context is None:
            message = await self.context.edit(
                content=content,
                embeds=embeds,
                attachments=attachments,
                components=_components,
            )
        else:
            message = await component_context.edit(
                content=content,
                embeds=embeds,
                attachments=attachments,
                components=_components,
            )

        try:
            context: interaction.ComponentsContext = (
                await self.client.wait_for_global_component(
                    check=lambda x: self.check_component(message, x),
                    timeout=300,
                )
            )
        except asyncio.TimeoutError:
            await self.cancel_component(
                component_context, content=content, embeds=embeds, components=components, **kwargs
            )
            return

        await context.defer_update()
        return context

    @property
    @abstractmethod
    def buttons(self) -> interaction.ActionRow:
        pass

    async def cancel_component(
            self,
            component_context: interaction.ComponentsContext | None = None,
            content: str = None,
            embeds: list[discord.Embed] = discord.utils.MISSING,
            attachments: list[discord.File] = discord.utils.MISSING,
            components: list[interaction.ActionRow] = None,
            **kwargs
    ):
        _components = [copy.copy(self.buttons)]
        for index, _ in enumerate(self.buttons.components):
            _components[0].components[index].disabled = True
            _components[0].components[index].style = 2
        if components is not None:
            _components += components

        if component_context is not None:
            await component_context.edit(
                content=content,
                embeds=embeds,
                attachments=attachments,
                components=_components,
                **kwargs
            )
        else:
            await self.context.edit(
                content=content,
                embeds=embeds,
                attachments=attachments,
                components=_components,
                **kwargs
            )
        return
