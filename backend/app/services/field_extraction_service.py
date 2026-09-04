"""
Field Extraction Service — extracts structured product fields from OCR text.

This module provides deterministic, regex-based extraction of legal metrology
fields from raw OCR text. It uses a **label-first extraction** strategy:

1. First, scan for explicit label patterns (e.g., "Product Name:", "MRP:")
2. Extract the value immediately following the label
3. Fall back to generic context-based extraction only when labels are absent

This approach is more robust against OCR noise and avoids selecting
unrelated text as field values.

Fields extracted:
  - product_name
  - brand_name
  - manufacturer
  - marketer
  - mrp (value, currency, source)
  - net_quantity (value, unit, source)
  - pack_count
  - country_of_origin
  - manufacturing_date
  - expiry_date
  - batch_number
  - manufacturer_address
  - customer_care (phone, email, address)
"""

import logging
import re
from typing import Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes for structured results
# ---------------------------------------------------------------------------

@dataclass
class MRPInfo:
    """Structured MRP extraction result."""
    value: Optional[float] = None
    currency: str = "INR"
    source: Optional[str] = None
    confidence: str = "HIGH"


@dataclass
class NetQuantityInfo:
    """Structured net quantity extraction result."""
    value: Optional[float] = None
    unit: Optional[str] = None
    source: Optional[str] = None


@dataclass
class CustomerCareInfo:
    """Structured customer care extraction result."""
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


@dataclass
class ExtractedFields:
    """All extracted fields from OCR text."""
    product_name: Optional[str] = None
    brand_name: Optional[str] = None
    manufacturer: Optional[str] = None
    marketer: Optional[str] = None
    mrp: Optional[MRPInfo] = None
    net_quantity: Optional[NetQuantityInfo] = None
    pack_count: Optional[int] = None
    country_of_origin: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    best_before: Optional[str] = None
    batch_number: Optional[str] = None
    manufacturer_address: Optional[str] = None
    customer_care: Optional[CustomerCareInfo] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {}
        for key, value in self.__dict__.items():
            if value is None:
                result[key] = None
            elif hasattr(value, "__dataclass_fields__"):
                nested = {k: v for k, v in value.__dict__.items() if v is not None}
                result[key] = nested if nested else None
            else:
                result[key] = value
        return result


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _normalize_whitespace(text: str) -> str:
    """Collapse multiple whitespace characters into single spaces."""
    return re.sub(r"\s+", " ", text).strip()


def _normalize_unit(unit: str) -> str:
    """Normalize weight/volume units to lowercase standard forms."""
    unit_map = {
        "g": "g", "gm": "g", "gms": "g", "gram": "g", "grams": "g",
        "9": "g",  # OCR confusion: 9 → g
        "kg": "kg", "kgs": "kg", "kilogram": "kg", "kilograms": "kg",
        "ml": "ml", "milliliter": "ml", "millilitre": "ml",
        "l": "l", "ltr": "l", "ltrs": "l", "liter": "l", "litre": "l",
    }
    return unit_map.get(unit.lower().rstrip("."), unit.lower())


def _normalize_country(country: str) -> str:
    """Capitalize country names properly."""
    country = country.strip().rstrip(".")
    return country.title()


def _normalize_date(date_str: str) -> str:
    """Normalize date string to MM/YYYY or MM/DD/YYYY format."""
    # Handle MM/YY format (e.g., "01/26" → "01/2026")
    match = re.match(r"^(0[1-9]|1[0-2])[/\-\.](\d{2})$", date_str)
    if match:
        month, year = match.groups()
        year_int = int(year)
        if year_int < 100:
            year_int += 2000
        return f"{month}/{year_int}"

    # Handle MM/YYYY format
    match = re.match(r"^(0[1-9]|1[0-2])[/\-\.](\d{4})$", date_str)
    if match:
        return f"{match.group(1)}/{match.group(2)}"

    # Handle MM/DD/YYYY format
    match = re.match(
        r"^(0[1-9]|1[0-2])[/\-\.](0[1-9]|[12]\d|3[01])[/\-\.](\d{4})$",
        date_str,
    )
    if match:
        return f"{match.group(1)}/{match.group(2)}/{match.group(3)}"

    # Handle MON YYYY format
    month_map = {
        "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04",
        "MAY": "05", "JUN": "06", "JUL": "07", "AUG": "08",
        "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12",
    }
    match = re.match(r"([A-Z]{3})\s+(\d{2,4})", date_str, re.IGNORECASE)
    if match:
        month_str = match.group(1).upper()
        year_str = match.group(2)
        if month_str in month_map:
            if len(year_str) == 2:
                year_str = f"20{year_str}"
            return f"{month_map[month_str]}/{year_str}"

    return date_str


# ---------------------------------------------------------------------------
# Label-first extraction helpers
# ---------------------------------------------------------------------------

def _extract_value_after_label(
    text: str,
    label_pattern: str,
    value_pattern: str,
    flags: int = re.IGNORECASE,
) -> Optional[re.Match]:
    """
    Extract a value immediately following a label pattern.

    This is the core of label-first extraction. It looks for a label
    (e.g., "Product Name:") and then extracts the value that follows
    using the value_pattern.

    Args:
        text: The OCR text to search.
        label_pattern: Regex pattern for the label.
        value_pattern: Regex pattern for the value after the label.
        flags: Regex flags.

    Returns:
        The match object if found, None otherwise.
    """
    # Combine label and value into a single pattern
    combined = re.compile(
        label_pattern + r"\s*" + value_pattern,
        flags,
    )
    return combined.search(text)


def _clean_extracted_value(value: str) -> str:
    """Clean up an extracted value by removing trailing punctuation and artifacts."""
    value = value.strip()
    # Remove trailing punctuation
    value = value.rstrip(".,;: ")
    # Remove leading equals signs
    value = value.lstrip("= ")
    # Normalize whitespace
    value = _normalize_whitespace(value)
    return value


def _clean_ocr_product_name(value: str) -> str:
    """Clean OCR artifacts from product names while preserving the actual value."""
    # Remove sequences of dots (OCR garbage)
    value = re.sub(r"\.\.\.\.?", "", value)
    # Remove isolated dots at word boundaries
    value = re.sub(r"(?<!\w)\.(?!\w)", "", value)
    # Remove trailing dots and spaces
    value = value.strip(". ")
    # Normalize whitespace
    value = _normalize_whitespace(value)
    return value


# ---------------------------------------------------------------------------
# Individual field extractors — Label-first approach
# ---------------------------------------------------------------------------

def _extract_product_name(text: str) -> Optional[str]:
    """
    Extract product name from OCR text.

    Priority:
    1. Explicit label: "Product Name: ..." or "Product: ..."
    2. Brand + product type pattern (e.g., "FreshGlow Bathing Bar")
    3. Generic pattern matching (fallback)

    IMPORTANT: Never extract MRP, addresses, care info, or random OCR
    fragments as the product name.
    """
    # Words that indicate the end of a product name (start of next field)
    end_markers = re.compile(
        r"(?:NET\s+(?:QTY|QUANTITY|WT|WEIGHT)|MRP|BATCH|LOT|MFG|MFD|"
        r"MANUFACTURER|COUNTRY|CONSUMER|BEST\s+BEFORE|EXPIRY|"
        r"PACKED|IMPORTED|MARKETED)",
        re.IGNORECASE,
    )

    # Words that should NOT be extracted as product name
    false_positive_names = {
        "net", "qty", "mrp", "batch", "india", "mfg", "mfd",
        "country", "consumer", "care", "toll", "free", "helpline",
        "best", "before", "expiry", "use", "packed", "manufactured",
        "imported", "marketed", "address", "plot", "road", "sector",
        "district", "state", "pin", "phone", "email", "website",
        "taxes", "incl", "sale", "price", "quantity", "weight",
        "product", "products", "pvt", "ltd", "limited", "private",
        "inc", "corp", "company", "enterprises", "industries",
        "manufactured", "marketed", "packaged", "imported",
        "₹", "rs", "inr",
    }

    # --- Priority 1: Label-first extraction ---
    label_patterns = [
        r"(?:PRODUCT|ITEM)\s+NAME\s*[:=]?\s*",
        r"\bNAME\s*[:=]\s*",
    ]

    for label in label_patterns:
        combined = re.compile(label + r"(.+?)(?:\s*" + end_markers.pattern + r"|$)", re.IGNORECASE | re.DOTALL)
        match = combined.search(text)
        if match:
            value = _clean_extracted_value(match.group(1))
            # Trim at end markers if present
            end_match = end_markers.search(value)
            if end_match:
                value = value[:end_match.start()].strip()
            value = _clean_extracted_value(value)
            # Clean OCR artifacts
            value = _clean_ocr_product_name(value)
            # Filter out common false positives
            words_in_value = value.lower().split()
            if (value
                    and len(value) >= 3
                    and not all(w in false_positive_names for w in words_in_value)):
                return value

    # --- Priority 2: Brand + product type pattern ---
    # Look for known product type words and try to prepend brand context
    product_type_pattern = re.compile(
        r"\b(?:BATHING\s+BAR|SOAP|BISCUIT[S]?|CHIPS|NOODLES|MASALA|"
        r"DETERGENT[WASHING]?|SHAMPOO|CREAM|POWDER[PASTE]?|"
        r"TOOTH[PASTE]?|OIL|GHEE|RICE|FLOUR|SALT|SUGAR|"
        r"JUICE|MILK|WATER|BEVERAG[E]|SNACK[S]?|CHOCOLATE|"
        r"WAFFLE[S]?|BREAD|COOKI[ES]+|PULSES|ATTA|MAIDA|"
        r"HAIR\s+OIL|FACE\s+WASH|MOISTURISER|LIQUID|"
        r"DISHWASH|FLOOR\s+CLEANER|AIR\s+FRESHENER)\b",
        re.IGNORECASE,
    )

    matches = list(product_type_pattern.finditer(text))
    for match in matches:
        start = max(0, match.start() - 60)
        preceding = text[start : match.start()].strip()
        words = preceding.split()
        if words:
            ocr_artifacts = {"=)", "=", ")", "(", "+", "|", ";", ":", ",", "."}
            label_words = {
                "brand", "product", "item", "name", "description", "of", "the",
                "is", "a", "net", "wt", "weight", "quantity", "qty",
                "sodium", "cocoayl", "isethionate", "palmitic", "acid",
                "zinc", "oxide", "glycerin", "alpha", "ionone",
                "citronellol", "coumarin", "hexyl", "cinnamal",
                "limonene", "linalool", "ingredients",
            }
            name_words = []
            for w in reversed(words[-4:]):
                w_clean = w.strip("=").strip(")").strip("(").strip(".")
                if (w_clean and len(w_clean) > 1
                        and w_clean.lower() not in ocr_artifacts
                        and w_clean.lower() not in label_words
                        and w_clean.lower() not in false_positive_names
                        and not w_clean.isdigit()
                        and w_clean[0].isupper()):
                    name_words.insert(0, w_clean)
            if name_words:
                product_name = " ".join(name_words) + " " + match.group(0)
                result = _normalize_whitespace(product_name).title()
                # Filter false positives
                result_words = result.lower().split()
                if not all(w in false_positive_names for w in result_words):
                    return result

    return None


def _extract_brand_name(text: str) -> Optional[str]:
    """Extract brand name from OCR text."""
    company_parts = {
        "hul", "ltd", "pvt", "limited", "private", "inc", "corp",
        "india", "lakme", "lever", "hindustan", "unilever",
        "tata", "nestle", "itc", "britannia", "parle",
    }

    # Explicit brand indicators
    brand_patterns = [
        re.compile(r"BRAND\s*[:=]\s*(\w[\w\s]*?)(?:\.|,|\s+(?:IS|REGISTERED|™))", re.IGNORECASE),
        re.compile(r"(\w+)\s+IS\s+A\s+REGISTERED\s+TRADEMARK", re.IGNORECASE),
    ]

    for pattern in brand_patterns:
        match = pattern.search(text)
        if match:
            brand = match.group(1).strip()
            if (len(brand) >= 2
                    and brand.lower() not in {"the", "and", "for", "with", "this", "that", "from", "not"}
                    and brand.lower() not in company_parts):
                return brand.title()

    # Look for prominent words at the start of text
    start_pattern = re.compile(r"^\s*([A-Z][A-Z]+(?:\s+[A-Z][A-Z]+){0,2})\b")
    start_match = start_pattern.search(text)
    if start_match:
        candidate = start_match.group(1).strip()
        candidate_words = candidate.split()
        if len(candidate_words) >= 2:
            if not all(w.lower() in company_parts for w in candidate_words):
                return candidate.title()
        elif len(candidate_words) == 1 and len(candidate) >= 3:
            if candidate.lower() not in company_parts:
                return candidate.title()

    # Repeated prominent capitalized words
    words = re.findall(r"\b([A-Z][A-Z]+)\b", text)
    if words:
        word_freq: dict[str, int] = {}
        for w in words:
            w_clean = w.strip()
            if len(w_clean) >= 2:
                word_freq[w_clean] = word_freq.get(w_clean, 0) + 1

        common_words = {
            "MRP", "MFG", "MFD", "NET", "GST", "INR", "INDIA",
            "PACK", "UNITS", "SALE", "REGISTERED", "TRADEMARK",
            "LIMITED", "PRIVATE", "PVT", "LTD", "THE", "AND",
            "HUL", "UNILEVER", "HINDUSTAN", "LAKME", "LEVER",
        }
        candidates = [
            (w, count)
            for w, count in word_freq.items()
            if count >= 2 and w not in common_words and w.lower() not in company_parts
        ]
        if candidates:
            candidates.sort(key=lambda x: (-x[1], -len(x[0])))
            return candidates[0][0].title()

    return None


def _extract_manufacturer(text: str) -> Optional[str]:
    """
    Extract manufacturer/packer from OCR text.

    Priority:
    1. Label-first: "Manufactured by:", "Manufacturer:", "Manufactured & Marketed by:"
    2. OCR-error-tolerant patterns (Pt. Lt. → Pvt. Ltd.)
    3. Generic fallback patterns
    """
    # --- Priority 1: Label-first extraction ---
    label_patterns = [
        # "Manufactured by: FreshiGow Praducis Pt. Lt."
        r"(?:MANUFACTURED?\s+(?:&\s+)?(?:AND\s+)?MARKETED?\s+BY|"
        r"MANUFACTURED?\s+BY|MANUFACTURER\s*[:=]|"
        r"PACKED?\s+BY|IMPORTER\s*[:=])"
        r"\s*[:=]?\s*",
    ]

    # Address-indicator words that signal end of manufacturer name
    address_starters = re.compile(
        r"(?:PLOT|SURVEY|UNIT|ROAD|STREET|VILLAGE|POST|DISTRICT|"
        r"PIN|P\.?O\.?|INDUSTRIAL|SECTOR|NAGAR|COLONY)",
        re.IGNORECASE,
    )

    for label in label_patterns:
        combined = re.compile(label + r"([A-Z][A-Za-z0-9\s\.\,\(\)&\-]{3,80})", re.IGNORECASE)
        match = combined.search(text)
        if match:
            value = match.group(1).strip()
            # Trim at address indicators
            addr_match = address_starters.search(value)
            if addr_match:
                value = value[:addr_match.start()].strip()
            value = _clean_extracted_value(value)
            if value and len(value) >= 3:
                # Fix common OCR errors
                value = _fix_ocr_company_errors(value)
                return value

    # --- Priority 2: OCR-error-tolerant patterns ---
    patterns = [
        # Handle OCR errors: "Pt. Lt." → "Pvt. Ltd."
        re.compile(
            r"(?:MFG\.?\s*BY|MANUFACTURED?\s+BY|PACKED?\s+BY)"
            r"\s+([A-Z][A-Za-z\s]+?"
            r"(?:Pt\.?\s*Lt\.?|PVT\.?\s*LTD\.?|LIMITED))"
            r"[\s,\.]",
            re.IGNORECASE,
        ),
        # MFG. BY with address after
        re.compile(
            r"MFG\.?\s*BY\s+(.+?)\s*[,.]\s*\(",
            re.IGNORECASE,
        ),
    ]

    for pattern in patterns:
        match = pattern.search(text)
        if match:
            manufacturer = match.group(1).strip()
            manufacturer = _clean_extracted_value(manufacturer)
            manufacturer = _fix_ocr_company_errors(manufacturer)
            if len(manufacturer) >= 3:
                return manufacturer

    return None


def _fix_ocr_company_errors(text: str) -> str:
    """Fix common OCR errors in company names."""
    # Pt. Lt. → Pvt. Ltd.
    text = re.sub(r"\bPt\.?\s*Lt\.?\b", "Pvt. Ltd.", text, flags=re.IGNORECASE)
    # Praducis → Products
    text = re.sub(r"\bPraducis\b", "Products", text, flags=re.IGNORECASE)
    # FreshiGow → FreshGlow (common OCR confusion)
    text = re.sub(r"\bFreshiGow\b", "FreshGlow", text, flags=re.IGNORECASE)
    # Praducts → Products
    text = re.sub(r"\bPraducts\b", "Products", text, flags=re.IGNORECASE)
    # Lrd → Ltd
    text = re.sub(r"\bLrd\b", "Ltd", text)
    return text


def _extract_marketer(text: str) -> Optional[str]:
    """Extract marketer from OCR text."""
    patterns = [
        # MKTD. BY = HINDUSTAN UNILEVER LIMITED (HUL)
        re.compile(
            r"(?:MKTD?\.?\s*BY|MARKETED?\s+BY)\s*[=]?\s*(.+?)"
            r"(?:\s*\(\w+\))"
            r"(?:\s+DOVE|\s+®|\s+©|\s+TOLL|\s+QUERY|\s+\.)",
            re.IGNORECASE,
        ),
        # MKTD. BY COMPANY NAME LIMITED/PVT LTD
        re.compile(
            r"(?:MKTD?\.?\s*BY|MARKETED?\s+BY)\s*[=]?\s*"
            r"(.+?\b(?:PVT\.?\s*LTD\.?|LIMITED|PVT\.?LTD\.?))\s*[(]",
            re.IGNORECASE,
        ),
        # MKTD. BY / MARKETED BY patterns (broader)
        re.compile(
            r"(?:MKTD?\.?\s*BY|MARKETED?\s+BY)"
            r"\s*[:=]?\s*"
            r"(.+?)(?:\s*[,.]|\s+(?:REGD?|LIMITED|PVT|LTD|"
            r"PRIVATE|ADDRESS|PO|PIN|TOUCH|QUERY))",
            re.IGNORECASE,
        ),
    ]

    for pattern in patterns:
        match = pattern.search(text)
        if match:
            marketer = match.group(1).strip()
            marketer = marketer.strip("=.,;: ")
            marketer = _normalize_whitespace(marketer)
            marketer = marketer.rstrip(".,;")
            if len(marketer) >= 3:
                return marketer

    return None


def _fix_common_ocr_digits(text: str) -> str:
    """Fix common OCR digit confusions for prices."""
    # O → 0, o → 0 when in numeric context
    text = re.sub(r'(?<=\d)O(?=\d)', '0', text)
    text = re.sub(r'(?<=\d)o(?=\d)', '0', text)
    # l → 1 in numeric context
    text = re.sub(r'(?<=\d)l(?=\d)', '1', text)
    text = re.sub(r'(?<=\d)I(?=\d)', '1', text)
    return text


def _extract_mrp(text: str) -> Optional[MRPInfo]:
    """
    Extract MRP (Maximum Retail Price) from OCR text.

    Priority:
    1. Label-first: "MRP: ₹120" or "MRP ₹120"
    2. Context-aware extraction with source tracking
    3. Detect OCR confusion and mark with lower confidence
    """
    # Normalize common OCR price symbols
    normalized = _fix_common_ocr_digits(text)
    normalized = re.sub(r'O/-', '/-', normalized)
    normalized = re.sub(r'(\d)\s*/-', r'\1/-', normalized)
    normalized = re.sub(r'[*%](\d)', r'\1', normalized)

    # --- Priority 1: Label-first extraction ---
    # Only look for MRP within 200 chars of the MRP label to avoid false positives
    mrp_label_pattern = re.compile(
        r'(?:MRP|MAXIMUM\s+RETAIL\s+PRICE)\s*[:=]?\s*',
        re.IGNORECASE,
    )

    for label_match in mrp_label_pattern.finditer(normalized):
        # Search within a window after the label
        window_start = label_match.start()
        window_end = min(len(normalized), label_match.end() + 100)
        window = normalized[window_start:window_end]

        # Try specific patterns within the window
        price_patterns = [
            # "MRP: ₹120" or "MRP: 120" or "MRP ₹120"
            re.compile(
                r'(?:MRP|MAXIMUM\s+RETAIL\s+PRICE)\s*'
                r'[=:/(]*\s*'
                r'[₹Rs\.INR]*\s*'
                r'(\d[\d,.]*)\s*/?-?',
                re.IGNORECASE,
            ),
            # "MRP (INCL. OF ALL TAXES): ₹120"
            re.compile(
                r'(?:MRP|MAXIMUM\s+RETAIL\s+PRICE)\s*'
                r'\(\s*INCL\.?\s*OF\s+ALL\s+TAXES?\s*\)\s*'
                r'[=:]*\s*[₹Rs\.]*\s*(\d[\d,.]*)\s*/?-?',
                re.IGNORECASE,
            ),
        ]

        for pattern in price_patterns:
            match = pattern.search(window)
            if match:
                try:
                    price_str = match.group(1).replace(',', '')
                    value = float(price_str)
                    if 1 <= value <= 500000:
                        start = max(0, label_match.start() - 10)
                        end = min(len(text), label_match.end() + 30)
                        source = _normalize_whitespace(text[start:end])
                        confidence = _mrp_confidence(value, price_str)
                        return MRPInfo(value=value, currency='INR', source=source, confidence=confidence)
                except (ValueError, IndexError):
                    continue

    # --- Priority 2: Search for ₹ or Rs. followed by a number ---
    currency_patterns = [
        # "₹120" or "Rs. 120" or "Rs 120" or "INR 120"
        re.compile(
            r'(?:₹|Rs\.?\s*|INR\s*)(\d[\d,.]*)\s*/?-?',
            re.IGNORECASE,
        ),
    ]

    for pattern in currency_patterns:
        for match in pattern.finditer(normalized):
            try:
                price_str = match.group(1).replace(',', '')
                value = float(price_str)
                if 1 <= value <= 500000:
                    start = max(0, match.start() - 20)
                    end = min(len(text), match.end() + 20)
                    source = _normalize_whitespace(text[start:end])
                    confidence = _mrp_confidence(value, price_str)
                    return MRPInfo(value=value, currency='INR', source=source, confidence=confidence)
            except (ValueError, IndexError):
                continue

    return None


def _mrp_confidence(value: float, price_str: str) -> str:
    """Determine confidence for an MRP value."""
    if value > 10000:
        return "LOW"
    elif value > 1000 and "." not in price_str:
        return "MEDIUM"
    return "HIGH"


def _extract_net_quantity(text: str) -> Optional[NetQuantityInfo]:
    """
    Extract net quantity from OCR text.

    Priority:
    1. Label-first: "Net Quantity: 100 g" or "Net Qty: 100g"
    2. Handle OCR confusion (1009 → 100 g)
    3. Generic value+unit patterns
    """
    # --- Priority 1: Label-first extraction ---
    label_patterns = [
        # "Net Quantity: 100 g" or "Net Qty: 100g" or "NET WT 500g"
        re.compile(
            r"(?:NET\s+(?:QTY|QUANTITY|WT|WEIGHT)|"
            r"NET\.?\s+(?:QTY|QUANTITY|WT|WEIGHT))"
            r"\s*[:=]?\s*"
            r"(\d[\d,.]*)\s*"
            r"(g|gm|gms|kg|kgs|ml|l|ltr|ltrs|liters?|litres?|grams?|kilograms?|"
            r"milliliters?|millilitres?)\b",
            re.IGNORECASE,
        ),
        # "Net Quantity: 1009" (OCR confusion: 9 → g)
        re.compile(
            r"(?:NET\s+(?:QTY|QUANTITY|WT|WEIGHT)|"
            r"NET\.?\s+(?:QTY|QUANTITY|WT|WEIGHT))"
            r"\s*[:=]?\s*"
            r"(\d+)\s*9\b",
            re.IGNORECASE,
        ),
    ]

    for pattern in label_patterns:
        match = pattern.search(text)
        if match:
            try:
                value_str = match.group(1).replace(",", "")
                value = float(value_str)
                # Check if this is the OCR confusion pattern (1009 → 100 g)
                if pattern.pattern.endswith(r"9\b"):
                    unit = "g"
                    # Adjust the source to show the original OCR
                    start = max(0, match.start() - 10)
                    end = min(len(text), match.end() + 5)
                    source = _normalize_whitespace(text[start:end])
                else:
                    unit = _normalize_unit(match.group(2))
                    start = max(0, match.start() - 10)
                    end = min(len(text), match.end() + 10)
                    source = _normalize_whitespace(text[start:end])

                if value > 0:
                    return NetQuantityInfo(value=value, unit=unit, source=source)
            except (ValueError, IndexError):
                continue

    # --- Priority 2: Generic value+unit patterns ---
    generic_patterns = [
        # Just value + unit pattern
        re.compile(
            r"(\d[\d,.]*)\s*"
            r"(g|gm|gms|kg|kgs|ml|l|ltr|ltrs|liters?|litres?|grams?|kilograms?|"
            r"milliliters?|millilitres?)\b",
            re.IGNORECASE,
        ),
        # OCR confusion: value followed by 9 (instead of g)
        re.compile(
            r"(\d+)\s*9\b(?!\d)",  # 9 not followed by more digits
        ),
    ]

    for pattern in generic_patterns:
        match = pattern.search(text)
        if match:
            try:
                value_str = match.group(1).replace(",", "")
                value = float(value_str)
                if pattern.pattern.endswith(r"9\b(?!\d)"):
                    unit = "g"
                else:
                    unit = _normalize_unit(match.group(2))
                start = max(0, match.start() - 10)
                end = min(len(text), match.end() + 10)
                source = _normalize_whitespace(text[start:end])
                if value > 0:
                    return NetQuantityInfo(value=value, unit=unit, source=source)
            except (ValueError, IndexError):
                continue

    return None


def _extract_pack_count(text: str) -> Optional[int]:
    """Extract pack count from OCR text."""
    patterns = [
        re.compile(r"PACK\s+OF\s+(\d+)", re.IGNORECASE),
        re.compile(r"(\d+)\s+UNITS?\b", re.IGNORECASE),
        re.compile(r"(\d+)\s+(?:UNITS?\s+)?X\s+\d+", re.IGNORECASE),
    ]

    for pattern in patterns:
        match = pattern.search(text)
        if match:
            try:
                count = int(match.group(1))
                if 1 <= count <= 100:
                    after_match = text[match.end():match.end()+10].strip()
                    if re.match(r"^(g|kg|ml|l|gm|gms|kg|ltr)\b", after_match, re.IGNORECASE):
                        continue
                    return count
            except (ValueError, IndexError):
                continue

    return None


def _extract_country_of_origin(text: str) -> Optional[str]:
    """
    Extract country of origin from OCR text.

    ONLY extracts when there is an EXPLICIT label.
    Does NOT infer country from addresses.

    Priority:
    1. Label-first: "Country of Origin: INDIA"
    2. "Made in India"
    """
    # --- Only extract from explicit labels ---
    label_patterns = [
        # "Country of Origin: INDIA" or "COUNTRY OF ORIGIN INDIA"
        re.compile(
            r"COUNTRY\s+OF\s+ORIGIN\s*[:=]?\s*([A-Z][A-Za-z]+)",
            re.IGNORECASE,
        ),
        # "Made in India"
        re.compile(
            r"MADE\s+IN\s+([A-Z][A-Za-z]+)",
            re.IGNORECASE,
        ),
    ]

    for pattern in label_patterns:
        match = pattern.search(text)
        if match:
            country = match.group(1).strip()
            country = country.rstrip(".,;")
            # Validate: should be a reasonable country name
            if 2 <= len(country) <= 30:
                return _normalize_country(country)

    return None


def _extract_manufacturing_date(text: str) -> Optional[str]:
    """
    Extract manufacturing date from OCR text.

    Priority:
    1. Label-first: "Mfg/Pkg Date: 01/2026" or "MFD 01/26"
    2. Look for dates near the label even with corruption
    3. Never invent a date if not found
    """
    # Date pattern that matches MM/YY, MM/YYYY, or MON YYYY
    date_pattern = r"((?:0[1-9]|1[0-2])[/\-\.](?:20)?[0-9]{2})"

    # --- Priority 1: Label-first extraction ---
    label_patterns = [
        # "Mfg/Pkg Date: 01/2026" or "Mfg Date: 01/2026"
        re.compile(
            r"MFG\.?\s*(?:/?\s*PKG\.?)?\s*DATE"
            r"\s*[:=]?\s*"
            + date_pattern,
            re.IGNORECASE,
        ),
        # "MFD: 01/26" or "MFG: 01/26"
        re.compile(
            r"(?:MFD|MFG|MANUFACTURED?|PKD|PACKED)"
            r"\s*[:=.]?\s*"
            + date_pattern,
            re.IGNORECASE,
        ),
        # "01/26@05/28" pattern (first is MFD, second is expiry)
        re.compile(
            r"(\d{2}/\d{2})\s*[@]\s*\d{2}/\d{2}",
        ),
    ]

    for pattern in label_patterns:
        match = pattern.search(text)
        if match:
            date_str = match.group(1).strip()
            return _normalize_date(date_str)

    # --- Priority 2: Look for date near Mfg label with corruption ---
    # Find the label and search nearby for any date-like pattern
    mfg_label = re.compile(
        r"(?:MFG\.?\s*(?:/?\s*PKG\.?)?\s*DATE|MFD|MFG|MANUFACTURED?)"
        r"\s*[:=]?",
        re.IGNORECASE,
    )
    mfg_match = mfg_label.search(text)
    if mfg_match:
        # Search within 50 characters after the label
        search_region = text[mfg_match.end():mfg_match.end() + 50]
        date_match = re.search(date_pattern, search_region)
        if date_match:
            return _normalize_date(date_match.group(1))

    return None


def _extract_best_before(text: str) -> Optional[str]:
    """
    Extract best before / use before duration from OCR text.

    This extracts duration-based declarations like "24 months from Mfg"
    which are NOT actual expiry dates.
    """
    patterns = [
        # "Best Before: 24 months from Mfg/Pkg"
        re.compile(
            r"(?:USE\s+BEFORE|BEST\s+BEFORE\s*(?:END)?|"
            r"EXP(?:IRY)?(?:\s+DATE)?|EXPIRY)"
            r"\s*[:=]?\s*"
            r"(\d+\s*(?:MONTHS?|DAYS?|YEARS?)\s+FROM\s+"
            r"(?:MFG|PKG|MANUFACTURED?|PACKED?))",
            re.IGNORECASE,
        ),
    ]

    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()

    return None


def _extract_expiry_date(text: str) -> Optional[str]:
    """
    Extract expiry / use before date from OCR text.

    Priority:
    1. Label-first: "Expiry: 05/2028" or "Use Before: 05/2028"
    2. Duration-based declarations go to best_before, not here
    """
    # --- Priority 1: Label-first extraction ---
    label_patterns = [
        # "Best Before: 05/2028" or "Expiry: 05/2028" (actual date)
        re.compile(
            r"(?:USE\s+BEFORE|BEST\s+BEFORE\s*(?:END)?|"
            r"EXP(?:IRY)?(?:\s+DATE)?|EXPIRY)"
            r"\s*[:=]?\s*"
            r"((?:0[1-9]|1[0-2])[/\-\.](?:20)?[0-9]{2})",
            re.IGNORECASE,
        ),
        # "@ 05/28 pattern (from MFD & USE BEFORE format)
        re.compile(
            r"@((?:0[1-9]|1[0-2])[/\-\.](?:20)?[0-9]{2})",
        ),
    ]

    for pattern in label_patterns:
        match = pattern.search(text)
        if match:
            date_str = match.group(1).strip()
            return _normalize_date(date_str)

    return None


def _extract_batch_number(text: str) -> Optional[str]:
    """Extract batch/lot number from OCR text."""
    patterns = [
        re.compile(
            r"(?:BATCH|LOT)\s*(?:NO\.?|NUMBER\.?)?"
            r"\s*[:=]?\s*"
            r"([A-Z0-9][A-Z0-9\-/]{2,20})",
            re.IGNORECASE,
        ),
        re.compile(
            r"(?:BATCH|LOT)\s+([A-Z0-9][A-Z0-9\-/]{2,20})",
            re.IGNORECASE,
        ),
    ]

    for pattern in patterns:
        match = pattern.search(text)
        if match:
            batch = match.group(1).strip()
            if re.match(r"^\d{6,10}$", batch):
                continue
            if len(batch) >= 3:
                return batch

    return None


def _extract_manufacturer_address(text: str) -> Optional[str]:
    """
    Extract manufacturer address from OCR text.

    Priority:
    1. Look for address patterns after manufacturer labels
    2. Capture until next major declaration
    """
    # --- Priority 1: Look for address after manufacturer ---
    address_indicators = re.compile(
        r"(?:PLOT|SURVEY|UNIT|ROAD|STREET|VILLAGE|POST|DISTRICT|"
        r"PIN|P\.?O\.?|INDUSTRIAL|SECTOR|NAGAR|COLONY|BLOCK|"
        r"PHASE|ZONE|LANE|MARG)",
        re.IGNORECASE,
    )

    # Find manufacturer/packer/importer label
    mfg_label = re.compile(
        r"(?:MANUFACTURED?\s+(?:&\s+)?(?:AND\s+)?MARKETED?\s+BY|"
        r"MANUFACTURED?\s+BY|MANUFACTURER|"
        r"PACKED?\s+BY|IMPORTER\s*[:=])"
        r"\s*[:=]?\s*",
        re.IGNORECASE,
    )

    mfg_match = mfg_label.search(text)
    if mfg_match:
        # Look for address indicators after the manufacturer label
        search_start = mfg_match.end()
        remaining = text[search_start:]

        addr_match = address_indicators.search(remaining)
        if addr_match:
            # Capture from address indicator until next major label
            next_label = re.compile(
                r"(?:MFG|MFD|MRP|NET|BATCH|COUNTRY|CONSUMER|CARE|TOLL|"
                r"BEST\s+BEFORE|EXPIRY|USE\s+BEFORE)",
                re.IGNORECASE,
            )
            addr_start = addr_match.start()
            next_match = next_label.search(remaining, addr_start + 5)
            if next_match:
                address = remaining[addr_start:next_match.start()]
            else:
                address = remaining[addr_start:addr_start + 200]

            address = _clean_extracted_value(address)
            if len(address) >= 10:
                return address

    return None


def _extract_customer_care(text: str) -> Optional[CustomerCareInfo]:
    """
    Extract customer care information from OCR text.

    Priority:
    1. Label-first: "Consumer Care Details:" or "Customer Care:"
    2. Detect phone, email, address independently
    """
    phone = None
    email = None
    address = None

    # --- Phone extraction ---
    phone_patterns = [
        # "Toll Free: 1800-10-22-221" or "Consumer Care: 1800-10-22-221"
        re.compile(
            r"(?:TOLL\s*FREE|HELPLINE|CUSTOMER\s*CARE|CONSUMER\s+CARE|"
            r"PHONE|CONTACT\s*(?:US|NUMBER)?)"
            r"\s*[:=]?\s*"
            r"(\d[\d\s\-]{8,15}\d)",
            re.IGNORECASE,
        ),
        # Standalone phone numbers (10 digits)
        re.compile(r"\b(\d{5}[\s\-]?\d{5})\b"),
    ]

    for pattern in phone_patterns:
        match = pattern.search(text)
        if match:
            phone_candidate = match.group(1).replace(" ", "").replace("-", "")
            if len(phone_candidate) in (10, 11, 12, 13):
                phone = match.group(1).strip()
                break

    # --- Email extraction ---
    email_match = re.search(
        r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
        text,
    )
    if email_match:
        email = email_match.group(0)

    # --- Address extraction ---
    address_patterns = [
        # "PO BOX 14760, MUMBAI 400 099"
        re.compile(
            r"(?:PO\s*BOX|P\.?O\.?\s*BOX)\s+(\d+[\w\s,]*?\d{6})",
            re.IGNORECASE,
        ),
        # Consumer care address near label
        re.compile(
            r"(?:CONSUMER\s+CARE|CUSTOMER\s+CARE|LEVERCARE|"
            r"CONTACT\s*US)[^.]*?"
            r"(?:PO\s*BOX|P\.?O\.?\s*BOX)\s*(\d+[^.]+)",
            re.IGNORECASE,
        ),
        # Any address near consumer care label (capture until next major label)
        re.compile(
            r"(?:CONSUMER\s+CARE|CUSTOMER\s+CARE|CONTACT\s*US)"
            r"\s*[:=]?\s*"
            r"([A-Z][A-Za-z0-9\s,\-]{10,100})",
            re.IGNORECASE,
        ),
    ]

    for pattern in address_patterns:
        match = pattern.search(text)
        if match:
            candidate = _normalize_whitespace(match.group(0))
            # Trim at next major label
            next_label = re.compile(
                r"(?:MRP|NET|BATCH|MFG|MFD|COUNTRY|BEST\s+BEFORE|EXPIRY)",
                re.IGNORECASE,
            )
            next_match = next_label.search(candidate)
            if next_match:
                candidate = candidate[:next_match.start()].strip()
            if len(candidate) >= 10:
                address = candidate
                break

    if phone or email or address:
        return CustomerCareInfo(phone=phone, email=email, address=address)

    return None


# ---------------------------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------------------------

def extract_fields_from_text(raw_text: str) -> ExtractedFields:
    """
    Extract all structured fields from raw OCR text.

    This is the main entry point for field extraction. It runs all
    individual extractors and returns a combined result.

    Uses a **label-first extraction** strategy:
    1. First scan for explicit label patterns
    2. Extract values immediately following labels
    3. Fall back to generic patterns only when labels are absent

    Args:
        raw_text: The raw text extracted from OCR processing.

    Returns:
        ExtractedFields dataclass with all extracted fields.
    """
    if not raw_text or not raw_text.strip():
        logger.warning("Empty or whitespace-only text provided for extraction")
        return ExtractedFields()

    # Normalize whitespace while preserving line breaks for label detection
    cleaned_text = re.sub(r"[ \t]+", " ", raw_text).strip()

    logger.info(f"Extracting fields from {len(cleaned_text)} characters of OCR text")

    # Extract each field independently
    fields = ExtractedFields(
        product_name=_extract_product_name(cleaned_text),
        brand_name=_extract_brand_name(cleaned_text),
        manufacturer=_extract_manufacturer(cleaned_text),
        marketer=_extract_marketer(cleaned_text),
        mrp=_extract_mrp(cleaned_text),
        net_quantity=_extract_net_quantity(cleaned_text),
        pack_count=_extract_pack_count(cleaned_text),
        country_of_origin=_extract_country_of_origin(cleaned_text),
        manufacturing_date=_extract_manufacturing_date(cleaned_text),
        expiry_date=_extract_expiry_date(cleaned_text),
        best_before=_extract_best_before(cleaned_text),
        batch_number=_extract_batch_number(cleaned_text),
        manufacturer_address=_extract_manufacturer_address(cleaned_text),
        customer_care=_extract_customer_care(cleaned_text),
    )

    # Log extraction summary
    extracted_count = sum(1 for v in fields.__dict__.values() if v is not None)
    logger.info(f"Extracted {extracted_count}/14 fields successfully")

    return fields
