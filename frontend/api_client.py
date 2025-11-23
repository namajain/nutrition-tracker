import requests
import os
import streamlit as st

API_URL = "http://localhost:8000"

@st.cache_data(ttl=300, show_spinner=False)
def get_recipes():
    try:
        res = requests.get(f"{API_URL}/recipes")
        return res.json() if res.status_code == 200 else []
    except:
        return []

def clear_recipe_cache():
    get_recipes.clear()

def get_daily_log(date_str):
    try:
        res = requests.get(f"{API_URL}/log", params={"date": date_str})
        return res.json() if res.status_code == 200 else []
    except:
        return []

def log_food(recipe_id, multiplier, date_str, override=None):
    payload = {
        "recipe_id": recipe_id,
        "serving_multiplier": multiplier,
        "date": date_str,
        "nutrition_override": override
    }
    return requests.post(f"{API_URL}/log", json=payload)

def analyze_image(image_file, mime_type):
    files = {"file": (image_file.name, image_file, mime_type)}
    return requests.post(f"{API_URL}/analyze-image", files=files)

def create_recipe(data):
    return requests.post(f"{API_URL}/recipes", json=data)

def update_recipe(recipe_id, data):
    return requests.put(f"{API_URL}/recipes/{recipe_id}", json=data)

def create_ingredient(data):
    return requests.post(f"{API_URL}/ingredients", json=data)

def delete_recipe(recipe_id):
    return requests.delete(f"{API_URL}/recipes/{recipe_id}")
