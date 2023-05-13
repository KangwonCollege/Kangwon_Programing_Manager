

class MealResponse:
    def __init__(self):
        self.breakfast: list[str] | None = None
        self.lunch: list[str] | None = None
        self.dinner: list[str] | None = None
