from __future__ import annotations

import re
from difflib import get_close_matches
from functools import lru_cache
from pathlib import Path

import cv2
import easyocr
import numpy as np


# ============================================================
# OCR READER
# ============================================================

@lru_cache(maxsize=1)
def get_ocr_reader():
    print("Loading EasyOCR...")

    reader = easyocr.Reader(
        ["en"],
        gpu=False,
    )

    print("EasyOCR loaded successfully")
    return reader


# ============================================================
# BASIC TEXT NORMALIZATION
# ============================================================

def normalize_text(text: str) -> str:
    text = str(text).replace("\n", " ")

    return " ".join(text.split())


# ============================================================
# SEMANTIC NORMALIZATION
# ============================================================

def normalize_semantic_text(text: str) -> str:
    text = normalize_text(text).lower()

    replacements = {
        # Head & Shoulders OCR errors
        "head shoulders": "head & shoulders",
        "headandshoulders": "head & shoulders",
        "headeshoulders": "head & shoulders",
        "heade shoulders": "head & shoulders",

        # Shampoo OCR errors
        "shampooing": "shampoo",
        "shampoolng": "shampoo",
        "shampooln": "shampoo",
        "shampu": "shampoo",

        # Variant OCR errors
        "2a1": "2 in 1",
        "2:1": "2 in 1",
        "2-1": "2 in 1",
        "classicclean": "classic clean",

        # Other common errors
        "anti dandruff": "anti-dandruff",
    }

    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    return " ".join(text.split())


# ============================================================
# IMAGE LOADING
# ============================================================

def load_image(
    image_path: str | Path,
) -> np.ndarray:

    image = cv2.imread(str(image_path))

    if image is None:
        raise ValueError(
            f"Could not read image: {image_path}"
        )

    height, width = image.shape[:2]

    # Keep OCR reasonably fast on large images.
    if width > 900:
        scale = 900 / width

        image = cv2.resize(
            image,
            (
                int(width * scale),
                int(height * scale),
            ),
            interpolation=cv2.INTER_AREA,
        )

    return image


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess_image(
    image: np.ndarray,
) -> np.ndarray:

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    contrast = clahe.apply(gray)

    sharpen_kernel = np.array(
        [
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0],
        ],
        dtype=np.float32,
    )

    sharpened = cv2.filter2D(
        contrast,
        -1,
        sharpen_kernel,
    )

    return sharpened


# ============================================================
# OCR
# ============================================================

def run_ocr(
    image: np.ndarray,
) -> list[str]:

    reader = get_ocr_reader()

    print("Running OCR pass 1/1...")

    results = reader.readtext(
        image,
        detail=0,
        paragraph=False,
        batch_size=1,
        workers=0,
    )

    lines = []

    for item in results:
        clean = normalize_text(item)

        if clean and clean not in lines:
            lines.append(clean)

    return lines


# ============================================================
# ATTRIBUTE HELPER
# ============================================================

def add_attribute(
    attributes: dict,
    category: str,
    value: str,
    confidence: str,
    source: str,
):
    """
    Add an attribute while preventing duplicate values.
    """

    value = normalize_text(value)

    existing_values = attributes.get(
        category,
        [],
    )

    for item in existing_values:
        if (
            item.get("value", "").lower()
            == value.lower()
        ):
            # Prefer high-confidence evidence if we later
            # discover the same value with stronger evidence.
            if (
                confidence == "high"
                and item.get("confidence") != "high"
            ):
                item["confidence"] = "high"
                item["source"] = source

            return

    attributes[category].append(
        {
            "value": value,
            "confidence": confidence,
            "source": source,
        }
    )


# ============================================================
# NUMERIC ATTRIBUTE EXTRACTION
# ============================================================

def extract_numeric_attributes(
    text: str,
) -> dict:

    text = normalize_text(text)

    attributes = {
        "price": [],
        "weight": [],
        "volume": [],
        "wattage": [],
        "voltage": [],
        "quantity": [],
        "storage": [],
        "dimensions": [],
    }

    # ========================================================
    # PRICE — HIGH CONFIDENCE
    # ========================================================

    price_patterns = [
        (
            r"₹\s*(\d+(?:[.,]\d{1,2})?)",
            "₹",
        ),
        (
            r"\bRs\.?\s*(\d+(?:[.,]\d{1,2})?)",
            "₹",
        ),
        (
            r"\bINR\s*(\d+(?:[.,]\d{1,2})?)",
            "₹",
        ),
        (
            r"\$\s*(\d+(?:[.,]\d{1,2})?)",
            "$",
        ),
        (
            r"\bUSD\s*(\d+(?:[.,]\d{1,2})?)",
            "$",
        ),
    ]

    for pattern, symbol in price_patterns:
        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        for number in matches:
            add_attribute(
                attributes,
                "price",
                f"{symbol}{number}",
                "high",
                "currency explicitly detected",
            )

    # ========================================================
    # PRICE — MEDIUM CONFIDENCE
    # ========================================================

    # Only use this when no explicit currency price exists.
    #
    # Example:
    # "Only 65"
    #
    # This is deliberately medium confidence because "Only"
    # does not guarantee that the number is a price.

    if not attributes["price"]:
        matches = re.findall(
            r"\bonly\s*[-:]?\s*"
            r"(\d+(?:[.,]\d{1,2})?)\b",
            text,
            flags=re.IGNORECASE,
        )

        for number in matches[:1]:
            add_attribute(
                attributes,
                "price",
                number,
                "medium",
                "price-like context; currency not detected",
            )

    # ========================================================
    # VOLUME — HIGH CONFIDENCE
    # ========================================================

    volume_pattern = (
        r"\b(\d+(?:\.\d+)?)\s*"
        r"(ml|milliliters?|millilitres?|"
        r"l|liters?|litres?|fl\s*oz)\b"
    )

    matches = re.findall(
        volume_pattern,
        text,
        flags=re.IGNORECASE,
    )

    for number, unit in matches:
        unit_lower = unit.lower()

        if (
            unit_lower == "ml"
            or unit_lower.startswith("millil")
        ):
            normalized_unit = "ml"

        elif (
            unit_lower == "l"
            or unit_lower.startswith("liter")
            or unit_lower.startswith("litre")
        ):
            normalized_unit = "L"

        else:
            normalized_unit = "fl oz"

        add_attribute(
            attributes,
            "volume",
            f"{number} {normalized_unit}",
            "high",
            "exact OCR volume unit",
        )

    # ========================================================
    # VOLUME — OCR RECOVERY
    # ========================================================

    # Examples observed/expected:
    #
    # 65 ioeml
    # 65 ioml
    # 65 touml
    # 65 toeml
    # 100 rnl
    # 500 m1

    corrupted_volume_pattern = (
        r"\b(\d+(?:\.\d+)?)\s*"
        r"(?:"
        r"ioeml|ioml|ioe?ml|"
        r"toeml|touml|"
        r"rnl|rni|"
        r"m1|"
        r"eml|oml|iml"
        r")\b"
    )

    matches = re.findall(
        corrupted_volume_pattern,
        text,
        flags=re.IGNORECASE,
    )

    for number in matches:
        add_attribute(
            attributes,
            "volume",
            f"{number} ml",
            "medium",
            "OCR-corrupted ml unit recovered",
        )

    # ========================================================
    # WEIGHT — HIGH CONFIDENCE
    # ========================================================

    weight_pattern = (
        r"\b(\d+(?:\.\d+)?)\s*"
        r"(kg|kilograms?|"
        r"g|gm|grams?|"
        r"mg|lbs?|pounds?)\b"
    )

    matches = re.findall(
        weight_pattern,
        text,
        flags=re.IGNORECASE,
    )

    for number, unit in matches:
        unit_lower = unit.lower()

        if (
            unit_lower == "kg"
            or unit_lower.startswith("kilogram")
        ):
            normalized_unit = "kg"

        elif unit_lower in {
            "g",
            "gm",
            "gram",
            "grams",
        }:
            normalized_unit = "g"

        elif (
            unit_lower == "mg"
            or unit_lower.startswith("milligram")
        ):
            normalized_unit = "mg"

        elif (
            unit_lower.startswith("lb")
            or unit_lower.startswith("pound")
        ):
            normalized_unit = "lb"

        else:
            normalized_unit = unit_lower

        add_attribute(
            attributes,
            "weight",
            f"{number} {normalized_unit}",
            "high",
            "exact OCR weight unit",
        )

    # ========================================================
    # WEIGHT — OCR RECOVERY
    # ========================================================

    # EasyOCR can occasionally read:
    #
    # 500 g
    #
    # as:
    #
    # 500 9
    #
    # This is only medium confidence.

    matches = re.findall(
        r"\b(\d{2,4})\s+9\b",
        text,
        flags=re.IGNORECASE,
    )

    for number in matches:
        numeric_value = int(number)

        if 10 <= numeric_value <= 5000:
            add_attribute(
                attributes,
                "weight",
                f"{number} g",
                "medium",
                "possible OCR g→9 recovery",
            )

    # ========================================================
    # WATTAGE
    # ========================================================

    wattage_pattern = (
        r"\b(\d+(?:\.\d+)?)\s*"
        r"(?:w|watt|watts)\b"
    )

    matches = re.findall(
        wattage_pattern,
        text,
        flags=re.IGNORECASE,
    )

    for number in matches:
        add_attribute(
            attributes,
            "wattage",
            f"{number} W",
            "high",
            "exact OCR wattage unit",
        )

    # ========================================================
    # VOLTAGE
    # ========================================================

    voltage_pattern = (
        r"\b(\d+(?:\.\d+)?)\s*"
        r"(?:v|volt|volts)\b"
    )

    matches = re.findall(
        voltage_pattern,
        text,
        flags=re.IGNORECASE,
    )

    for number in matches:
        add_attribute(
            attributes,
            "voltage",
            f"{number} V",
            "high",
            "exact OCR voltage unit",
        )

    # ========================================================
    # QUANTITY
    # ========================================================

    quantity_pattern = (
        r"\b(\d+)\s*"
        r"(pack|packs|pcs|"
        r"piece|pieces|count|ct)\b"
    )

    matches = re.findall(
        quantity_pattern,
        text,
        flags=re.IGNORECASE,
    )

    for number, unit in matches:
        add_attribute(
            attributes,
            "quantity",
            f"{number} {unit.lower()}",
            "high",
            "exact OCR quantity unit",
        )

    # ========================================================
    # STORAGE
    # ========================================================

    storage_pattern = (
        r"\b(\d+(?:\.\d+)?)\s*"
        r"(MB|GB|TB)\b"
    )

    matches = re.findall(
        storage_pattern,
        text,
        flags=re.IGNORECASE,
    )

    for number, unit in matches:
        add_attribute(
            attributes,
            "storage",
            f"{number} {unit.upper()}",
            "high",
            "exact OCR storage unit",
        )

    # ========================================================
    # DIMENSIONS
    # ========================================================

    dimensions_pattern = (
        r"\b"
        r"(\d+(?:\.\d+)?)"
        r"\s*(?:x|×)\s*"
        r"(\d+(?:\.\d+)?)"
        r"(?:"
        r"\s*(?:x|×)\s*"
        r"(\d+(?:\.\d+)?)"
        r")?"
        r"\s*"
        r"(cm|mm|inch|inches|in)\b"
    )

    matches = re.findall(
        dimensions_pattern,
        text,
        flags=re.IGNORECASE,
    )

    for first, second, third, unit in matches:
        unit_lower = unit.lower()

        if unit_lower in {
            "inch",
            "inches",
            "in",
        }:
            normalized_unit = "in"
        else:
            normalized_unit = unit_lower

        if third:
            value = (
                f"{first} × {second} × "
                f"{third} {normalized_unit}"
            )
        else:
            value = (
                f"{first} × {second} "
                f"{normalized_unit}"
            )

        add_attribute(
            attributes,
            "dimensions",
            value,
            "high",
            "exact OCR dimension pattern",
        )

    return attributes


# ============================================================
# PRODUCT TYPE DATABASE
# ============================================================

PRODUCT_TYPES = {
    "shampoo": [
        "shampoo",
        "shampooing",
        "shampu",
        "shampoolng",
    ],

    "conditioner": [
        "conditioner",
        "conditioning",
        "conditoner",
    ],

    "soap": [
        "soap",
    ],

    "lotion": [
        "lotion",
        "body lotion",
    ],

    "cream": [
        "cream",
    ],

    "toothpaste": [
        "toothpaste",
    ],

    "laptop": [
        "laptop",
        "notebook",
    ],

    "phone": [
        "phone",
        "smartphone",
        "mobile",
    ],

    "headphones": [
        "headphones",
        "headphone",
        "earphones",
        "earbuds",
    ],

    "charger": [
        "charger",
        "adapter",
    ],

    "printer": [
        "printer",
    ],

    "camera": [
        "camera",
    ],

    "television": [
        "television",
        "tv",
    ],
}


# ============================================================
# PRODUCT TYPE DETECTION
# ============================================================

def detect_product_type(
    text: str,
) -> str | None:

    semantic_text = normalize_semantic_text(
        text
    )

    # --------------------------------------------------------
    # 1. DIRECT MATCH
    # --------------------------------------------------------

    for canonical, variants in PRODUCT_TYPES.items():
        for variant in variants:
            if variant in semantic_text:
                return canonical.title()

    # --------------------------------------------------------
    # 2. FUZZY TOKEN MATCH
    # --------------------------------------------------------

    tokens = re.findall(
        r"[a-zA-Z]+",
        semantic_text,
    )

    all_variants = []
    variant_to_type = {}

    for canonical, variants in PRODUCT_TYPES.items():
        for variant in variants:

            # Fuzzy token matching is useful primarily for
            # single-word product-type variants.
            if " " not in variant:
                all_variants.append(variant)
                variant_to_type[variant] = canonical

    for token in tokens:
        matches = get_close_matches(
            token,
            all_variants,
            n=1,
            cutoff=0.78,
        )

        if matches:
            return variant_to_type[
                matches[0]
            ].title()

    return None


# ============================================================
# BRAND DETECTION
# ============================================================

def detect_brand(
    text: str,
) -> str | None:

    semantic_text = normalize_semantic_text(
        text
    )

    # ========================================================
    # HEAD & SHOULDERS
    # ========================================================

    head_shoulders_patterns = [
        "head & shoulders",
        "head shoulders",
        "headeshoulders",
        "headandshoulders",
        "heade shoulders",
    ]

    for pattern in head_shoulders_patterns:
        if pattern in semantic_text:
            return "Head & Shoulders"

    # ========================================================
    # K.P. NAMBOODIRI
    # ========================================================

    if "namboodiri" in semantic_text:
        return "K.P. Namboodiri's"

    # ========================================================
    # OTHER KNOWN BRANDS
    # ========================================================

    brand_patterns = {
        "Dell": [
            "dell",
        ],
        "Apple": [
            "apple",
        ],
        "Samsung": [
            "samsung",
        ],
        "Lenovo": [
            "lenovo",
        ],
        "Sony": [
            "sony",
        ],
        "HP": [
            "hp",
        ],
    }

    words = set(
        re.findall(
            r"[a-zA-Z]+",
            semantic_text,
        )
    )

    for brand, variants in brand_patterns.items():
        for variant in variants:
            if variant in words:
                return brand

    return None


# ============================================================
# VARIANT DETECTION
# ============================================================

def detect_variant(
    text: str,
) -> str | None:

    semantic_text = normalize_semantic_text(
        text
    )

    parts = []

    # ========================================================
    # 2 IN 1
    # ========================================================

    if "2 in 1" in semantic_text:
        parts.append(
            "2 in 1"
        )

    # ========================================================
    # CLASSIC CLEAN
    # ========================================================

    if "classic clean" in semantic_text:
        parts.append(
            "Classic Clean"
        )

    # ========================================================
    # ANTI-DANDRUFF
    # ========================================================

    if (
        "anti-dandruff" in semantic_text
        or "anti dandruff" in semantic_text
        or "dandruff" in semantic_text
    ):
        parts.append(
            "Anti-Dandruff"
        )

    if not parts:
        return None

    return " | ".join(parts)


# ============================================================
# MAIN EXTRACTION FUNCTION
# ============================================================

def extract_product_attributes(
    image_path: str | Path,
) -> dict:

    image_path = Path(
        image_path
    )

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    # ========================================================
    # 1. LOAD IMAGE
    # ========================================================

    image = load_image(
        image_path
    )

    # ========================================================
    # 2. PREPROCESS IMAGE
    # ========================================================

    processed_image = preprocess_image(
        image
    )

    # ========================================================
    # 3. OCR
    # ========================================================

    ocr_lines = run_ocr(
        processed_image
    )

    ocr_text = normalize_text(
        " ".join(ocr_lines)
    )

    # ========================================================
    # 4. NUMERIC ATTRIBUTES
    # ========================================================

    attributes = extract_numeric_attributes(
        ocr_text
    )

    # ========================================================
    # 5. PRODUCT TYPE
    # ========================================================

    product_type = detect_product_type(
        ocr_text
    )

    # ========================================================
    # 6. BRAND
    # ========================================================

    brand = detect_brand(
        ocr_text
    )

    # ========================================================
    # 7. VARIANT
    # ========================================================

    variant = detect_variant(
        ocr_text
    )

    # ========================================================
    # 8. FINAL RESPONSE
    # ========================================================

    return {
        "ocr_text": ocr_text,
        "ocr_lines": ocr_lines,
        "product_type": product_type,
        "brand": brand,
        "variant": variant,
        "attributes": attributes,
    }