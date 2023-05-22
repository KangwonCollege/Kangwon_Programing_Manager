import datetime
from abc import ABCMeta
from abc import abstractmethod

import discord
from discord.ext import interaction

from modules.meal.dormitoryMeal import DormitoryMeal
from modules.meal.schoolMeal import SchoolMeal
from modules.meal.schoolMealType import SchoolMealType
from process.responseBase import ResponseBase
from utils.find_enum import find_enum


class ProcessBase(ResponseBase, metaclass=ABCMeta):
    def __init__(
            self,
            ctx: interaction.ApplicationContext,
            client: interaction.Client,
            dormitory_client: DormitoryMeal = None,
            school_client: SchoolMeal = None,
            **kwargs
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

        self.dormitory_client = dormitory_client
        if self.dormitory_client is None:
            self.dormitory_client = DormitoryMeal(loop=self.client.loop)
        self.school_client = school_client
        if self.school_client is None:
            self.school_client = SchoolMeal(loop=self.client.loop)

        self.dormitory_process = kwargs.get('dormitory_process')
        self.school_process = kwargs.get('school_process')

    @property
    def building_selection(self):
        return interaction.ActionRow(components=[
            interaction.Selection(
                custom_id="building_selection",
                options=[
                    interaction.Options(label="새롬관", value="새롬관"),
                    interaction.Options(label="이룸관", value="이룸관"),
                    interaction.Options(label="천지관", value=SchoolMealType.CheonJi.value),
                    interaction.Options(label="백록관", value=SchoolMealType.BaekNok.value),
                    interaction.Options(label="두리관", value=SchoolMealType.Duri.value),
                ],
                min_values=1,
                max_values=1
            )
        ])

    def check_component(self, original_message: discord.Message, component: interaction.ComponentsContext) -> bool:
        return (
                super().check_component(original_message, component) and
                component.custom_id in [
                    t.custom_id for t in (self.buttons.components + self.building_selection.components)
                ]
        )

    async def request_component(
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
        return await super(ProcessBase, self).request_component(
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

    @abstractmethod
    async def content(
            self,
            date: datetime.date,
            building: str | SchoolMealType,
            component_context: interaction.ComponentsContext = None,
            **kwargs
    ):
        pass

    async def response_component(
            self,
            component: interaction.ComponentsContext,
            date: datetime.date,
            building: str | SchoolMealType,
            **kwargs
    ):
        if component.custom_id in [
            x.custom_id for x in self.building_selection.components
        ] and component.type == interaction.Selection.TYPE:
            if component.values[0] in ["새롬관", "이룸관"]:
                return await self.dormitory_process.content(
                    date=date,
                    building=component.values[0],
                    component_context=component,
                    **kwargs
                )
            elif component.values[0] in [
                SchoolMealType.CheonJi.value,
                SchoolMealType.BaekNok.value,
                SchoolMealType.Duri.value
            ]:
                _building = find_enum(SchoolMealType, component.values[0])
                return await self.school_process.content(
                    date=date,
                    building=_building,
                    component_context=component,
                    **kwargs
                )
            return

        if component.custom_id == self.left_button.custom_id:
            return await self.content(
                date=(date + datetime.timedelta(days=-1)),
                building=building,
                component_context=component,
                **kwargs
            )
        elif component.custom_id == self.right_button.custom_id:
            return await self.content(
                date=(date + datetime.timedelta(days=1)),
                building=building,
                component_context=component,
                **kwargs
            )
        elif component.custom_id == self.breakfast_button.custom_id:
            kwargs.pop('meal_type')
            return await self.content(
                date=date,
                building=building,
                component_context=component,
                meal_type="breakfast",
                **kwargs
            )
        elif component.custom_id == self.lunch_button.custom_id:
            kwargs.pop('meal_type')
            return await self.content(
                date=date,
                building=building,
                component_context=component,
                meal_type="lunch",
                **kwargs
            )
        elif component.custom_id == self.dinner_button.custom_id:
            kwargs.pop('meal_type')
            return await self.content(
                date=date,
                building=building,
                component_context=component,
                meal_type="dinner",
                **kwargs
            )
        return
