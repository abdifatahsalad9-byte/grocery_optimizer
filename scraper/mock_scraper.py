from .base_scraper import BaseScraper, PriceResult

# Willys = verkliga priser från kvitton apr-maj 2026
# Övriga butiker = uppskattade priser relativt Willys:
#   Lidl:      -15 %  (billigast)
#   Coop:       +3 %
#   City Gross: +5 %
#   ICA:        +7 %
#   Hemköp:    +10 %
#   Mathem:    +15 %  (online-tillägg)

_W = {
    # Kött & Fisk
    "kycklingfile":       131.54,
    "kycklingkebab":       66.15,
    "kycklingleårfile":    56.68,
    "kycklinginnerfile":   47.22,
    # Mejeri & Kyl
    "mjolk":               18.30,
    "smor":                61.42,
    "normalsalt_smor":     51.50,
    "agg":                 59.90,
    "grekisk_yoghurt":     35.86,
    "yoghurt":             28.29,
    "yoghurt_vanilj":      20.50,
    "turkisk_yoghurt":     26.40,
    "crunchy_yoghurt":     31.04,
    "min_yoghurt":         24.51,
    "matgradde":           24.51,
    "vispgradde":          30.19,
    "gradde":              32.65,
    "graddfil":            19.77,
    "parmigiano":          56.68,
    "vaniljsas":           25.45,
    "apelsinjuice":        23.56,
    "appeljuice":          17.90,
    # Frukt & Grönt
    "avokado":             39.90,
    "banan":               32.49,
    "citron":              15.90,
    "tomat_baby":          40.60,
    "gurka":               15.90,
    "paprika":             27.90,
    "isbergssallad":       17.00,
    "zucchini":             9.90,
    "potatis":             19.44,
    "gul_lok":              7.90,
    "rod_lok":             16.90,
    "vitlok":              11.90,
    "majskolv":            21.90,
    "kiwi":                37.60,
    "mango":               20.72,
    # Barn
    "blojor":             122.90,
    "nan_pro":            131.45,
    "fruktmums":           94.54,
    "fruktgrot":           46.27,
    "min_yoghurt_barn":    24.51,
    "katrinplommon":       10.31,
    "baby_wash":           34.90,
    # Skafferi
    "pasta":                8.42,
    "fusilli":             40.60,
    "makaroner":           14.10,
    "bulgur":              19.77,
    "strosocker":          22.61,
    "nudlar_orient":        4.63,
    "nudlar_svamp":         4.63,
    "olivolja":            75.61,
    "rapsolja":            66.15,
    "tomatpure":           23.56,
    "kakao":               37.76,
    "bakchoklad":          38.70,
    "senap":               15.99,
    "ketchup":             31.13,
    "sriracha":            44.38,
    "salsa":               15.04,
    "cheddar_dip":         28.29,
    "dressing":            16.90,
    "dressing_jalpeno":    16.90,
    "citron_pressad":       9.36,
    "taco_spice":          25.45,
    "tortilla":            39.27,
    "ljus_sirap":          15.04,
    "crisp_wheat":         15.61,
    "multivitamin":        19.50,
    # Bröd
    "polarvete":           34.92,
    "hamburgerbrod":       31.70,
    "korvbrod":            19.68,
    "lingongrova":         22.87,
    "levain":              35.86,
    "skargardskaka":       29.67,
    "orientbrod":           9.36,
    # Hem & Hygien
    "diskmedel":           69.90,
    "skoljmedel":          47.90,
    "hushallspapper":      29.90,
    "toapapper":           27.90,
    "tvattlapp":           47.90,
    "microfiber":          29.90,
    "rengoring":            6.90,
    "refill_mopp":         19.90,
    "carpet_care":         59.90,
    "avfallspasar":        19.90,
    "pas_frys":            16.90,
    "pappkasse":            4.90,
    "engangshyvlar":       28.90,
    "twister_medium":      16.90,
    "twister_soft":        16.90,
    "mellanrumsborst":     34.90,
    "tandtradsbygel":      39.90,
    "max_fresh":           19.90,
    "dreamlengths_sch":    36.90,
    "dreamlengths_balsam": 36.90,
    "deospray":            34.90,
    "vaselin":             18.90,
    "vatservetter":        11.90,
    # Godis & Glass
    "strawb_cream":        50.06,
    "bj_glass":            58.58,
    "almond_cone":         28.39,
    "vanilla_pecan":       58.58,
    "pommes_strips":       33.97,
}

def _scale(prices: dict, factor: float) -> dict:
    return {k: round(v * factor, 2) for k, v in prices.items()}

MOCK_PRICES = {
    "willys":    {k: (v, "") for k, v in _W.items()},
    "lidl":      {k: (v, "") for k, v in _scale(_W, 0.85).items()},
    "coop":      {k: (v, "") for k, v in _scale(_W, 1.03).items()},
    "citygross": {k: (v, "") for k, v in _scale(_W, 1.05).items()},
    "ica":       {k: (v, "") for k, v in _scale(_W, 1.07).items()},
    "hemkop":    {k: (v, "") for k, v in _scale(_W, 1.10).items()},
    "mathem":    {k: (v, "") for k, v in _scale(_W, 1.15).items()},
}

# Erbjudanden per butik (produkt-id: erbjudandetext)
OFFERS = {
    "willys":    {"blojor": "Köp 2 betala för 1.5"},
    "ica":       {"paprika": "3 för 79 kr", "agg": "Veckans vara"},
    "coop":      {"banan": "Ekologiskt veckopris"},
    "lidl":      {"kycklingfile": "Veckans fynd"},
    "hemkop":    {},
    "citygross": {},
    "mathem":    {"nan_pro": "Fri frakt på blöjor & modersmjölk"},
}

for store, offers in OFFERS.items():
    for pid, offer_text in offers.items():
        if pid in MOCK_PRICES[store]:
            price = MOCK_PRICES[store][pid][0]
            MOCK_PRICES[store][pid] = (price, offer_text)


class MockScraper(BaseScraper):
    """Testskraper med hårdkodade priser. Byt ut mot riktiga scrapers per butik."""

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
            is_real=False,
        )
