import datetime

import asyncio
from bs4 import BeautifulSoup

from modules.baseMeal import BaseMeal
from modules.mealResponse import MealResponse
from modules.schoolMealType import SchoolMealType
from utils.weekday import weekday


class SchoolMeal(BaseMeal):
    def __init__(self, loop: asyncio.BaseEventLoop):
        super(SchoolMeal, self).__init__(loop)

        self.data: dict[
            SchoolMealType,
            dict[
                datetime.date, dict[
                    str, MealResponse | None
                ]
            ]
        ] = {
            building: dict() for building in list(SchoolMealType)
        }

    async def meal(self, building: SchoolMealType, date: datetime.date = None) -> dict[str, MealResponse]:
        if building not in self.data:
            self.data[building] = dict()

        if date not in self.data[building]:
            await self.update(building, date)
        return self.data[building][date]

    async def update(self, building: SchoolMealType, date: datetime.date = None):
        if date is None:
            date = datetime.date.today()

        weekday_response = weekday(date)
        params = {
            "sc1": building.value,
            "sc5": (weekday_response.Monday + datetime.timedelta(days=-1)).strftime("%Y%m%d")
        }
        response = await self.requests.post(
            "https://wwwk.kangwon.ac.kr/www/selecttnCafMenuListWU.do",
            raise_on=True,
            params=params
        )
        soup = BeautifulSoup(response.data, 'html.parser')

        for br in soup.find_all("br"):
            br.replace_with("\n")

        body = soup.find("main", {"class": "colgroup"}).find("div", {"id": "contents"})
        table = body.find('div', {"class": "over_scroll_table"}).find('table')
        tbody = table.find('tbody')

        restaurant_name = None
        restaurant_name_max_key = 0
        for index, value in enumerate(tbody.find_all("tr")):
            if index >= restaurant_name_max_key:
                restaurant_name = None

            if restaurant_name is None:
                restaurant_name_tag = value.find('th', {"scope": "rowgroup"})
                restaurant_name = restaurant_name_tag.text
                restaurant_name_max_key = index + int(restaurant_name_tag.get("rowspan", 1))
            meal_type = value.find('th', {"rowspan": None}).text
            for j, meal_info in enumerate(tbody.find_all("td")):
                meal_date = weekday_response.Monday + datetime.timedelta(days=j)
                if meal_date not in self.data[building]:
                    self.data[building][meal_date] = dict()

                if restaurant_name not in self.data[building][meal_date]:
                    self.data[building][meal_date][restaurant_name] = MealResponse()

                if meal_type == "아침":
                    self.data[building][meal_date][restaurant_name].breakfast = meal_info.text.split('\n')
                elif meal_type == "점심":
                    self.data[building][meal_date][restaurant_name].lunch = meal_info.text.split('\n')
                elif meal_type == "저녁":
                    self.data[building][meal_date][restaurant_name].dinner = meal_info.text.split('\n')
                