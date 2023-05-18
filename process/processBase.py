from abc import ABCMeta

import discord
from discord.ext import interaction
from modules.meal import SchoolMealType
from process.responseBase import ResponseBase


class ProcessBase(ResponseBase, metaclass=ABCMeta):
    def __init__(
            self,
            ctx: interaction.ApplicationContext,
            client: interaction.Client
    ):
        super(ProcessBase, self).__init__(
            ctx=ctx, client=client
        )
        self.left_button: interaction.Button | None = None
        self.breakfast_button: interaction.Button | None = None
        self.lunch_button: interaction.Button | None = None
        self.dinner_button: interaction.Button | None = None
        self.right_button: interaction.Button | None = None
        self.init_button()

    @property
    def building_selection(self):
        return interaction.ActionRow(components=[
            interaction.Selection(
                custom_id="building_selection",
                options=[
                    interaction.Options(label="새롬관", value="dormitory_btl1"),
                    interaction.Options(label="이룸관", value="dormitory_btl2"),
                    interaction.Options(label="천지관", value=SchoolMealType.CheonJi.value()),
                    interaction.Options(label="백록관", value=SchoolMealType.BaekNok.value()),
                    interaction.Options(label="두리관", value=SchoolMealType.Duri.value()),
                ]
            )
        ])

    async def response_component(
            self,
            component_context: interaction.ComponentsContext | None = None,
            content: str = discord.utils.MISSING,
            embeds: list[discord.Embed] = None,
            attachments: list[discord.File] = discord.utils.MISSING,
            components: list[interaction.ActionRow] = None,
            **kwargs
    ) -> interaction.ComponentsContext | None:
        _components = [self.building_selection]
        if components is not None:
            _components += components
        return await super(ProcessBase, self).response_component(
            component_context,
            content,
            embeds,
            attachments,
            _components,
            **kwargs
        )

    def init_button(self):
        self.left_button = interaction.Button(
            custom_id="left_arrow_button",
            emoji=discord.PartialEmoji(name="\U00002B05"),
            style=1,
        )
        self.right_button = interaction.Button(
            custom_id="right_arrow_button",
            emoji=discord.PartialEmoji(name="\U000027A1"),
            style=1,
        )
        self.breakfast_button = interaction.Button(
            custom_id="breakfast_button",
            emoji=discord.PartialEmoji(name="\U0001F307"),
            style=1,
        )
        self.lunch_button = interaction.Button(
            custom_id="lunch_button",
            emoji=discord.PartialEmoji(name="\U0001F3D9"),
            style=1,
        )
        self.dinner_button = interaction.Button(
            custom_id="dinner_button",
            emoji=discord.PartialEmoji(name="\U0001F303"),
            style=1,
        )

    @property
    def buttons(self) -> interaction.ActionRow:
        return interaction.ActionRow(
            components=[
                self.left_button,
                self.breakfast_button,
                self.lunch_button,
                self.dinner_button,
                self.right_button,
            ]
        )
