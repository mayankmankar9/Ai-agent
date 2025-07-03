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
List 6–8 individual food items with quantity.
Format: one item per line like "100g tofu".
""")

def plan_meal(goal, diet_type, calorie_target, protein_target, dislikes=None) -> str:
    prompt = meal_prompt_template.format(
        goal=goal, diet_type=diet_type,
        calorie_target=calorie_target, protein_target=protein_target,
        dislikes=dislikes or "none"
    )
    
    food_items = llm.invoke(prompt).content.strip().split("\n")
    print("🔍 GPT Output:", food_items)  # Debug output
    
    total_cal, total_pro, total_carb, total_fat = 0, 0, 0, 0
    meal_lines = []
    margin = 50  # kcal margin for target
    i = 0
    
    # Loop to add foods until calorie target is hit (within margin)
    while total_cal < calorie_target - margin and i < len(food_items):
        food = food_items[i].strip()
        if not food:  # Skip empty lines
            i += 1
            continue
            
        result = calorie_tool.invoke({"food": food})
        
        if result == "Not found":
            print(f"⚠️ Food not found: {food}")
            i += 1
            continue
            
        try:
            # Parse the result from calorie tool
            lines = result.split("\n")
            cal = float([line for line in lines if line.startswith("Calories:")][0].split(":")[1].strip())
            pro = float([line for line in lines if line.startswith("Protein:")][0].split(":")[1].strip())
            carb = float([line for line in lines if line.startswith("Carbs:")][0].split(":")[1].strip())
            fat = float([line for line in lines if line.startswith("Fat:")][0].split(":")[1].strip())
            
            total_cal += cal
            total_pro += pro
            total_carb += carb
            total_fat += fat
            
            meal_lines.append(f"- {food} → {cal:.0f} kcal | {pro:.1f}g protein | {carb:.1f}g carbs | {fat:.1f}g fat")
            
        except Exception as e:
            print(f"⚠️ Error parsing nutrition for {food}: {e}")
            pass
        i += 1
    
    # If overshot calorie target, remove last meal
    if total_cal > calorie_target + margin and meal_lines:
        last_line = meal_lines.pop()
        try:
            # Parse the last line to subtract its values
            parts = last_line.split("→")[1].split("|")
            cal = float(parts[0].replace("kcal", "").strip())
            pro = float(parts[1].replace("g protein", "").strip())
            carb = float(parts[2].replace("g carbs", "").strip())
            fat = float(parts[3].replace("g fat", "").strip())
            
            total_cal -= cal
            total_pro -= pro
            total_carb -= carb
            total_fat -= fat
        except:
            pass
    
    # Try to add more foods if still under target
    while total_cal < calorie_target - margin and i < len(food_items):
        food = food_items[i].strip()
        if not food:
            i += 1
            continue
            
        result = calorie_tool.invoke({"food": food})
        
        if result == "Not found":
            i += 1
            continue
            
        try:
            lines = result.split("\n")
            cal = float([line for line in lines if line.startswith("Calories:")][0].split(":")[1].strip())
            pro = float([line for line in lines if line.startswith("Protein:")][0].split(":")[1].strip())
            carb = float([line for line in lines if line.startswith("Carbs:")][0].split(":")[1].strip())
            fat = float([line for line in lines if line.startswith("Fat:")][0].split(":")[1].strip())
            
            total_cal += cal
            total_pro += pro
            total_carb += carb
            total_fat += fat
            
            meal_lines.append(f"- {food} → {cal:.0f} kcal | {pro:.1f}g protein | {carb:.1f}g carbs | {fat:.1f}g fat")
            
        except Exception as e:
            print(f"⚠️ Error parsing nutrition for {food}: {e}")
            pass
        i += 1
    
    return (f"🍽️ Meal Plan ({diet_type}, {goal})\n" + 
            "\n".join(meal_lines) + 
            f"\n\nTotal: {total_cal:.1f} kcal, {total_pro:.1f}g protein, {total_carb:.1f}g carbs, {total_fat:.1f}g fat")

meal_planner_tool = StructuredTool.from_function(
    func=plan_meal,
    name="MealPlannerTool",
    description="Generate a 1-day meal plan with calorie and protein targets.",
    args_schema=MealPlannerInput
)