"""
product_catalogue.py
====================
Catalogue of product categories (4-digit HS codes) to analyse as candidate
import opportunities from China into Spain.

Each HS code (Harmonized System) identifies a product family. We work at the
4-digit level (heading): granular enough to tell sectors apart, broad enough
to have stable trade volumes.

This list is the "search universe": the analysis scores each category and
tells you which are worth pursuing. Extend or trim it to taste.

Code reference: https://www.taric.es / https://ec.europa.eu/taxation_customs
"""

# Mapping: HS code -> (readable name, thematic group)
# Consumer durables with B2B potential in Spain.
PRODUCT_CATALOGUE: dict[str, tuple[str, str]] = {
    # --- Furniture & home ---
    "9401": ("Seats and sofas", "Furniture"),
    "9403": ("Other furniture and parts", "Furniture"),
    "9404": ("Mattresses, cushions, bedding", "Furniture"),
    "9405": ("Lighting fixtures and lamps", "Home"),
    "6302": ("Bed, table and bath linen", "Home textile"),
    "6911": ("Porcelain tableware", "Home"),
    "7013": ("Glassware for table and kitchen", "Home"),

    # --- Decoration & gifts ---
    "4420": ("Wood marquetry and decorative objects", "Decoration"),
    "6913": ("Ceramic statuettes and decorative objects", "Decoration"),
    "9505": ("Festive and seasonal decoration articles", "Decoration"),

    # --- Consumer electronics & small appliances ---
    "8516": ("Small thermal appliances", "Appliances"),
    "8509": ("Electromechanical household appliances", "Appliances"),
    "8471": ("Computers and peripherals", "Electronics"),
    "8517": ("Phones and communication equipment", "Electronics"),
    "8544": ("Electrical cables and conductors", "Electronics"),

    # --- Sport, leisure & outdoor ---
    "9506": ("Sports and gym articles", "Sport & leisure"),
    "8712": ("Bicycles (non-motorised)", "Sport & leisure"),
    "6601": ("Umbrellas and parasols", "Sport & leisure"),
    "9503": ("Toys and scale models", "Sport & leisure"),

    # --- Textile & accessories ---
    "4202": ("Bags, suitcases and leather goods", "Accessories"),
    "6404": ("Footwear with textile uppers", "Footwear"),
    "6116": ("Knitted gloves", "Textile"),

    # --- Hardware, garden & light construction ---
    "8302": ("Metal fittings and mountings", "Hardware"),
    "3924": ("Plastic articles for home and kitchen", "Home"),
}


def get_valid_hs_codes() -> list[str]:
    """Return only the real HS codes (usable against the API)."""
    return [code for code in PRODUCT_CATALOGUE if code.isdigit()]


def label_for(code: str) -> str:
    """Readable name for an HS code."""
    entry = PRODUCT_CATALOGUE.get(code)
    return entry[0] if entry else code


def group_for(code: str) -> str:
    """Thematic group for an HS code."""
    entry = PRODUCT_CATALOGUE.get(code)
    return entry[1] if entry else "Other"


if __name__ == "__main__":
    print(f"Catalogue with {len(PRODUCT_CATALOGUE)} categories")
    print(f"Valid HS codes for the API: {len(get_valid_hs_codes())}")
    for code in get_valid_hs_codes():
        print(f"  {code}  {label_for(code):45s} [{group_for(code)}]")
