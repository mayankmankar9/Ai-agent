from app.firebase import get_user_profile
from app.tools.calorie_tool import calorie_tool
from app.tools.meal_planner_tool import meal_planner_tool
from app.tools.protein_goal_tool import protein_goal_tool, estimate_protein
from app.tools.tdee_calculator_tool import tdee_calculator_tool, calculate_tdee
from app.tools.nutrition_calculator_tool import nutrition_calculator_tool, calculate_realistic_targets, NutritionCalculatorInput
from app.tools.weekly_planner_tool import weekly_planner_tool
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from typing import Dict, Any
import re
import math

# 🔧 Main agent runner
def run_agent(user_id: str, query: str) -> str:
    user = get_user_profile(user_id)
    if not user:
        return "❌ User profile not found."

    # Build personalized prompt context
    full_query = build_user_prompt(user_id, query)

    # 🔌 Initialize agent with tools
    tools = [
        calorie_tool,
        meal_planner_tool,
        protein_goal_tool,
        tdee_calculator_tool,
        weekly_planner_tool,
        nutrition_calculator_tool
    ]
    llm = ChatOpenAI(model="gpt-4")  # Or "gpt-3.5-turbo" if preferred

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )

    # 💬 Run the query through agent
    response = agent.run(full_query)
    return response

# ✍️ Build user profile context for prompt
def build_user_prompt(user_id: str, query: str) -> str:
    user = get_user_profile(user_id)
    if not user:
        return query

    goal = user.get("goal")
    diet_type = user.get("diet_type")
    dislikes = user.get("dislikes", "")
    weight = user.get("weight_kg")
    height = user.get("height_cm")
    age = user.get("age")
    gender = user.get("gender")
    activity = user.get("activity_level")
    tenure = user.get("tenure_months")
    target_weight = user.get("target_weight")

    tdee = calculate_tdee(gender, age, weight, height, activity)
    protein = estimate_protein(weight, goal)

    return f"""
User Profile:
- Name: {user.get('name', 'Unknown')}
- Goal: {goal}
- Diet Type: {diet_type}
- Dislikes: {dislikes}
- Weight: {weight}kg → Target: {target_weight or 'Not specified'}
- Tenure: {tenure or 'Not specified'} months
- Gender: {gender}
- Age: {age}
- Height: {height} cm
- Activity Level: {activity}

Estimated Needs:
{tdee}

Protein Goal:
{protein}

User Query:
{query}
""".strip()

def parse_nutrition_from_meal(meal_text: str) -> Dict[str, float]:
    """
    Parses a meal plan string and sums up kcal, protein, carbs, fat for the week.
    Handles both old and new format nutrition lines.
    """
    kcal, protein, carbs, fat = 0, 0, 0, 0
    
    for line in meal_text.splitlines():
        line = line.strip()
        
        # Handle new format: "Total: 1234.5 kcal, 56.7g protein, 123.4g carbs, 45.6g fat"
        if line.startswith('Total:'):
            try:
                # Extract numbers using regex
                kcal_match = re.search(r'(\d+\.?\d*)\s*kcal', line)
                protein_match = re.search(r'(\d+\.?\d*)g\s*protein', line)
                carbs_match = re.search(r'(\d+\.?\d*)g\s*carbs', line)
                fat_match = re.search(r'(\d+\.?\d*)g\s*fat', line)
                
                if kcal_match:
                    kcal += float(kcal_match.group(1))
                if protein_match:
                    protein += float(protein_match.group(1))
                if carbs_match:
                    carbs += float(carbs_match.group(1))
                if fat_match:
                    fat += float(fat_match.group(1))
                    
            except Exception as e:
                print(f"⚠️ Error parsing Total line: {line}, Error: {e}")
                continue
        
        # Handle old format: "Calories: 123, Protein: 12, Carbs: 34, Fat: 5"
        elif 'Calories:' in line and 'Protein:' in line and 'Carbs:' in line and 'Fat:' in line:
            try:
                kcal_match = re.search(r'Calories:\s*(\d+\.?\d*)', line)
                protein_match = re.search(r'Protein:\s*(\d+\.?\d*)', line)
                carbs_match = re.search(r'Carbs:\s*(\d+\.?\d*)', line)
                fat_match = re.search(r'Fat:\s*(\d+\.?\d*)', line)
                
                if kcal_match:
                    kcal += float(kcal_match.group(1))
                if protein_match:
                    protein += float(protein_match.group(1))
                if carbs_match:
                    carbs += float(carbs_match.group(1))
                if fat_match:
                    fat += float(fat_match.group(1))
                    
            except Exception as e:
                print(f"⚠️ Error parsing nutrition line: {line}, Error: {e}")
                continue
    
    return {"kcal": kcal, "protein": protein, "carbs": carbs, "fat": fat}

def calculate_safe_calorie_target(goal: str, current_tdee: float, target_weight: float, current_weight: float, weeks_remaining: int) -> float:
    """
    Calculate a safe and realistic calorie target based on goal and timeline.
    """
    # Safe weight loss/gain rates (kg per week)
    safe_rates = {
        "cut": -0.5,     # 0.5kg loss per week (conservative)
        "bulk": 0.25,    # 0.25kg gain per week (lean bulk)
        "maintain": 0    # maintain current weight
    }
    
    if goal == "maintain":
        return current_tdee
    
    # Calculate required weekly weight change
    if target_weight and weeks_remaining > 0:
        total_weight_change = target_weight - current_weight
        required_weekly_change = total_weight_change / weeks_remaining
        
        # Clamp to safe rates
        safe_rate = safe_rates[goal]
        if goal == "cut":
            # For cutting, don't exceed -1kg/week and don't go below safe rate
            weekly_change = max(-1.0, min(safe_rate, required_weekly_change))
        else:  # bulk
            # For bulking, don't exceed +0.5kg/week and don't go above safe rate
            weekly_change = min(0.5, max(safe_rate, required_weekly_change))
    else:
        weekly_change = safe_rates[goal]
    
    # Convert weight change to calorie adjustment
    # 1kg fat = ~7700 kcal, but muscle/water affects this
    # Use more conservative 7000 kcal per kg for mixed body composition
    kcal_per_kg = 7000
    weekly_kcal_change = weekly_change * kcal_per_kg
    daily_kcal_adjustment = weekly_kcal_change / 7
    
    target_calories = current_tdee + daily_kcal_adjustment
    
    # Safety bounds - never go below 1200 kcal or above TDEE + 500
    min_calories = 1200
    max_calories = current_tdee + 500
    
    return max(min_calories, min(max_calories, target_calories))

def generate_multiweek_plan(user_id: str, tenure_months: int, start_state: dict = None) -> Dict[str, Any]:
    user = get_user_profile(user_id)
    if not user:
        return {"error": "User profile not found."}

    goal = user.get("goal")
    diet_type = user.get("diet_type")
    dislikes = user.get("dislikes", "")
    weight = float(user.get("weight_kg"))
    height = float(user.get("height_cm"))
    age = int(user.get("age"))
    gender = user.get("gender")
    activity = user.get("activity_level")
    target_weight = float(user.get("target_weight")) if user.get("target_weight") else None

    max_weeks = tenure_months * 4
    plans = []
    cumulative = {"kcal": 0, "protein": 0, "carbs": 0, "fat": 0}
    current_weight = start_state["weight"] if start_state and "weight" in start_state else weight
    week_offset = start_state["week_offset"] if start_state and "week_offset" in start_state else 0
    kcal_per_kg = 7700  # Roughly 7700 kcal = 1kg fat
    warning = None
    analysis = None

    # Use the nutrition calculator tool for initial targets and analysis
    nutrition_input = NutritionCalculatorInput(
        current_weight=weight,
        target_weight=target_weight,
        height_cm=height,
        age=age,
        gender=gender,
        activity_level=activity,
        goal=goal,
        weeks_available=max_weeks
    )
    analysis = calculate_realistic_targets(**nutrition_input.dict())

    # Parse calorie and macro targets from the analysis string (simple extraction)
    cal_match = re.search(r"Calories: (\d+) kcal", analysis)
    pro_match = re.search(r"Protein: (\d+)g", analysis)
    carb_match = re.search(r"Carbs: (\d+)g", analysis)
    fat_match = re.search(r"Fat: (\d+)g", analysis)
    calorie_target = float(cal_match.group(1)) if cal_match else None
    protein_target = float(pro_match.group(1)) if pro_match else None
    carb_target = float(carb_match.group(1)) if carb_match else None
    fat_target = float(fat_match.group(1)) if fat_match else None

    for i in range(max_weeks):
        week = week_offset + i + 1
        # Use the calculated targets for each week
        week_plan = weekly_planner_tool.invoke({
            "goal": goal,
            "diet_type": diet_type,
            "calorie_target": calorie_target,
            "protein_target": protein_target,
            "dislikes": dislikes,
            "user_id": user_id
        })
        # Parse nutrition totals
        totals = parse_nutrition_from_meal(week_plan)
        for k in cumulative:
            cumulative[k] += totals[k]
        # Simulate weight change
        kcal_diff = totals["kcal"] - (calorie_target * 7)
        weight_change = kcal_diff / kcal_per_kg
        next_weight = current_weight + weight_change
        # For the last week, adjust to hit the target exactly
        if target_weight is not None and i == max_weeks - 1:
            next_weight = target_weight
        plans.append({
            "week": week,
            "plan": week_plan,
            "totals": totals,
            "start_weight": current_weight,
            "end_weight": next_weight,
            "calorie_target": calorie_target,
            "protein_target": protein_target,
            "carb_target": carb_target,
            "fat_target": fat_target
        })
        current_weight = next_weight
    # Cumulative summary
    summary = {
        "total_kcal": cumulative["kcal"],
        "total_protein": cumulative["protein"],
        "total_carbs": cumulative["carbs"],
        "total_fat": cumulative["fat"],
        "start_weight": weight,
        "end_weight": current_weight,
        "weeks": len(plans),
        "warning": warning,
        "analysis": analysis
    }
    # Return new end state for chaining
    end_state = {"weight": current_weight, "week_offset": plans[-1]["week"] if plans else week_offset}

    if target_weight is not None:
        total_weight_change = target_weight - weight
        required_weekly_change = total_weight_change / max_weeks
        # Clamp to safe maximum (1 kg/week)
        safe_max = 1.0 if total_weight_change > 0 else -1.0
        if abs(required_weekly_change) > abs(safe_max):
            suggested_weeks = math.ceil(abs(total_weight_change / safe_max))
            warning = (
                f"⚠️ The required weekly weight change ({required_weekly_change:.2f} kg/week) exceeds the safe maximum of {safe_max} kg/week. "
                f"The plan will use the maximum safe rate, and you may not reach your target in the selected tenure.\n"
                f"👉 To create a safer and more achievable plan, consider increasing your tenure to at least {suggested_weeks} weeks, or setting a less aggressive target weight."
            )
            required_weekly_change = safe_max
        # Calculate required kcal change per week
        required_kcal_change_per_week = required_weekly_change * kcal_per_kg

    return {"weeks": plans, "summary": summary, "end_state": end_state}
