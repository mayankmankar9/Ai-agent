from typing import Literal, Optional
from pydantic import BaseModel
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.tools import StructuredTool
from app.tools.calorie_tool import calorie_tool

class MealPlannerInput(BaseModel):
    goal: Literal["cut", "bulk", "maintain"]
    diet_type: Literal["veg", "non-veg"]
    calorie_target: float
    protein_target: float
    dislikes: Optional[str] = None

# Add a safe float conversion function
def safe_float(val):
    try:
        return float(val)
    except Exception:
        return 0.0

llm = ChatOpenAI(model="gpt-3.5-turbo")

meal_prompt_template = PromptTemplate.from_template("""
You are a diet assistant generating a meal plan for a {goal} goal using a {diet_type} diet.
Target: {calorie_target} kcal and {protein_target}g protein per day.
Avoid: {dislikes}.
Generate a list of high-protein foods with specific quantities (e.g., "100g paneer", "2 boiled eggs", etc).
List one food item per line. Maximum 8 items.
""")

def plan_meal(goal, diet_type, calorie_target, protein_target, dislikes=None) -> str:
    prompt = meal_prompt_template.format(
        goal=goal,
        diet_type=diet_type,
        calorie_target=calorie_target,
        protein_target=protein_target,
        dislikes=dislikes or "none"
    )

    food_items = llm.invoke(prompt).content.strip().split("\n")
    total_cal, total_pro, total_carb, total_fat = 0, 0, 0, 0
    meal_lines = []

    for food in food_items:
        result = calorie_tool.invoke({"food": food.strip()})
        lines = result.strip().split("\n")

        cal, pro, carb, fat = 0, 0, 0, 0
        for line in lines:
            if "Calories:" in line:
                cal = safe_float(line.split(":")[1].strip())
            elif "Protein:" in line:
                pro = safe_float(line.split(":")[1].replace("g", "").strip())
            elif "Carbs:" in line:
                carb = safe_float(line.split(":")[1].replace("g", "").strip())
            elif "Fat:" in line:
                fat = safe_float(line.split(":")[1].replace("g", "").strip())

        if cal == 0 or pro == 0:
            continue

        if total_cal + cal > calorie_target and len(meal_lines) >= 5:
            break

        total_cal += cal
        total_pro += pro
        total_carb += carb
        total_fat += fat
        meal_lines.append(f"- {food.strip()} → {cal:.0f} kcal | {pro:.1f}g protein | {carb:.1f}g carbs | {fat:.1f}g fat")

    return (
        f"🍽️ Meal Plan ({diet_type}, {goal})\n" +
        "\n".join(meal_lines) +
        f"\n\nTotal: {total_cal:.1f} kcal, {total_pro:.1f}g protein, {total_carb:.1f}g carbs, {total_fat:.1f}g fat"
    )

meal_planner_tool = StructuredTool.from_function(
    func=plan_meal,
    name="MealPlannerTool",
    description="Generate a 1-day meal plan with calorie, protein, carb, and fat targets.",
    args_schema=MealPlannerInput
)
