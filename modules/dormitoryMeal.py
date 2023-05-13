import datetime

import asyncio
from bs4 import BeautifulSoup

from modules.baseMeal import BaseMeal
from modules.dormitoryResponse import DormitoryResponse

from utils.dict_to_form import dict_to_form
from utils.weekday import weekday


class DormitoryMeal(BaseMeal):
    def __init__(self, loop: asyncio.BaseEventLoop):
        super(DormitoryMeal, self).__init__(loop)

        self.data: dict[datetime.date, DormitoryResponse | None] = dict()

    async def meal(self, date: datetime.date = None) -> DormitoryResponse:
        if date not in self.data:
            await self.update(date)
        return self.data[date]

    async def update(self, date: datetime.date = None):
        weekday_response = weekday(
            date if date is not None
            else datetime.date.today()
        )
        if date is None:
            response = await self.requests.get(
                "https://knudorm.kangwon.ac.kr/content/K11",
                raise_on=True
            )
        else:
            form = {
                "mode": "7301000",
                "bil": 1
            }

            if datetime.date.today() < date:
                form.update({
                    "next": "Y",
                    "before": "",
                })
                form_date = date + datetime.timedelta(days=-7)
            else:
                form.update({
                    "next": "",
                    "before": "Y",
                })
                form_date = date + datetime.timedelta(days=7)

            form_weekday_response = weekday(form_date)
            form.update({
                "monDay": form_weekday_response.Monday.strftime("%Y-%m-%d"),
                "sunDay": form_weekday_response.Sunday.strftime("%Y-%m-%d"),
            })
            form_data = dict_to_form(form)

            response = await self.requests.post(
                "https://knudorm.kangwon.ac.kr/content/K11",
                raise_on=True,
                data=form_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
        soup = BeautifulSoup(response.data, 'html.parser')
        body = soup.find("form", {"class": "fm"}).find("div", {"class": "tab-content"})

        dormitory_type = {
            "general": "latest01",  # 재정생활관
            "BTL1": "latest02",  # 새롬관(제1 BTL 기숙사)
            "BTL2": "latest03"  # 이롬관(제2 BTL 기숙사)
        }
        for index, (key, value) in enumerate(dormitory_type.items()):
            dormitory_body = body.find("div", {"class": "tab-pane", "id": value})
            meal = dormitory_body.find_all("tr")  # 1번(월요일) ~ 7번(일요일)
            for j, meal_info in enumerate(meal):
                meal_date = weekday_response.Monday + datetime.timedelta(days=j)
                if self.data not in meal_date:
                    self.data[meal_date] = DormitoryResponse()
                else:
                    setattr(self.data[meal_date], key, meal_info.text)
        return self.data
