#!/usr/bin/env python3
"""
Simple test script for food nutrient queries.
User enters any food, gets back calories, protein, carbs, fat from API.
Supports both interactive and batch (CLI args) modes.
"""

import sys
import os
from dotenv import load_dotenv

# Always load .env from project root
ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(ROOT, ".env"))

# Add backend to sys.path for import
BACKEND_PATH = os.path.join(ROOT, "backend", "app", "tools")
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, os.path.join(ROOT, "backend", "app"))

from backend.app.tools.calorie_tool import estimate_calorie

def pretty_print(food, result):
    print(f"\n{'='*40}")
    print(f"Food: {food}")
    print(result)
    print(f"{'='*40}")

def main():
    if len(sys.argv) > 1:
        # Batch mode: foods passed as CLI args
        foods = sys.argv[1:]
        for food in foods:
            pretty_print(food, estimate_calorie(food))
        return

    # Interactive mode
    print("🍽️  Food Nutrient Query Tool 🍽️")
    print("Enter any food item to get calories, protein, carbs, and fat")
    print("Type 'quit' or 'exit' to stop")
    print("=" * 50)
    
    while True:
        try:
            food = input("\nEnter a food item: ").strip()
            if food.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            if not food:
                print("Please enter a food item.")
                continue
            pretty_print(food, estimate_calorie(food))
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()