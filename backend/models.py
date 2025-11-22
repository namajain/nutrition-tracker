from sqlalchemy import create_engine, Column, Integer, String, Float, Enum, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()

class RecipeType(str, enum.Enum):
    GRANULAR = "GRANULAR"
    DIRECT = "DIRECT"

class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    energy_kcal_100g = Column(Float, default=0.0)
    protein_g_100g = Column(Float, default=0.0)
    carbs_g_100g = Column(Float, default=0.0)
    fat_g_100g = Column(Float, default=0.0)

class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(Enum(RecipeType), default=RecipeType.GRANULAR)
    standard_serving_amount = Column(Float, default=1.0)
    standard_serving_unit = Column(String, default="serving")
    
    # For DIRECT recipes, we store nutrition directly
    nutrition_direct = Column(JSON, nullable=True)

    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    food_entries = relationship("FoodEntry", back_populates="recipe")

class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"))
    quantity = Column(Float)
    unit = Column(String)

    recipe = relationship("Recipe", back_populates="ingredients")
    ingredient = relationship("Ingredient")

class FoodEntry(Base):
    __tablename__ = "food_entries"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    serving_multiplier = Column(Float, default=1.0)
    date = Column(String, index=True) # storing as YYYY-MM-DD for simplicity or datetime string
    
    # Optional override
    nutrition_override = Column(JSON, nullable=True)

    recipe = relationship("Recipe", back_populates="food_entries")

