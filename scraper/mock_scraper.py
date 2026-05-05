import random
from .base_scraper import BaseScraper, PriceResult

# Fiktiva priser för MVP – ersätt med riktig skraper senare
MOCK_PRICES = {
    "willys": {
        "kycklingfile":       (131.00, ""),
        "farserad_kyckling":  (89.00,  ""),
        "notfars":            (59.90,  "2 för 109 kr"),
        "lax":                (89.00,  ""),
        "korv":               (39.90,  ""),
        "mjolk":              (19.90,  ""),
        "smor":               (39.90,  ""),
        "yoghurt":            (29.90,  ""),
        "ost":                (69.90,  ""),
        "agg":                (39.90,  ""),
        "banan":              (19.90,  ""),
        "tomat":              (24.90,  ""),
        "gurka":              (14.90,  "2 för 25 kr"),
        "paprika":            (34.90,  ""),
        "potatis":            (29.90,  ""),
        "blojor":             (122.00, ""),
        "barnmat":            (19.90,  "4 för 69 kr"),
        "barnmat_kyckling":   (19.90,  "4 för 69 kr"),
        "vetegrot":           (34.90,  ""),
        "barnflingor":        (39.90,  ""),
        "pasta":              (14.90,  ""),
        "ris":                (29.90,  ""),
        "mjol":               (24.90,  ""),
        "olja":               (39.90,  ""),
        "tomatkross":         (12.90,  ""),
        "brod":               (29.90,  ""),
        "knackebrod":         (24.90,  ""),
        "havregryn":          (19.90,  ""),
    },
    "ica": {
        "kycklingfile":       (139.00, ""),
        "farserad_kyckling":  (95.00,  ""),
        "notfars":            (64.90,  ""),
        "lax":                (99.00,  ""),
        "korv":               (42.90,  "2 för 79 kr"),
        "mjolk":              (21.90,  ""),
        "smor":               (42.90,  ""),
        "yoghurt":            (27.90,  ""),
        "ost":                (74.90,  ""),
        "agg":                (44.90,  ""),
        "banan":              (22.90,  ""),
        "tomat":              (26.90,  ""),
        "gurka":              (16.90,  ""),
        "paprika":            (36.90,  "3 för 99 kr"),
        "potatis":            (31.90,  ""),
        "blojor":             (129.00, ""),
        "barnmat":            (21.90,  ""),
        "barnmat_kyckling":   (21.90,  ""),
        "vetegrot":           (36.90,  ""),
        "barnflingor":        (42.90,  ""),
        "pasta":              (16.90,  ""),
        "ris":                (32.90,  ""),
        "mjol":               (26.90,  ""),
        "olja":               (42.90,  ""),
        "tomatkross":         (14.90,  ""),
        "brod":               (32.90,  ""),
        "knackebrod":         (27.90,  ""),
        "havregryn":          (22.90,  ""),
    },
}


class MockScraper(BaseScraper):
    """Testskraper med hårdkodade priser. Byt ut mot WillysScraper/ICAScraper."""

    def __init__(self, store_name: str):
        super().__init__(store_name)
        self._prices = MOCK_PRICES.get(store_name.lower(), {})

    def get_price(self, product_id: str, product_name: str) -> PriceResult | None:
        if product_id not in self._prices:
            return None
        price, offer = self._prices[product_id]
        return PriceResult(
            product_id=product_id,
            product_name=product_name,
            store=self.store_name,
            price=price,
            unit="st",
            offer=offer,
        )
