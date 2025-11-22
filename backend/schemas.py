from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class RecipeType(str, Enum):
    GRANULAR = "GRANULAR"
    DIRECT = "DIRECT"

class IngredientBase(BaseModel):
    name: str
    energy_kcal_100g: float
    protein_g_100g: float
    carbs_g_100g: float
    fat_g_100g: float

class IngredientCreate(IngredientBase):
    pass

class Ingredient(IngredientBase):
    id: int
    class Config:
        from_attributes = True

class RecipeIngredientBase(BaseModel):
    ingredient_name: str
    quantity: float
    unit: str
    nutrition_per_100g: Optional[dict] = None
    # Add calculated totals for convenience in UI
    # We can't easily inject these from ORM without property methods
    # So for now, we'll stick to basics or use a nested Ingredient object

class RecipeIngredientDisplay(BaseModel):
    quantity: float
    unit: str
    ingredient: Ingredient

    class Config:
        from_attributes = True

class RecipeCreate(BaseModel):
    name: str
    type: RecipeType
    standard_serving_amount: float = 1.0
    standard_serving_unit: str = "serving"
    nutrition_direct: Optional[dict] = None
    ingredients: Optional[List[RecipeIngredientBase]] = []

class Recipe(BaseModel):
    id: int
    name: str
    type: RecipeType
    standard_serving_amount: float
    standard_serving_unit: str
    nutrition_direct: Optional[dict] = None
    # Use the display schema which includes the full Ingredient object
    ingredients: List[RecipeIngredientDisplay] = []

    class Config:
        from_attributes = True

class FoodEntryCreate(BaseModel):
    recipe_id: int
    serving_multiplier: float = 1.0
    nutrition_override: Optional[dict] = None
    date: str

class FoodEntry(FoodEntryCreate):
    id: int
    class Config:
        from_attributes = True
