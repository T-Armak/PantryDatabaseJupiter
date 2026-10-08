from typing import Any, Dict, List, Optional, Tuple
from .models import Ingredient, Recipe

_VOLUME_FACTORS: Dict[str, float] = {
    "ml": 0.001,     # milliliter
    "cl": 0.01,      # centiliter
    "dl": 0.1,       # deciliter
    "l": 1.0,        # liter (basenhet)
    "krm": 0.001,    # kryddmått 
    "tsk": 0.005,    # tesked
    "msk": 0.015,    # matsked
}

_WEIGHT_FACTORS: Dict[str, float] = {
    "mg": 0.001,    # milligram
    "g": 1.0,       # gram (basenhet)
    "kg": 1000.0,    # kilogram
}

_COUNT_UNITS: List[str] = [
    "st", 
    "styck", 
    "stycken", 
    "",       # tolkar tom sträng som "st"
]

def standardize_unit(quantity: float, unit: str) -> Tuple[float, str]:
    """
    Standardiserar en mängd och enhet till basenheten för volym, vikt eller antal.

    Returnerar en tuple med (standardiserad_mängd, standardiserad_enhet).

    Om enheten inte känns igen, returneras den ursprungliga mängden och enheten.
    """
    u = normalize_unit(unit)

    if u in _VOLUME_FACTORS:
        return quantity * _VOLUME_FACTORS[u], "l"  # basenhet för volym är liter
    
    elif u in _WEIGHT_FACTORS:
        return quantity * _WEIGHT_FACTORS[u], "g"  # basenhet för vikt är gram
    
    elif u in _COUNT_UNITS:
        return quantity, "st"  # basenhet för antal är styck
    
    return quantity, unit  # okänd enhet, returnera som är

def standardize_ingredient(ingredient: Ingredient) -> Ingredient:
    """
    Standardiserar en ingrediens till basenheten för volym, vikt eller antal.

    Returnerar en ny Ingredient med standardiserad mängd och enhet.
    """
    q, u = standardize_unit(ingredient.quantity, ingredient.unit)

    return Ingredient(name = normalize_name(ingredient.name), quantity = q, unit = u)

def normalize_name(s: str) -> str:
    return " ".join(s.strip().lower().split())

def normalize_unit(s: str) -> str:
    return s.strip().lower()

def scaled_ingredients(recipe: Recipe, servings: int) -> List[Ingredient]:
    if servings < 1:
        raise ValueError("servings must be >= 1")
    scale_factor = servings / recipe.servings

    scaled: List[Ingredient] = []
    for ingredient in recipe.ingredients:
        scaled_quantity = round(ingredient.quantity * scale_factor, 2)
        scaled.append(Ingredient(ingredient.name, scaled_quantity, ingredient.unit))
    
    return scaled

