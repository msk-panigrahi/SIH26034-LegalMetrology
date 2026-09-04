# LegalMetriX Backend

Packaged Commodity Legal Metrology Compliance & Inspection Support System

## Architecture

```
backend/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── database.py                # SQLAlchemy engine & session
│   ├── models/
│   │   ├── __init__.py            # Model registry
│   │   ├── user.py                # Inspector/admin users
│   │   ├── product.py             # Packaged commodities
│   │   ├── inspection.py          # Inspection events
│   │   ├── ocr_result.py          # OCR text & extracted fields
│   │   ├── compliance_result.py   # Full compliance evaluation
│   │   ├── declaration.py         # OCR-extracted declarations
│   │   └── compliance_finding.py  # Individual compliance findings
│   ├── routers/
│   │   ├── inspection_upload.py   # Image upload endpoint
│   │   ├── ocr.py                 # OCR text extraction
│   │   ├── extraction.py          # Field extraction endpoint
│   │   └── compliance.py          # Compliance validation endpoint
│   └── services/
│       ├── ocr_service.py         # Tesseract OCR wrapper
│       ├── field_extraction_service.py  # Field extraction logic
│       └── compliance/            # Compliance engine package
│           ├── __init__.py
│           ├── engine.py          # Main compliance engine
│           ├── models.py          # Rule status, severity, result models
│           ├── context.py         # Compliance context dataclass
│           ├── base_rule.py       # Abstract base rule class
│           ├── rule_registry.py   # Central rule registry
│           └── rules/
│               ├── __init__.py
│               ├── declaration_rules.py  # LM-001 to LM-004
│               ├── quantity_rules.py     # LM-005
│               ├── mrp_rules.py          # LM-006 to LM-007
│               ├── date_rules.py         # LM-008 to LM-009
│               ├── unit_price_rules.py   # Additional unit price helpers
│               └── package_rules.py      # LM-010 to LM-013
├── alembic/                       # Database migrations
├── uploads/                       # Uploaded inspection images
└── requirements.txt
```

## Data Flow

```
Product Image
     ↓
Image Upload          POST /api/inspections/upload
     ↓
Inspection Record
     ↓
Tesseract OCR        POST /api/inspections/{id}/ocr
     ↓
Raw OCR Text
     ↓
Field Extraction     POST /api/inspections/{id}/extract-fields
     ↓
Structured Product Data
     ↓
Compliance Validation POST /api/inspections/{id}/compliance
     ↓
Rule-by-Rule Results
     ↓
Overall Assessment
```

## API Endpoints

### 1. Health Check
```
GET /health
```

### 2. Upload Inspection Image
```
POST /api/inspections/upload
Content-Type: multipart/form-data

Parameters:
- file: Package/product image (jpg, jpeg, png, webp)
- product_name: Optional product name
- product_category: Optional category (food, cosmetic, etc.)
- notes: Optional inspection notes
```

### 3. Run OCR
```
POST /api/inspections/{inspection_id}/ocr
```

### 4. Extract Fields
```
POST /api/inspections/{inspection_id}/extract-fields
```

### 5. Compliance Validation (NEW)

#### POST — Run Compliance Evaluation
```
POST /api/inspections/{inspection_id}/compliance
```

No request body required. The endpoint:
1. Validates the inspection exists
2. Retrieves OCR text and extracted fields
3. Runs all compliance rules (LM-001 to LM-013)
4. Calculates overall compliance status
5. Persists the result
6. Returns structured rule-by-rule results

**Prerequisites**: OCR and field extraction must be completed first.

#### GET — Retrieve Stored Result
```
GET /api/inspections/{inspection_id}/compliance
```

Returns the most recent stored compliance result.

## Compliance Engine

### Overview

The compliance engine is a deterministic, explainable, evidence-based
validation system for the Legal Metrology (Packaged Commodities) Rules, 2011.

**Important disclaimer**: The compliance engine provides an automated
preliminary assessment based on available image/OCR evidence and should
not be interpreted as a substitute for inspection by an authorized
Legal Metrology officer.

### Rule IDs

| Rule ID | Name | Legal Basis |
|---------|------|-------------|
| LM-001 | Common / Generic Name | Rule 6(1)(b) |
| LM-002 | Manufacturer / Packer / Importer Declaration | Rule 6(1)(a) |
| LM-003 | Address Declaration | Rule 6(1)(a) |
| LM-004 | Country of Origin | Rule 6(1)(a) |
| LM-005 | Net Quantity Declaration | Rule 6(1)(d) |
| LM-006 | MRP Declaration | Rule 6(1)(f) |
| LM-007 | Unit Sale Price | Rule 6(1)(f) |
| LM-008 | Manufacturing / Packing Date | Rule 6(1)(e) |
| LM-009 | Best Before / Use By / Expiry | Rule 6(1)(e) |
| LM-010 | Consumer Care Details | Rule 6(1)(g) |
| LM-011 | Dimensions | Rule 6 (where applicable) |
| LM-012 | Legibility / Prominence | Rule 9 |
| LM-013 | Multi-Piece / Group Package | Rule 3 |

### Rule Status Definitions

| Status | Meaning |
|--------|---------|
| `PASS` | Requirement detected and passes automated check |
| `FAIL` | Requirement missing, malformed, or fails automated check |
| `WARNING` | Potential issue detected, but insufficient for definitive failure |
| `NOT_VERIFIABLE` | Insufficient image/OCR/context to make determination |
| `NOT_APPLICABLE` | Rule does not apply to the inspected product/context |

### Severity Levels

| Level | Usage |
|-------|-------|
| `LOW` | Minor or optional requirements |
| `MEDIUM` | Standard requirements |
| `HIGH` | Core legal metrology requirements |
| `CRITICAL` | Fundamental compliance failures |

### Overall Status Logic

```
Any FAIL → NON_COMPLIANT
No FAIL but WARNING(s) → REVIEW_REQUIRED
No FAIL but NOT_VERIFIABLE(s) → REVIEW_REQUIRED
All applicable rules PASS → COMPLIANT
All rules NOT_APPLICABLE → INCOMPLETE
```

### Example Response

```json
{
  "inspection_id": 3,
  "overall_status": "REVIEW_REQUIRED",
  "rule_version": "LM-PCR-2026",
  "summary": {
    "passed": 8,
    "failed": 0,
    "warnings": 2,
    "not_verifiable": 2,
    "not_applicable": 1,
    "rules_checked": 13
  },
  "rules": [
    {
      "rule_id": "LM-001",
      "rule_name": "Common / Generic Name",
      "legal_basis": "Rule 6(1)(b)",
      "status": "PASS",
      "severity": "HIGH",
      "field": "product_name",
      "message": "The package declares a common/generic commodity name.",
      "evidence": "Dove Bathing Bar",
      "confidence": "HIGH"
    }
  ],
  "message": "Compliance assessment completed."
}
```

### Rule Details

#### LM-001 — Common / Generic Name
- **Purpose**: Check that the package contains the common or generic name
- **Input**: `product_name`, raw OCR text
- **Checks**: Looks for known commodity type words (Bathing Bar, Soap, Biscuits, etc.)
- **Limitation**: Cannot verify legal sufficiency of the generic name

#### LM-002 — Manufacturer / Packer / Importer Declaration
- **Purpose**: Verify responsible entity declaration exists
- **Input**: `manufacturer`, `marketer`, raw OCR text
- **Checks**: Looks for MFG BY, MANUFACTURED BY, MARKETED BY, etc.
- **Limitation**: Cannot verify entity registration or legal status

#### LM-003 — Address Declaration
- **Purpose**: Verify manufacturer/packer address is present
- **Input**: `manufacturer_address`, raw OCR text
- **Checks**: Looks for address indicators (Survey No, Road, PIN code, etc.)
- **Limitation**: Cannot verify address accuracy or completeness

#### LM-004 — Country of Origin
- **Purpose**: Verify country of origin declaration
- **Input**: `country_of_origin`, raw OCR text
- **Checks**: Looks for MADE IN, COUNTRY OF ORIGIN labels
- **Limitation**: Applicability depends on whether product is imported

#### LM-005 — Net Quantity Declaration
- **Purpose**: Validate net quantity declaration
- **Input**: `net_quantity`, `pack_count`, raw OCR text
- **Checks**: Value positive, unit recognized, multi-pack handling
- **Limitation**: Cannot verify actual quantity measurement

#### LM-006 — MRP Declaration
- **Purpose**: Verify Maximum Retail Price declaration
- **Input**: `mrp.value`, `mrp.currency`, `mrp.source`
- **Checks**: Value positive, reasonable range, currency valid
- **Limitation**: Cannot verify price accuracy with actual product

#### LM-007 — Unit Sale Price
- **Purpose**: Validate unit sale price declaration
- **Input**: `mrp`, `net_quantity`, raw OCR text
- **Checks**: Calculates expected unit price, compares with declared USP
- **Limitation**: Only applicable for certain commodity types

#### LM-008 — Manufacturing / Packing Date
- **Purpose**: Verify manufacturing date declaration
- **Input**: `manufacturing_date`, raw OCR text
- **Checks**: Date format valid, label present
- **Limitation**: Cannot verify date accuracy

#### LM-009 — Best Before / Use By / Expiry
- **Purpose**: Verify expiry date declaration
- **Input**: `expiry_date`, `manufacturing_date`, raw OCR text
- **Checks**: Date present, expiry after manufacturing (consistency)
- **Limitation**: Applicability depends on commodity type

#### LM-010 — Consumer Care Details
- **Purpose**: Verify consumer care contact information
- **Input**: `customer_care.phone`, `customer_care.email`, `customer_care.address`
- **Checks**: At least one valid contact channel present
- **Limitation**: Cannot verify contact information accuracy

#### LM-011 — Dimensions
- **Purpose**: Verify dimension declaration (where applicable)
- **Input**: raw OCR text
- **Checks**: Looks for dimension patterns (cm, mm, etc.)
- **Limitation**: Not applicable for all commodity types

#### LM-012 — Legibility / Prominence
- **Purpose**: Verify declarations are legible and prominent
- **Input**: OCR confidence score
- **Checks**: Currently returns NOT_VERIFIABLE (requires visual analysis)
- **Limitation**: OCR alone cannot establish legal legibility

#### LM-013 — Multi-Piece / Group Package
- **Purpose**: Detect and assess multi-piece packages
- **Input**: `pack_count`, raw OCR text
- **Checks**: Identifies multi-pack indicators
- **Limitation**: Cannot verify individual package compliance

## Testing

### Via Swagger UI
1. Start server: `uvicorn app.main:app --reload`
2. Open: http://localhost:8000/docs
3. Upload image → Run OCR → Extract fields → Run compliance

### Via curl
```bash
# Upload
curl -F "file=@package.jpg" http://localhost:8000/api/inspections/upload

# OCR
curl -X POST http://localhost:8000/api/inspections/{id}/ocr

# Extract fields
curl -X POST http://localhost:8000/api/inspections/{id}/extract-fields

# Run compliance
curl -X POST http://localhost:8000/api/inspections/{id}/compliance

# Get stored result
curl http://localhost:8000/api/inspections/{id}/compliance
```

## Database Migration

```bash
cd backend
alembic upgrade head
```

Tables:
- `ocr_results`: Stores OCR text and extracted fields
- `compliance_results`: Stores full compliance evaluations

## Dependencies

No new external dependencies were added. The compliance engine uses only
Python standard library (`re`, `dataclasses`, `enum`, `datetime`).

## Rule Versioning

The engine uses rule version `LM-PCR-2026` to track which rule set
was applied. This allows the engine to evolve as regulations change
while preserving historical evaluation results.
