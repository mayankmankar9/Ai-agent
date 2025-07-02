from typing import Literal
from pydantic import BaseModel
from langchain.tools import StructuredTool

class TDEEInput(BaseModel):
    gender: Literal["male", "female"]
    age: int
    weight_kg: float
    height_cm: float
    activity_level: Literal["sedentary", "light", "moderate", "active", "very active"]

def calculate_tdee(gender: str, age: int, weight_kg: float, height_cm: float, activity_level: str) -> str:
    # Mifflin-St Jeor BMR formula
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + (5 if gender == "male" else -161)

    # TDEE multipliers
    multiplier = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very active": 1.9
    }[activity_level]

    tdee = bmr * multiplier
    return f"BMR: {bmr:.1f} kcal/day\nTDEE: {tdee:.1f} kcal/day"

tdee_calculator_tool = StructuredTool.from_function(
    func=calculate_tdee,
    name="TDEECalculatorTool",
    description="Estimate BMR and TDEE using weight, height, age, gender, and activity level.",
    args_schema=TDEEInput
)
