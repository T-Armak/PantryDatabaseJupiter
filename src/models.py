from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Ingredient:
    name: str
    quantity: float
    unit: str

    
    def __post_init__(self): 
        """
        Post-init för att säkerställa formatering av attribut
        """

        # Felmeddelanden för tomt namn
        if not self.name.strip():
            raise ValueError("Ingredient name cannot be empty")
        
        # Felmeddelanden för tom enhet
        if not self.unit.strip():
            raise ValueError("Unit cannot be empty") 
        
        # Felmeddelanden för negativ mängd
        if self.quantity < 0:
            raise ValueError("Quantity cannot be negative")
        
@dataclass
class ShoppingList:
    name: str
    items: List[Ingredient] = field(default_factory=list)

    def __post_init__(self):
        # Validering av attribut
        if not self.name.strip():
            raise ValueError("ShoppingList must have a name")
        
        

@dataclass
class Recipe:
    name: str
    ingredients: List[Ingredient] = field(default_factory=list)
    servings: int = 4 # Anta 4 portioner som standard

    
    def __post_init__(self):
        # Validering av attribut
        if not self.name.strip():
            raise ValueError("Recipe must have a name")
        
        # Kontrollflagga för portioner
        if self.servings <= 0:
            raise ValueError("servings must be >= 1")
        
    # ----------- Privata hjälpmetoder ----------
    
    def _findRecipeIndex(self, name: str) -> Optional[int]:
        """
        Privat metod för att hitta index av ingrediens i receptets ingredienslista.

        Args:
            name (str): Namnet på ingrediensen att hitta.

        Returns:
            Optional[int]: Index av ingrediensen om den finns, annars None.
        """
        # Loopar igenom ingredienserna
        for i, ingredient in enumerate(self.ingredients):
            # Jämför namnet

            if ingredient.name == name:
                # Returnerar indexet om hittad
                return i 
            
        return None # Returnerar None om inte hittad

    # ----------- Publika API-metoder ----------
    
    def addIngredient(self, ingredient: Ingredient) -> None:
        """
        Lägger till en ingrediens i receptet. Om ingrediensen redan finns, uppdateras dess mängd.

        Args:
            ingredient (Ingredient): Ingrediensen att lägga till eller uppdatera.
        """
        idx = self._findRecipeIndex(ingredient.name) # Hitta index av ingrediensen

        # Om index/ingrediens saknas, lägg till
        if idx is None:
            self.ingredients.append(ingredient)

        # Om ingrediensen finns, uppdatera mängden
        else:
            cur = self.ingredients[idx] # Hämta nuvarande ingrediens

            # Kontrollera enhetsmatchning
            if cur.unit != ingredient.unit:
                raise ValueError(f"Unit mismatch for '{ingredient.name}': '{cur.unit}' vs '{ingredient.unit}'")
            
            # Skriv över med uppdaterad mängd
            self.ingredients[idx] = Ingredient(cur.name, cur.quantity + ingredient.quantity, cur.unit)

    def remove_ingredient(self, name: str) -> bool:
        """
        Tar bort en ingrediens från receptet baserat på dess namn.

        Args:
            name (str): Namnet på ingrediensen att ta bort.

        Returns:
            bool: True om ingrediensen togs bort, False om den inte hittades.
        """
        idx = self._findRecipeIndex(name)

        # Om ett objekt finns på index, ta bort det
        if idx is not None:
            del self.ingredients[idx]

            return True
        
        return False

    def get_ingredient(self, name: str) -> Optional[Ingredient]:
        """
        Hämtar en ingrediens från receptet baserat på dess namn.

        Args:
            name (str): Namnet på ingrediensen att hämta.

        Returns:
            Optional[Ingredient]: Ingrediensen om den hittas, annars None.
        """
        idx = self._findRecipeIndex(name)

        if idx is not None:
            return self.ingredients[idx]
        
        return None

    def scaleToServings(self, newServings: int) -> "Recipe": # Kanske överflödig, men behåll tills vidare

        """
        Skalar receptets ingredienser till ett nytt antal portioner och returnerar ett nytt Recipe-objekt.

        Args:
            new_servings (int): Det nya antalet portioner. Måste vara >= 1.

        Raises:
            ValueError: Om new_servings är mindre än 1.

        Returns:
            Recipe: Ett nytt recept med uppdaterade ingredienser och portioner.
        """
        # Kontrollera att new_servings är giltigt
        if newServings < 1:
            raise ValueError("new_servings must be >= 1")

        factor = newServings / self.servings
        
        for i in self.ingredients:
            i.quantity *= factor

        self.servings = newServings

        return self


@dataclass
class Inventory:
    items: List[Ingredient] = field(default_factory=list)
    
    def _findItemIndex(self, name: str) -> Optional[int]:
        """
        Privat metod för att hitta index av ingrediens i inventarielistan.

        Args:
            name (str): Namnet på ingrediensen att hitta.
        Returns:
            Optional[int]: Index av ingrediensen om den finns, annars None.
        """
        for i, item in enumerate(self.items):
            if item.name == name:

                return i
            
        return None
    
    def add(self, item: Ingredient) -> None:
        """
        Lägger till en ingrediens i inventariet. Om ingrediensen redan finns, uppdateras dess mängd.

        Args:
            item (Ingredient): Ingrediensen att lägga till eller uppdatera.
        Returns:
            None
        """
        idx = self._findItemIndex(item.name)

        # Om index saknas, lägg till
        if idx is None:
            self.items.append(item)

        else:
            cur = self.items[idx]

            if cur.unit != item.unit:
                raise ValueError(f"Unit mismatch for '{item.name}': '{cur.unit}' vs '{item.unit}'")
            
            self.items[idx] = Ingredient(cur.name, cur.quantity + item.quantity, cur.unit)
    
    def removeItem(self, name: str) -> bool:
        """
        Tar bort en ingrediens från inventariet baserat på dess namn.

        Args:
            name (str): Namnet på ingrediensen att ta bort.
        Returns:
            bool: True om ingrediensen togs bort, False om den inte hittades.
        """
        idx = self._findItemIndex(name)

        # Om ett objekt finns på index, ta bort det
        if idx is not None:
            del self.items[idx]

            return True
        
        return False
    
    def getItem(self, name: str) -> Optional[Ingredient]:
        """
        Hämtar en ingrediens från inventariet baserat på dess namn.

        Args:
            name (str): Namnet på ingrediensen att hämta.
        Returns:
            Optional[Ingredient]: Ingrediensen om den hittas, annars None.
        """
        idx = self._findItemIndex(name)

        # Returnera vara om hittad
        if idx is not None:
            return self.items[idx]
        
        return None
    
    def hasItem(self, item: Ingredient) -> bool:
        """
        Kontrollerar om inventariet har tillräckligt av en viss ingrediens.

        Args:
            item (Ingredient): Ingrediensen att kontrollera.
        Returns:
            bool: True om inventariet har tillräckligt av ingrediensen, annars False.
        """
        idx = self._findItemIndex(item.name)

        # Kollar om idex finns
        if idx is None:
            return False
        
        # Skapar temp-objket för jämförelse
        cur = self.items[idx]

        # Kollar enhet
        if cur.unit != item.unit:
            return False

        # Kollar mängd
        return cur.quantity >= item.quantity
    
    def updateAmount(self, name: str, new_amount: float) -> None:
        """
        Uppdaterar mängden av en ingrediens i inventariet.

        Args:
            name (str): Namnet på ingrediensen att uppdatera.
            new_amount (float): Den nya mängden för ingrediensen.
        Raises:
            KeyError: Om ingrediensen inte finns i inventariet.
            ValueError: Om den nya mängden är negativ.
        Returns:
            None
        """
        idx = self._findItemIndex(name) # Hitta index av 

        # Om item saknas, kasta fel
        if idx is None:
            raise KeyError(f"Ingredient '{name}' not found in inventory")
        
        cur = self.items[idx] # Hämta nuvarande ingrediens

        # Kontrollera att mängden inte är negativ
        if new_amount < 0:
            raise ValueError("Quantity cannot be negative")
        
        # Skriv över med uppdaterad mängd
        self.items[idx] = Ingredient(cur.name, new_amount, cur.unit)
