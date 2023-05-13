from typing import NamedTuple
from modules.mealResponse import MealResponse


class DormitoryResponse(NamedTuple):
    general: MealResponse = MealResponse()
    BTL1: MealResponse = MealResponse()
    BTL2: MealResponse = MealResponse()
