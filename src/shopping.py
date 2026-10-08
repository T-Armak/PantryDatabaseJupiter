
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from .database import DatabaseManager
from .models import Ingredient, ShoppingList
from .inventory import InventoryManager
from .utils import normalize_name, normalize_unit, standardize_ingredient

@dataclass
class ShoppingManager:
    db: DatabaseManager
    lists: List[ShoppingList] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        """
        data = self.db.load()
        loaded_lists: List[ShoppingList] = []

        # initiera från rådata
        if isinstance(data, dict):

            # skapa shoppinglistor
            for list_name, raw_items in data.items():
                items: List[Ingredient] = [] # temporär lista

                # initiera ingredienser
                for item_dict in raw_items:
                    item_name = normalize_name(item_dict["name"])
                    item_qty = item_dict["quantity"]
                    item_unit = item_dict["unit"]

                    ingredient_obj = standardize_ingredient(Ingredient(item_name, item_qty, item_unit)) 
                    items.append(ingredient_obj)

                # skapa shoppinglistobjekt
                normalized_list_name = normalize_name(list_name)
                shopping_list = ShoppingList(name=normalized_list_name, items=items)
                loaded_lists.append(shopping_list)

        self.lists = loaded_lists

    # ------- Hjälpare -------
    def _find(self, name: str) -> Optional[ShoppingList]:
        """
        Hittar en shoppinglista med normaliserat namn.

        Returnerar None om inget hittas.
        """
        normalized_name = normalize_name(name)

        # sök i befintliga
        for existing in self.lists:
            if normalize_name(existing.name) == normalized_name:
                return existing
        return None

    # ------- Publikt API -------
    def list_lists(self) -> List[ShoppingList]:
        """
        Listar alla shoppinglistor.
        """
        return list(self.lists)

    def get(self, name: str) -> Optional[ShoppingList]:
        """
        Hämtar en shoppinglista baserat på namn.
        """
        return self._find(name)

    def upsert(self, shopping_list: ShoppingList) -> None:
        """
        Lägger till eller uppdaterar en shoppinglista.
        """
        key_name = normalize_name(shopping_list.name)

        # ersätt om finns annars lägg till
        kept: List[ShoppingList] = []
        for existing in self.lists:

            # behåll alla som inte matchar
            if normalize_name(existing.name) != key_name:
                kept.append(existing)

        self.lists = kept

        normalized_items: List[Ingredient] = []

        # normalisera ingredienser
        for item in shopping_list.items:
            normalized_items.append(standardize_ingredient(item))

        self.lists.append(ShoppingList(name=key_name, items=normalized_items))

    def remove(self, name: str) -> bool:
        """
        Tar bort en shoppinglista baserat på namn.
        """
        key_name = normalize_name(name)
        before_count = len(self.lists)

        kept: List[ShoppingList] = []

        # behåll alla som inte matchar
        for existing in self.lists:
            if normalize_name(existing.name) != key_name:
                kept.append(existing)

        self.lists = kept

        # om count minskat, togs något bort
        return len(self.lists) < before_count

    def add_item(self, list_name: str, item: Ingredient) -> None:
        """
        Lägger till en ingrediens i en shoppinglista.

        Skapar listan om den inte finns. Om ingrediensen redan finns, uppdateras dess mängd.
        """
        shopping_list = self._find(list_name)

        # skapa om saknas
        if shopping_list is None:
            shopping_list = ShoppingList(name=normalize_name(list_name), items=[])
            self.lists.append(shopping_list)

        # normalisera
        normalized_item = standardize_ingredient(item)
        key_name = normalized_item.name
        unit_value = normalized_item.unit

        # sök om finns
        found_index: Optional[int] = None
        for idx, current in enumerate(shopping_list.items):
            if normalize_name(current.name) == key_name:
                found_index = idx
                break
        
        # uppdatera eller lägg till
        if found_index is not None:
            current = shopping_list.items[found_index]

            # om enhet skiljer, fel
            if current.unit != unit_value:
                raise ValueError(f"Unit mismatch for '{key_name}': '{current.unit}' vs '{unit_value}'")
            
            # uppdatera mängd
            updated_quantity = current.quantity + normalized_item.quantity
            shopping_list.items[found_index] = Ingredient(current.name, updated_quantity, unit_value)

        # lägg till ny    
        else:
            shopping_list.items.append(Ingredient(key_name, normalized_item.quantity, unit_value))

    def remove_item(self, list_name: str, item_name: str) -> bool:
        """
        Tar bort en ingrediens från en shoppinglista baserat på namn.
        """
        shopping_list = self._find(list_name)

        # om listan saknas, inget att ta bort
        if shopping_list is None:
            return False


        key_name = normalize_name(item_name)
        before_count = len(shopping_list.items)

        kept_items: List[Ingredient] = [] # temporär lista

        # behåll alla som inte matchar
        for current in shopping_list.items:
            # Om inte match, behåll
            if normalize_name(current.name) != key_name:
                kept_items.append(current)

        shopping_list.items = kept_items

        # om count minskat, togs något bort
        return len(shopping_list.items) < before_count

    def purchase_item(self, list_name: str, inventory: InventoryManager, clear: bool = False) -> Dict[str, Any]:
        """
        Flyttar alla ingredienser från en shoppinglista till inventariet.
        Om clear är True, töms shoppinglistan efteråt.
        """
        shopping_list = self._find(list_name)

        # om listan saknas, fel
        if shopping_list is None:
            raise KeyError(f"shopping list '{list_name}' not found")

        # lägg till alla i inventariet
        for item in shopping_list.items:
            inventory.add(item)
        
        # returnera vad som lades till
        added: List[Dict[str, Any]] = []
        for i in shopping_list.items:
            added.append({"name": i.name, "quantity": i.quantity, "unit": i.unit})

        result: Dict[str, Any] = {"list": shopping_list.name, "added": added} 

        # töm listan om så önskas
        if clear:
            shopping_list.items = []

        return result

    def rename(self, old_name: str, new_name: str) -> bool:
        """
        Byter namn på en inköpslista.

        Returnerar True om lyckades, annars False.
        """

        shopping_list = self._find(old_name)

        if shopping_list is None:
            return False

        shopping_list.name = normalize_name(new_name)
        return True

    # ------- Persistens -------
    def save(self) -> None:
        payload: Dict[str, List[Dict[str, Any]]] = {}

        for shopping_list in self.lists:
            item_entries: List[Dict[str, Any]] = []
            for i in shopping_list.items:
                item_entries.append({"name": i.name, "quantity": i.quantity, "unit": i.unit})
            payload[shopping_list.name] = item_entries

        self.db.save(payload)
