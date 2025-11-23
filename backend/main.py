from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from .database import engine, get_db, init_db
from .models import Base, RecipeType, RecipeIngredient, Ingredient as DBIngredient, FoodEntry as DBFoodEntry
from .schemas import RecipeCreate, Recipe, IngredientCreate, Ingredient, FoodEntryCreate, FoodEntry
from .services import RecipeService, IngredientService, NutritionService
from .ai_service import AIService
import json

app = FastAPI(title="Nutrition Tracker API")

@app.on_event("startup")
def on_startup():
    init_db()

@app.post("/analyze-image")
def analyze_image(file: UploadFile = File(...)):
    contents = file.file.read()
    result = AIService.analyze_image(contents, file.content_type)
    return result

@app.post("/ingredients", response_model=Ingredient)
def create_ingredient(ingredient: IngredientCreate, db: Session = Depends(get_db)):
    return IngredientService.create_ingredient(db, ingredient)

@app.get("/ingredients", response_model=List[Ingredient])
def list_ingredients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return IngredientService.list_ingredients(db, skip, limit)

@app.post("/recipes", response_model=Recipe)
def create_recipe(recipe: RecipeCreate, db: Session = Depends(get_db)):
    return RecipeService.create_recipe(db, recipe)

@app.get("/recipes", response_model=List[Recipe])
def list_recipes(db: Session = Depends(get_db)):
    return RecipeService.list_recipes(db)

@app.get("/recipes/{recipe_id}", response_model=Recipe)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = RecipeService.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe

@app.put("/recipes/{recipe_id}", response_model=Recipe)
def update_recipe(recipe_id: int, recipe: RecipeCreate, db: Session = Depends(get_db)):
    db_recipe = RecipeService.get_recipe(db, recipe_id)
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Update fields
    db_recipe.name = recipe.name
    db_recipe.standard_serving_amount = recipe.standard_serving_amount
    db_recipe.standard_serving_unit = recipe.standard_serving_unit
    db_recipe.type = recipe.type
    db_recipe.nutrition_direct = recipe.nutrition_direct
    
    # Update ingredients if provided (full replace strategy for simplicity)
    if recipe.type == RecipeType.GRANULAR and recipe.ingredients is not None:
        # Clear existing
        db.query(RecipeIngredient).filter(RecipeIngredient.recipe_id == db_recipe.id).delete()
        
        # Add new
        for item in recipe.ingredients:
             # Ensure ingredient exists
            ingredient = db.query(DBIngredient).filter(DBIngredient.name == item.ingredient_name).first()
            if not ingredient:
                 # Create ingredient if missing
                nutrition = item.nutrition_per_100g or {}
                ing_create = IngredientCreate(
                    name=item.ingredient_name,
                    energy_kcal_100g=nutrition.get('energy_kcal', 0),
                    protein_g_100g=nutrition.get('protein_g', 0),
                    carbs_g_100g=nutrition.get('carbs_g', 0),
                    fat_g_100g=nutrition.get('fat_g', 0)
                )
                ingredient = IngredientService.create_ingredient(db, ing_create)

            db_item = RecipeIngredient(
                recipe_id=db_recipe.id,
                ingredient_id=ingredient.id,
                quantity=item.quantity,
                unit=item.unit
            )
            db.add(db_item)
            
    db.commit()
    db.refresh(db_recipe)
    return db_recipe

@app.post("/recipes/{recipe_id}/flatten", response_model=Recipe)
def flatten_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = RecipeService.flatten_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe

@app.post("/log", response_model=FoodEntry)
def log_food(entry: FoodEntryCreate, db: Session = Depends(get_db)):
    db_entry = DBFoodEntry(**entry.dict())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@app.get("/log", response_model=List[FoodEntry])
def get_log(date: str = None, db: Session = Depends(get_db)):
    query = db.query(DBFoodEntry)
    if date:
        query = query.filter(DBFoodEntry.date == date)
    return query.all()

@app.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = RecipeService.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Manually delete associated food entries first (simulating cascade)
    db.query(DBFoodEntry).filter(DBFoodEntry.recipe_id == recipe_id).delete()
    
    # Delete the recipe
    db.delete(recipe)
    db.commit()
    return {"message": "Recipe deleted successfully"}
