"""
Inspection upload router — handles image upload and inspection record creation.
Requires authentication — the current user becomes the inspector.
"""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, Inspection, User
from app.auth.dependencies import require_inspector

router = APIRouter(prefix="/api/inspections", tags=["inspections"])

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "inspections"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Category presets for the dropdown
VALID_CATEGORIES = [
    "food",
    "beverage",
    "cosmetic",
    "pharmaceutical",
    "electronics",
    "textile",
    "household",
    "other",
]


def _ensure_upload_dir() -> None:
    """Create the upload directory if it does not exist."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _validate_image(file: UploadFile) -> None:
    """Raise HTTPException if the file is not a supported image or is too large."""
    if file.filename is None or file.filename == "":
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image format '{ext}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/upload", summary="Upload a package image and create an inspection")
async def upload_inspection_image(
    file: UploadFile = File(..., description="Package/product image"),
    product_name: str = Form(default="", description="Optional product name"),
    product_category: str = Form(default="other", description="Optional product category"),
    notes: str = Form(default="", description="Optional inspection notes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_inspector),
):
    """
    Accept a package image via multipart/form-data.

    Requires authentication. The current user becomes the inspector.

    1. Validate the image format.
    2. Save the file to ``backend/uploads/inspections/``.
    3. Create Product + Inspection records.
    4. Return the inspection details as JSON.
    """

    # --- Validate --------------------------------------------------------
    _validate_image(file)

    # --- Read & check size -----------------------------------------------
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)} MB.",
        )
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # --- Generate unique filename -----------------------------------------
    ext = Path(file.filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"

    _ensure_upload_dir()
    save_path = UPLOAD_DIR / unique_name

    try:
        with open(save_path, "wb") as f:
            f.write(contents)
    except OSError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save file: {e}"
        )

    # --- Database records ------------------------------------------------
    # Create a product record
    resolved_name = product_name.strip() if product_name.strip() else "Untitled Product"
    resolved_category = product_category.strip().lower() if product_category.strip() else "other"
    if resolved_category not in VALID_CATEGORIES:
        resolved_category = "other"

    product = Product(
        product_name=resolved_name,
        brand_name="Unknown",
        category=resolved_category,
    )
    db.add(product)
    db.flush()  # get product.id without committing yet

    # Create an inspection record — owner is the authenticated user
    relative_path = f"inspections/{unique_name}"
    inspection = Inspection(
        product_id=product.id,
        inspector_id=current_user.id,
        image_path=relative_path,
        status="UPLOADED",
        notes=notes.strip() if notes.strip() else None,
    )
    db.add(inspection)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(inspection)
    db.refresh(product)

    # --- Response --------------------------------------------------------
    return {
        "inspection_id": inspection.id,
        "filename": unique_name,
        "status": inspection.status,
        "product": {
            "id": product.id,
            "product_name": product.product_name,
            "category": product.category,
        },
        "notes": inspection.notes,
        "inspector_id": current_user.id,
        "message": "Image uploaded and inspection record created successfully.",
    }
