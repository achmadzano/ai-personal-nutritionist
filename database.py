import os
from dotenv import load_dotenv
from pymongo import MongoClient
import bcrypt
from datetime import datetime, date
import streamlit as st

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.client = MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.client[os.getenv('MONGODB_DB_NAME')]
        self.users = self.db.users
        self.nutrition_logs = self.db.nutrition_logs
        self.user_profiles = self.db.user_profiles
        self.daily_meals = self.db.daily_meals
    
    def create_user(self, username, email, password):
        """Create a new user account"""
        # Check if user already exists
        if self.users.find_one({"$or": [{"username": username}, {"email": email}]}):
            return False, "Username or email already exists"
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_data = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "created_at": datetime.now(),
            "is_active": True
        }
        
        try:
            self.users.insert_one(user_data)
            return True, "User created successfully"
        except Exception as e:
            return False, f"Error creating user: {str(e)}"
    
    def authenticate_user(self, username, password):
        """Authenticate user login"""
        user = self.users.find_one({"username": username})
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return True, user
        return False, None
    
    def save_user_profile(self, username, height, current_weight, target_weight, age, gender, activity_level):
        """Save or update user profile with BMI data"""
        profile_data = {
            "username": username,
            "height": height,  # in cm
            "current_weight": current_weight,  # in kg
            "target_weight": target_weight,  # in kg
            "age": age,
            "gender": gender,
            "activity_level": activity_level,
            "updated_at": datetime.now()
        }
        
        try:
            # Upsert profile
            self.user_profiles.update_one(
                {"username": username},
                {"$set": profile_data},
                upsert=True
            )
            return True
        except Exception as e:
            st.error(f"Error saving profile: {str(e)}")
            return False
    
    def get_user_profile(self, username):
        """Get user profile"""
        return self.user_profiles.find_one({"username": username})
    
    def calculate_bmi(self, weight, height):
        """Calculate BMI"""
        height_m = height / 100  # convert cm to m
        return round(weight / (height_m ** 2), 1)
    
    def get_bmi_category(self, bmi):
        """Get BMI category"""
        if bmi < 18.5:
            return "Underweight", "🔵"
        elif 18.5 <= bmi < 25:
            return "Normal", "🟢"
        elif 25 <= bmi < 30:
            return "Overweight", "🟡"
        else:
            return "Obese", "🔴"
    
    def calculate_ideal_weight_range(self, height):
        """Calculate ideal weight range based on height"""
        height_m = height / 100
        min_weight = round(18.5 * (height_m ** 2), 1)
        max_weight = round(24.9 * (height_m ** 2), 1)
        return min_weight, max_weight
    
    def calculate_daily_calorie_needs(self, profile):
        """Calculate daily calorie needs based on BMR and activity level"""
        if not profile:
            return 2000  # default
        
        # Calculate BMR (Basal Metabolic Rate) using Mifflin-St Jeor Equation
        if profile['gender'].lower() == 'male':
            bmr = 10 * profile['current_weight'] + 6.25 * profile['height'] - 5 * profile['age'] + 5
        else:
            bmr = 10 * profile['current_weight'] + 6.25 * profile['height'] - 5 * profile['age'] - 161
        
        # Activity multipliers
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9
        }
        
        multiplier = activity_multipliers.get(profile['activity_level'], 1.2)
        daily_calories = round(bmr * multiplier)
        
        # Adjust for weight goal
        current_weight = profile['current_weight']
        target_weight = profile['target_weight']
        
        if target_weight > current_weight:  # Want to gain weight
            daily_calories += 300  # Add calories for weight gain
        elif target_weight < current_weight:  # Want to lose weight
            daily_calories -= 300  # Reduce calories for weight loss
        
        return daily_calories
    
    def save_daily_meal(self, username, meal_type, image_data, analysis_result):
        """Save meal for specific time of day"""
        today = date.today().isoformat()
        
        meal_data = {
            "username": username,
            "date": today,
            "meal_type": meal_type,  # 'breakfast', 'lunch', 'dinner'
            "image_data": image_data,
            "analysis_result": analysis_result,
            "timestamp": datetime.now()
        }
        
        try:
            # Replace existing meal for same date and meal_type
            self.daily_meals.update_one(
                {"username": username, "date": today, "meal_type": meal_type},
                {"$set": meal_data},
                upsert=True
            )
            return True
        except Exception as e:
            st.error(f"Error saving meal: {str(e)}")
            return False
    
    def get_daily_meals(self, username, target_date=None):
        """Get all meals for a specific date"""
        if target_date is None:
            target_date = date.today().isoformat()
        
        meals = self.daily_meals.find({
            "username": username,
            "date": target_date
        }).sort("timestamp", 1)
        
        return list(meals)
    
    def get_daily_nutrition_summary(self, username, target_date=None):
        """Get nutrition summary for a day"""
        meals = self.get_daily_meals(username, target_date)
        
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        meal_count = len(meals)
        
        for meal in meals:
            result = meal.get('analysis_result', {})
            total_calories += result.get('total_calories', 0)
            
            nutrition = result.get('nutritional_breakdown', {})
            total_protein += nutrition.get('protein', 0)
            total_carbs += nutrition.get('carbohydrates', 0)
            total_fat += nutrition.get('fat', 0)
        
        return {
            'total_calories': total_calories,
            'total_protein': total_protein,
            'total_carbs': total_carbs,
            'total_fat': total_fat,
            'meal_count': meal_count,
            'meals': meals
        }
    
    def get_user_logs(self, username, limit=20):
        """Get nutrition logs for a user, sorted by latest"""
        logs = self.nutrition_logs.find({"username": username}).sort("timestamp", -1).limit(limit)
        return list(logs)
    
    def save_nutrition_log(self, username, image_data, analysis_result):
        """Save a nutrition analysis log for a user"""
        log = {
            "username": username,
            "image_data": image_data,
            "analysis_result": analysis_result,
            "timestamp": datetime.now()
        }
        try:
            self.nutrition_logs.insert_one(log)
            return True
        except Exception as e:
            st.error(f"Error saving nutrition log: {str(e)}")
            return False