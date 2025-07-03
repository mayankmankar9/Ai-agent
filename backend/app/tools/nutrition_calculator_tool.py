from typing import Literal, Dict, Tuple
from pydantic import BaseModel
from langchain.tools import StructuredTool
import math

class NutritionCalculatorInput(BaseModel):
    current_weight: float
    target_weight: float
    height_cm: float
    age: int
    gender: Literal["male", "female"]
    activity_level: Literal["sedentary", "light", "moderate", "active", "very active"]
    goal: Literal["cut", "bulk", "maintain"]
    weeks_available: int

def calculate_realistic_targets(current_weight: float, target_weight: float, height_cm: float, 
                              age: int, gender: str, activity_level: str, goal: str, 
                              weeks_available: int) -> str:
    """
    Calculate realistic calorie and macro targets based on safe weight change rates.
    """
    
    # Calculate BMR using Mifflin-St Jeor equation
    bmr = 10 * current_weight + 6.25 * height_cm - 5 * age + (5 if gender == "male" else -161)
    
    # Activity multipliers
    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very active": 1.9
    }
    
    tdee = bmr * activity_multipliers[activity_level]
    
    # Safe weight change rates (kg per week)
    safe_rates = {
        "cut": {"min": -1.0, "recommended": -0.5, "aggressive": -0.75},
        "bulk": {"min": 0.1, "recommended": 0.25, "aggressive": 0.4},
        "maintain": {"recommended": 0}
    }
    
    if goal == "maintain":
        calorie_target = tdee
        timeline_analysis = "Maintaining current weight"
        weekly_change = 0
    else:
        # Calculate required weekly change
        total_change_needed = target_weight - current_weight
        required_weekly_change = total_change_needed / weeks_available if weeks_available > 0 else 0
        
        # Get safe rates for this goal
        rates = safe_rates[goal]
        recommended_rate = rates["recommended"]
        
        # Determine if timeline is realistic
        if goal == "cut":
            is_realistic = required_weekly_change >= rates["min"]  # Not too aggressive
            is_recommended = abs(required_weekly_change - recommended_rate) <= 0.1
        else:  # bulk
            is_realistic = required_weekly_change <= rates["aggressive"]  # Not too fast
            is_recommended = abs(required_weekly_change - recommended_rate) <= 0.1
        
        # Choose the appropriate rate
        if is_realistic and abs(required_weekly_change) <= abs(rates["aggressive"]):
            weekly_change = required_weekly_change
            timeline_analysis = "Timeline is realistic"
        else:
            weekly_change = recommended_rate
            realistic_weeks = abs(total_change_needed / recommended_rate)
            timeline_analysis = f"Timeline needs adjustment: {realistic_weeks:.0f} weeks recommended vs {weeks_available} requested"
        
        # Convert to calorie adjustment
        # 1kg fat ≈ 7700 kcal, but use 7000 for mixed body composition
        weekly_calorie_change = weekly_change * 7000
        daily_calorie_adjustment = weekly_calorie_change / 7
        calorie_target = tdee + daily_calorie_adjustment
        
        # Safety bounds
        min_calories = max(1200, bmr * 1.1)  # Never below 110% of BMR
        max_calories = tdee + 500  # Never more than +500 above TDEE
        calorie_target = max(min_calories, min(max_calories, calorie_target))
    
    # Calculate protein target
    protein_multipliers = {
        "cut": 2.0,      # Higher protein during cut to preserve muscle
        "bulk": 1.6,     # Moderate protein for muscle building
        "maintain": 1.2  # Basic protein needs
    }
    
    protein_target = current_weight * protein_multipliers[goal]
    
    # Calculate estimated macros (basic distribution)
    protein_calories = protein_target * 4  # 4 kcal per gram
    
    if goal == "cut":
        # Lower carb approach for cutting
        fat_percentage = 0.25
        carb_percentage = 0.35
    elif goal == "bulk":
        # Higher carb for building
        fat_percentage = 0.2
        carb_percentage = 0.5
    else:  # maintain
        # Balanced approach
        fat_percentage = 0.25
        carb_percentage = 0.45
    
    fat_calories = calorie_target * fat_percentage
    carb_calories = calorie_target * carb_percentage
    
    # Adjust if protein is too high
    total_macro_calories = protein_calories + fat_calories + carb_calories
    if total_macro_calories > calorie_target:
        # Reduce carbs first, then fats
        excess = total_macro_calories - calorie_target
        carb_calories = max(carb_calories - excess, calorie_target * 0.2)
        fat_calories = calorie_target - protein_calories - carb_calories
    
    fat_grams = fat_calories / 9  # 9 kcal per gram
    carb_grams = carb_calories / 4  # 4 kcal per gram
    
    # Prepare detailed response
    result = f"""
🎯 Nutrition Plan Analysis

Current Stats:
- Weight: {current_weight:.1f}kg
- Target: {target_weight:.1f}kg ({total_change_needed:+.1f}kg change)
- Timeline: {weeks_available} weeks
- Goal: {goal.upper()}

Metabolic Calculations:
- BMR: {bmr:.0f} kcal/day
- TDEE: {tdee:.0f} kcal/day
- Activity Level: {activity_level}

Weight Change Plan:
- Required Rate: {required_weekly_change:.2f}kg/week
- Recommended Rate: {weekly_change:.2f}kg/week
- Analysis: {timeline_analysis}

Daily Targets:
- Calories: {calorie_target:.0f} kcal
- Protein: {protein_target:.0f}g ({protein_calories:.0f} kcal)
- Carbs: {carb_grams:.0f}g ({carb_calories:.0f} kcal)
- Fat: {fat_grams:.0f}g ({fat_calories:.0f} kcal)

Weekly Deficit/Surplus: {weekly_calorie_change:+.0f} kcal
Expected Weekly Change: {weekly_change:+.2f}kg
""".strip()
    
    return result

def get_adaptive_calorie_target(current_weight: float, target_weight: float, weeks_remaining: int, 
                              goal: str, current_tdee: float) -> float:
    """
    Get adaptive calorie target that adjusts based on proximity to goal and time remaining.
    """
    if goal == "maintain":
        return current_tdee
    
    # Calculate how much change is still needed
    remaining_change = target_weight - current_weight
    
    # If we're close to target (within 2kg), use maintenance calories
    if abs(remaining_change) <= 2.0:
        return current_tdee
    
    # Calculate safe weekly rate based on remaining change and time
    if weeks_remaining <= 0:
        return current_tdee
    
    required_weekly_rate = remaining_change / weeks_remaining
    
    # Apply safety limits
    if goal == "cut":
        # Don't lose more than 1kg per week
        safe_rate = max(-1.0, required_weekly_rate)
    else:  # bulk
        # Don't gain more than 0.5kg per week
        safe_rate = min(0.5, required_weekly_rate)
    
    # Convert to calories
    weekly_calorie_change = safe_rate * 7000
    daily_adjustment = weekly_calorie_change / 7
    
    target_calories = current_tdee + daily_adjustment
    
    # Safety bounds
    min_calories = 1200
    max_calories = current_tdee + 500
    
    return max(min_calories, min(max_calories, target_calories))

# Create the structured tool
nutrition_calculator_tool = StructuredTool.from_function(
    func=calculate_realistic_targets,
    name="NutritionCalculatorTool",
    description="Calculate realistic calorie and macro targets based on safe weight change rates and timeline.",
    args_schema=NutritionCalculatorInput
)
