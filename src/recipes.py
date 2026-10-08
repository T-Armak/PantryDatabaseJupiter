
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from .database import DatabaseManager
from .models import Ingredient, Recipe, ShoppingList
from .utils import normalize_name, normalize_unit, scaled_ingredients, standardize_ingredient
from .inventory import InventoryManager

@dataclass
class RecipeManager:
    db: DatabaseManager
    recipes: List[Recipe] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        """
        data = self.db.load()
        loaded_recipes: List[Recipe] = []

        if isinstance(data, dict):
            for recipe_name, recipe_dict in data.items():
                # Skapa ingredienslista
                ingredient_list: List[Ingredient] = []
                raw_ingredients = recipe_dict.get("ingredients", [])

                # Initiera ingredienser
                for ing_dict in raw_ingredients:
                    ing_name = normalize_name(ing_dict["name"])
                    ing_qty = ing_dict["quantity"]
                    ing_unit = ing_dict["unit"]

                    ingredient_obj = standardize_ingredient(Ingredient(ing_name, ing_qty, ing_unit))
                    ingredient_list.append(ingredient_obj)

                # Initiera recept
                normalized_recipe_name = normalize_name(recipe_name)
                recipe_servings = int(recipe_dict.get("servings", 1))

                # Skapa Recipe-objekt
                recipe_obj = Recipe(
                    name = normalized_recipe_name,
                    ingredients = ingredient_list,
                    servings = recipe_servings,
                )

                # Lägg till i listan
                loaded_recipes.append(recipe_obj)

        self.recipes = loaded_recipes 

    # ------- Hjälpare -------
    def _find(self, name: str) -> Optional[Recipe]:
        """
        Hittar ett recept med normaliserat namn.
        Returnerar None om inget hittas.
        """
        normalized_name = normalize_name(name)

        # sök i befintliga
        for recipe in self.recipes:
            # Om match, returnera
            if normalize_name(recipe.name) == normalized_name:
                return recipe
        return None

    # ------- Publikt API -------
    def list_recipes(self) -> List[Recipe]:
        return list(self.recipes)

    def get(self, name: str) -> Optional[Recipe]:
        return self._find(name)

    def upsert(self, recipe: Recipe) -> None:
        """
        Ersätter/Skapar recept. Normaliserar namn och enheter.
        """
        key_name = normalize_name(recipe.name)

        # behåll bara de som inte matchar key_name
        kept: List[Recipe] = []
        for existing in self.recipes:
            # Om inte match, behåll
            if normalize_name(existing.name) != key_name:
                kept.append(existing)
        
        # uppdatera listan
        self.recipes = kept

        # normalisera ingredienser
        normalized_ingredients: List[Ingredient] = []
        for ing in recipe.ingredients:
            normalized_ingredients.append(standardize_ingredient(ing))

        # skapa nytt recept och lägg till
        new_recipe = Recipe(name=key_name, ingredients=normalized_ingredients, servings=int(recipe.servings))
        self.recipes.append(new_recipe)

    def remove(self, name: str) -> bool:
        """
        Tar bort ett recept.

        Returnerar True om något togs bort, annars False.
        """
        key_name = normalize_name(name)
        before_count = len(self.recipes)

        # behåll bara de som inte matchar key_name
        kept: List[Recipe] = []
        for existing in self.recipes:
            if normalize_name(existing.name) != key_name:
                kept.append(existing)
        self.recipes = kept

        return len(self.recipes) < before_count

    def rename(self, old_name: str, new_name: str) -> bool:
        """
        Byter namn på ett recept.

        Returnerar True om lyckades, annars False.
        """

        recipe = self._find(old_name)

        if recipe is None:
            return False
        
        recipe.name = normalize_name(new_name)
        return True

    # --- Ingrediens-API ---
    def add_ingredient(self, recipe_name: str, ingredient: Ingredient) -> None:
        """
        Lägger till en ingrediens i ett recept.

        Skapar receptet om det inte finns.
        """

        recipe = self._find(recipe_name)
        # Skapa om inte finns
        if recipe is None:
            recipe = Recipe(name=normalize_name(recipe_name), ingredients=[], servings=1)
            self.recipes.append(recipe)

        # Lägg till ingrediens 
        ingredient_to_add = standardize_ingredient(ingredient)
        recipe.addIngredient(ingredient_to_add)

    def remove_ingredient(self, recipe_name: str, ingredient_name: str) -> bool:
        """
        Tar bort en ingrediens från ett recept.
        """
        recipe = self._find(recipe_name)
        if recipe is None:
            return False
        return recipe.remove_ingredient(normalize_name(ingredient_name))

    def get_ingredient(self, recipe_name: str, ingredient_name: str) -> Optional[Ingredient]:
        """
        Hämtar en ingrediens från ett recept.
        """

        recipe = self._find(recipe_name)
        if recipe is None:
            return None
        return recipe.get_ingredient(normalize_name(ingredient_name))


    # --- Tillagning ---
    def make_recipe(self, recipe_name: str, servings: int, inventory: InventoryManager, shopping: "Any|None" = None, shopping_list_name: "str|None" = None) -> Dict[str, Any]:
        """
        Försöker laga ett recept med angivet antal portioner.

        Om dry_run är True, så reserveras inga ingredienser från lagret.

        """
        recipe = self._find(recipe_name)
        if recipe is None:
            raise KeyError(f"recipe '{recipe_name}' not found")
        
        # beräkna behov
        needed = scaled_ingredients(recipe, servings)
        ok, missing, to_buy = inventory.check_availability(needed)

        
        consumed: List[Dict[str, Any]] = [] # lista av ingredienser som konsumerades

        # om ok, konsumera
        if ok:
            # lägg till alla i consumed
            for ing in needed:
                consumed.append({
                    "name": ing.name,
                    "quantity": ing.quantity,
                    "unit": ing.unit,
                })

        # skapa resultat
        created_list: Optional[str] = None

        if not ok and shopping is not None:
            if to_buy:
                created_list = shopping_list_name or f"{recipe.name} - inköp"
                shopping.upsert(ShoppingList(name = created_list, items = to_buy))

        # Sparar resultat i dict, lite fult kanske
        result: Dict[str, Any] = {
            "recipe": recipe.name,
            "servings": servings,
            "ok": ok,
            "missing": missing,
            "consumed": consumed if ok else [],
            "shopping_list": created_list,
        }

        # om ok konsumera
        if ok:
            inventory.consume(needed)

        return result

    # ------- Persistens -------
    def save(self) -> None:
        payload: Dict[str, Dict[str, Any]] = {} # recipe name -> dict

        # skapa payload
        for recipe in self.recipes:
            ing_list: List[Dict[str, Any]] = []

            # Skapa ingredienslista
            for ing in recipe.ingredients:
                ing_entry = {"name": ing.name, "quantity": ing.quantity, "unit": ing.unit}
                ing_list.append(ing_entry)

            # Lägg till i payload
            payload[recipe.name] = {
                "servings": int(recipe.servings),
                "ingredients": ing_list,
            }

        # spara
        self.db.save(payload)
