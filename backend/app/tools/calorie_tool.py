import requests
from langchain.tools import StructuredTool
from pydantic import BaseModel

# Simple in-memory cache for Nutritionix API results
nutritionix_cache = {}

class CalorieInput(BaseModel):
    food: str

def estimate_calorie(food: str) -> str:
    headers = {
        "x-app-id": "91aa6676",        # 🔁 Replace with your real app ID
        "x-app-key": "43b6c68289627c30c8961b25399cbf98",      # 🔁 Replace with your real app key
        "Content-Type": "application/json"
    }
    url = "https://trackapi.nutritionix.com/v2/natural/nutrients"

    # 🔍 Clean food description to avoid vague GPT responses
    cleaned_food = food.split("→")[0].strip("- ").strip()

    # Check cache first
    if cleaned_food in nutritionix_cache:
        return nutritionix_cache[cleaned_food]

    response = requests.post(url, headers=headers, json={"query": cleaned_food})
    if response.status_code != 200 or not response.json().get("foods"):
        return "Not found"

    result = response.json()["foods"][0]
    result_str = (
        f"**{result['food_name'].title()}**\n"
        f"Calories: {result['nf_calories']}\n"
        f"Protein: {result['nf_protein']}\n"
        f"Carbs: {result['nf_total_carbohydrate']}\n"
        f"Fat: {result['nf_total_fat']}"
    )
    # Store in cache
    nutritionix_cache[cleaned_food] = result_str
    return result_str

calorie_tool = StructuredTool.from_function(
    func=estimate_calorie,
    name="CalorieEstimatorTool",
    description="Returns nutritional data (calories, protein, carbs, fat) for any food item.",
    args_schema=CalorieInput
)
