from typing import Literal, Optional
from pydantic import BaseModel
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.tools import StructuredTool
from app.tools.calorie_tool import calorie_tool

class MealPlannerInput(BaseModel):
    goal: Literal["cut", "bulk", "maintain"]
    diet_type: Literal["veg", "non-veg"]
    calorie_target: float
    protein_target: float
    dislikes: Optional[str] = None

llm = ChatOpenAI()

meal_prompt_template = PromptTemplate.from_template("""
You are a diet assistant creating a 1-day meal plan for {goal} using a {diet_type} diet.
Target: {calorie_target} kcal, {protein_target}g protein.
Avoid: {dislikes}.
List 6–8 individual food items with quantity. Format: one item per line like "100g tofu".
""")

def plan_meal(goal, diet_type, calorie_target, protein_target, dislikes=None) -> str:
    prompt = meal_prompt_template.format(
        goal=goal, diet_type=diet_type,
        calorie_target=calorie_target, protein_target=protein_target,
        dislikes=dislikes or "none"
    )
    
    food_items = llm.invoke(prompt).content.strip().split("\n")
    print("🔍 GPT Output:", food_items)  # ✅ Debug output

    total_cal, total_pro = 0, 0
    meal_lines = []

    for food in food_items:
        result = calorie_tool.invoke({"food": food})
        try:
            lines = result.split("\n")
            cal = float(lines[1].split(":")[1].strip())
            pro = float(lines[2].split(":")[1].strip())
            total_cal += cal
            total_pro += pro
            meal_lines.append(f"- {food} → {cal:.0f} kcal | {pro:.1f}g protein")
        except:
            continue

        # ✅ New stop condition: only break if already have 5+ meals AND target is hit
        if (total_cal >= calorie_target or total_pro >= protein_target) and len(meal_lines) >= 5:
            break

    return f"🍽️ Meal Plan ({diet_type}, {goal})\n" + "\n".join(meal_lines) + f"\n\nTotal: {total_cal:.1f} kcal, {total_pro:.1f}g protein"


meal_planner_tool = StructuredTool.from_function(
    func=plan_meal,
    name="MealPlannerTool",
    description="Generate a 1-day meal plan with calorie and protein targets.",
    args_schema=MealPlannerInput
)
