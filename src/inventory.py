
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any

from .database import DatabaseManager
from .models import Ingredient, Inventory
from .utils import normalize_name, normalize_unit, standardize_ingredient


@dataclass
class InventoryManager:
    db: DatabaseManager
    inventory: Inventory = field(default_factory=Inventory)

    def __post_init__(self) -> None:
        """
        """
        data = self.db.load()
        items: List[Ingredient] = []

        # initiera från rådata
        if isinstance(data, dict):
            # skapa ingredienser
            for item_name, item_dict in data.items():
                normalized_name = normalize_name(item_name)
                quantity_value = item_dict.get("quantity", 0.0)
                unit_value = item_dict.get("unit", "")
                ingredient_obj = standardize_ingredient(Ingredient(normalized_name, quantity_value, unit_value))
                items.append(ingredient_obj)
        else:
            # Tom eller oförväntad struktur -> starta tomt
            items = []

        self.inventory.items = items

    # ------- Publikt API -------
    def list_items(self) -> List[Ingredient]:
        """
        Listar alla ingredienser i inventariet.
        """
        return list(self.inventory.items)

    def get(self, name: str) -> Optional[Ingredient]:
        """
        Hämtar en ingrediens baserat på namn.
        """
        normalized_name = normalize_name(name)
        return self.inventory.getItem(normalized_name)

    def add(self, item: Ingredient) -> None:
        """
        Lägger till en ingrediens i inventariet.

        Om ingrediensen redan finns, uppdateras dess mängd.
        """
        normalized_item = standardize_ingredient(item)

        self.inventory.add(normalized_item)

    def remove(self, name: str) -> bool:
        """
        Tar bort en ingrediens från inventariet baserat på namn.
        """
        normalized_name = normalize_name(name)
        return self.inventory.removeItem(normalized_name)

    def update_amount(self, name: str, new_amount: float) -> None:
        """
        Uppdaterar mängden av en ingrediens i inventariet.
        """
        normalized_name = normalize_name(name)
        self.inventory.updateAmount(normalized_name, new_amount)

    def has(self, item: Ingredient) -> bool:
        """
        Kollar om inventariet har minst den angivna mängden av ingrediensen.
        """
        normalized_item = standardize_ingredient(item)

        return self.inventory.hasItem(normalized_item)

    def check_availability(self, ingredients: List[Ingredient]) -> Tuple[bool, List[str], List[Ingredient]]:
        """
        Kollar om inventariet kan uppfylla en lista av ingredienser.

        Returns:
            - ok (bool): True om alla ingredienser finns i tillräcklig mängd, annars False
            - messages (List[str]): Lista av meddelanden om vad som saknas
            - missing_items (List[Ingredient]): Lista av ingredienser som saknas eller är otillräckliga
        """
        messages: List[str] = [] # meddelanden om vad som saknas
        missing_items: List[Ingredient] = [] # ingredienser som saknas eller är otillräckliga

        # kolla varje ingrediens
        for requested in ingredients:
            req_item = standardize_ingredient(requested)
            # kolla om finns i inventariet
            current = self.inventory.getItem(req_item.name)

            # om saknas helt
            if current is None:
                messages.append(f"Saknas: {req_item.name} ({round(req_item.quantity, 2)} {req_item.unit})")
                missing_items.append(Ingredient(req_item.name, req_item.quantity, req_item.unit))
                continue

            # om enhet skiljer (defensiv)
            if current.unit != req_item.unit: # eventuellt ta bort detta blocket
                messages.append(f"Fel enhet för {req_item.name}: har '{current.unit}', behöver '{req_item.unit}'")
                missing_items.append(Ingredient(req_item.name, req_item.quantity, req_item.unit))
                continue

            # om mängd är otillräcklig
            if current.quantity < req_item.quantity:
                diff = req_item.quantity - current.quantity

                messages.append(f"Otillräckligt {req_item.name}: har {round(current.quantity, 2)} {current.unit}, behöver {round(req_item.quantity, 2)} {req_item.unit}")


                missing_items.append(Ingredient(req_item.name, diff, req_item.unit))    

        # om inga saknas, är allt ok
        ok = len(messages) == 0
        return ok, messages, missing_items

    def consume(self, ingredients: List[Ingredient]) -> None:
        """
        Konsumerar (minskar mängden av) en lista av ingredienser från inventariet.
        """
        ok, msg_missing, _ = self.check_availability(ingredients) # kolla först

        # om inte ok, kasta fel
        if not ok:
            error_lines = "\n- ".join(msg_missing)
            raise ValueError("Kan inte laga receptet:\n- " + error_lines)

        # minska mängd för varje ingrediens
        for requested in ingredients:
            req = standardize_ingredient(requested)

            name_key = req.name
            requested_amount = req.quantity


            current = self.inventory.getItem(name_key)

            # safety check
            if current is None:
                raise RuntimeError(f"Internal error: ingredient '{name_key}' not found during consume")

            # säkerställ att current finns och enhet matchar (borde vara garanterat av can_fulfil)
            new_amount = current.quantity - requested_amount
            self.inventory.updateAmount(name_key, new_amount)

    # ------- Persistens -------
    def save(self) -> None:
        """
        Sparar som dict {name: {quantity, unit}}
        """
        payload: Dict[str, Dict[str, Any]] = {}

        for item in self.inventory.items:
            entry: Dict[str, Any] = {
                "quantity": item.quantity,
                "unit": item.unit,
            }
            payload[item.name] = entry

        self.db.save(payload)
