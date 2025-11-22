from sqlalchemy.orm import Session
from .models import Ingredient, Recipe, RecipeIngredient, RecipeType, FoodEntry
from .schemas import RecipeCreate, IngredientCreate
import math

class NutritionService:
    @staticmethod
    def calculate_recipe_nutrition(recipe: Recipe, db: Session):
        if recipe.type == RecipeType.DIRECT:
            return recipe.nutrition_direct or {}
        
        total_nutrition = {
            "energy_kcal": 0.0,
            "protein_g": 0.0,
            "carbs_g": 0.0,
            "fat_g": 0.0
        }
        
        for item in recipe.ingredients:
            qty_factor = item.quantity / 100.0  # Nutrition is per 100g
            ingredient = item.ingredient
            if ingredient:
                total_nutrition["energy_kcal"] += ingredient.energy_kcal_100g * qty_factor
                total_nutrition["protein_g"] += ingredient.protein_g_100g * qty_factor
                total_nutrition["carbs_g"] += ingredient.carbs_g_100g * qty_factor
                total_nutrition["fat_g"] += ingredient.fat_g_100g * qty_factor
                
        # Rounding
        return {
            "energy_kcal": round(total_nutrition["energy_kcal"]),
            "protein_g": round(total_nutrition["protein_g"], 1),
            "carbs_g": round(total_nutrition["carbs_g"], 1),
            "fat_g": round(total_nutrition["fat_g"], 1)
        }

class IngredientService:
    @staticmethod
    def get_ingredient_by_name(db: Session, name: str):
        return db.query(Ingredient).filter(Ingredient.name == name).first()

    @staticmethod
    def create_ingredient(db: Session, ingredient: IngredientCreate):
        db_ingredient = Ingredient(**ingredient.dict())
        db.add(db_ingredient)
        db.commit()
        db.refresh(db_ingredient)
        return db_ingredient
    
    @staticmethod
    def list_ingredients(db: Session, skip: int = 0, limit: int = 100):
        return db.query(Ingredient).offset(skip).limit(limit).all()

class RecipeService:
    @staticmethod
    def create_recipe(db: Session, recipe: RecipeCreate):
        db_recipe = Recipe(
            name=recipe.name, 
            type=recipe.type,
            standard_serving_amount=recipe.standard_serving_amount,
            standard_serving_unit=recipe.standard_serving_unit,
            nutrition_direct=recipe.nutrition_direct
        )
        db.add(db_recipe)
        db.commit()
        db.refresh(db_recipe)
        
        if recipe.type == RecipeType.GRANULAR and recipe.ingredients:
            for item in recipe.ingredients:
                ingredient = db.query(Ingredient).filter(Ingredient.name == item.ingredient_name).first()
                
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

    @staticmethod
    def get_recipe(db: Session, recipe_id: int):
        return db.query(Recipe).filter(Recipe.id == recipe_id).first()

    @staticmethod
    def list_recipes(db: Session):
        return db.query(Recipe).all()
        
    @staticmethod
    def flatten_recipe(db: Session, recipe_id: int):
        recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe or recipe.type == RecipeType.DIRECT:
            return recipe
            
        nutrition = NutritionService.calculate_recipe_nutrition(recipe, db)
        
        recipe.type = RecipeType.DIRECT
        recipe.nutrition_direct = nutrition
        # Ideally we archive the ingredients instead of deleting if we want audit/undo
        # For this MVP, we'll just delete the links
        db.query(RecipeIngredient).filter(RecipeIngredient.recipe_id == recipe.id).delete()
        
        db.commit()
        db.refresh(recipe)
        return recipe
