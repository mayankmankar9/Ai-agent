import requests
from langchain.tools import StructuredTool
from pydantic import BaseModel

class CalorieInput(BaseModel):
    food: str

def estimate_calorie(food: str) -> str:
    headers = {
        "x-app-id": "a8fb31d6",        # 🔁 Replace with your real app ID
        "x-app-key": "36c96c77ec3226683518e485f9c3a9c3",      # 🔁 Replace with your real app key
        "Content-Type": "application/json"
    }
    url = "https://trackapi.nutritionix.com/v2/natural/nutrients"

    # 🔍 Clean food description to avoid vague GPT responses
    cleaned_food = food.split("→")[0].strip("- ").strip()

    response = requests.post(url, headers=headers, json={"query": cleaned_food})
    if response.status_code != 200 or not response.json().get("foods"):
        return "Not found"

    result = response.json()["foods"][0]
    return (
        f"**{result['food_name'].title()}**\n"
        f"Calories: {result['nf_calories']}\n"
        f"Protein: {result['nf_protein']}\n"
        f"Carbs: {result['nf_total_carbohydrate']}\n"
        f"Fat: {result['nf_total_fat']}"
    )

calorie_tool = StructuredTool.from_function(
    func=estimate_calorie,
    name="CalorieEstimatorTool",
    description="Returns nutritional data (calories, protein, carbs, fat) for any food item.",
    args_schema=CalorieInput
)
