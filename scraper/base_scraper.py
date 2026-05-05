from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class PriceResult:
    product_id: str
    product_name: str
    store: str
    price: float
    unit: str
    offer: str  = ""    # t.ex. "2 för 30 kr"
    is_real: bool = True  # False = uppskattad/mock-pris


class BaseScraper(ABC):
    """Basklass för alla butiksskrapar. Utöka denna för Willys, ICA, Coop etc."""

    def __init__(self, store_name: str):
        self.store_name = store_name

    @abstractmethod
    def get_price(self, product_id: str, product_name: str) -> PriceResult | None:
        """Hämta priset för en enskild vara. Returnerar None om ej hittad."""
        pass

    def get_prices(self, products: list[dict]) -> list[PriceResult]:
        results = []
        for p in products:
            result = self.get_price(p["id"], p["name"])
            if result:
                results.append(result)
        return results
