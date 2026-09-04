# ⚖️ LegalMetriX

### Intelligent Packaged Commodity Inspection & Legal Metrology Compliance Platform

**LegalMetriX** is a digital inspection and compliance-assistance platform designed to support **Legal Metrology Officers** in the inspection of packaged commodities.

The platform transforms traditionally manual inspection activities into a structured digital workflow by combining **OCR-based label analysis, automated field extraction, rule-based legal-metrology validation, inspection management, compliance classification, dashboards, and digital report generation**.

> **Inspect smarter. Verify faster. Document digitally.**

---

## 📌 Problem Statement

Inspection of packaged commodities requires Legal Metrology Officers to verify declarations printed on product packages, including:

* Maximum Retail Price (MRP)
* Net Quantity
* Manufacturer / Packer / Importer details
* Batch / Lot information
* Manufacturing / Packing date
* Consumer-care information
* Mandatory declarations
* Other applicable Legal Metrology requirements

In conventional inspection workflows, officers may need to manually locate and verify these declarations from physical packaging, record observations, determine compliance, and prepare inspection documentation.

This can become challenging when:

* Product labels contain large amounts of text
* Information is distributed across different parts of the package
* Multiple declarations need to be verified
* Inspection records need to be maintained systematically
* Reports need to be generated consistently
* Previous inspection data needs to be reviewed

**LegalMetriX addresses this workflow by providing a centralized digital inspection and compliance-assistance system.**

---

# 🎯 Our Solution

LegalMetriX provides a complete inspection workflow:

```text
                    ┌──────────────────────┐
                    │     Product Image    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    OCR Processing    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Field Extraction     │
                    │                      │
                    │ • MRP                │
                    │ • Net Quantity       │
                    │ • Batch/Lot          │
                    │ • Manufacturer       │
                    │ • Dates              │
                    │ • Consumer Care      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Compliance Engine    │
                    │                      │
                    │ Legal Metrology      │
                    │ Validation Rules     │
                    └──────────┬───────────┘
                               │
                               ▼
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        COMPLIANT        NON_COMPLIANT    REVIEW_REQUIRED
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Inspection Record    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Digital PDF Report   │
                    └──────────────────────┘
```

The goal is **not to replace the Legal Metrology Officer's judgement**.

Instead, LegalMetriX acts as a **decision-support and inspection-assistance system**, helping officers process information faster while keeping the final inspection decision under human supervision.

---

# ✨ Key Features

## 🔍 1. OCR-Based Product Label Analysis

LegalMetriX accepts product/package images and performs OCR processing to extract textual information from the label.

The OCR pipeline includes:

* Image preprocessing
* EXIF-based automatic image rotation
* Adaptive image resizing
* Multiple OCR segmentation strategies
* Multiple preprocessing variants
* OCR result quality evaluation
* OCR confidence reporting
* Diagnostic information about the selected OCR strategy

This allows the system to handle different product-label layouts and image conditions more effectively.

---

## 🧾 2. Automated Field Extraction

After OCR processing, LegalMetriX identifies important declarations from the extracted text.

The extraction layer focuses on fields such as:

* Product Name
* MRP
* Net Quantity
* Batch / Lot Number
* Manufacturer / Packer / Importer
* Manufacturing / Packing Date
* Expiry / Best Before information
* Consumer Care details
* Other relevant declarations

The extraction service includes contextual matching and false-positive filtering to reduce incorrect field assignments.

---

## ⚖️ 3. Legal Metrology Compliance Engine

Extracted information is evaluated using structured Legal Metrology validation rules.

The system can classify inspection results into:

### 🟢 COMPLIANT

The applicable declarations satisfy the configured requirements.

### 🔴 NON_COMPLIANT

One or more applicable requirements are violated.

### 🟡 REVIEW_REQUIRED

The available information is insufficient or uncertain and requires officer verification.

### ⚪ NOT_APPLICABLE / NOT_VERIFIABLE

Rules that do not apply to the specific product or cannot reasonably be verified from the available information are handled separately rather than being incorrectly marked as non-compliant.

This approach helps prevent ambiguous information from automatically becoming a false compliance violation.

---

# 📋 Compliance Rule Framework

LegalMetriX follows a modular rule-based architecture.

Each compliance rule can evaluate a specific declaration or requirement.

Example:

```text
LM-001 → Product / Declaration Validation
LM-006 → MRP Declaration
LM-011 → Applicable Declaration Validation
LM-012 → Applicable Declaration Validation
LM-013 → Applicable Declaration Validation
```

The modular structure makes it possible to extend the platform with additional Legal Metrology rules without redesigning the entire application.

---

# 👮 Inspector Dashboard

The Inspector Dashboard is designed around the actual inspection workflow.

It provides:

* Inspection statistics
* Recent inspections
* Product information
* Compliance status
* OCR confidence information
* Inspection history
* Inspection-level details
* Access to generated reports

The dashboard allows an officer to move from **image analysis → verification → compliance result → documentation** through a single workflow.

---

# 🛡️ Admin Dashboard

The Admin Dashboard provides a system-wide operational overview.

Administrators can view:

* Total inspections
* Compliance statistics
* Inspector activity
* Active inspectors
* OCR confidence information
* Recent inspection activity
* System-level statistics

This provides a high-level view of inspection operations and system usage.

---

# 📊 Public Landing Page

LegalMetriX includes a public-facing landing page containing:

* Product overview
* Problem statement
* Key capabilities
* Live system statistics
* Legal notice
* Platform information
* Footer and application information

The landing page provides a professional entry point to the platform without exposing protected inspection functionality.

---

# 📄 Digital Inspection Reports

LegalMetriX supports digital inspection report generation.

Reports can be accessed through:

```text
GET /api/inspections/{inspection_id}/report/pdf
```

The report workflow allows inspection information and compliance findings to be documented digitally instead of relying exclusively on manually prepared records.

The PDF report endpoint is designed as a **public read-only report access endpoint** according to the application's inspection-report workflow.

---

# 🔐 Role-Based Access

The application supports role-aware access control.

### Inspector

Inspectors can:

* Perform inspections
* Upload product images
* Analyze product declarations
* Review extracted information
* View compliance results
* Access inspection records
* Generate/view reports

### Administrator

Administrators can:

* Monitor system-wide activity
* View inspection statistics
* Monitor inspector activity
* Review system information
* Access administrative dashboards

Protected application functionality is separated from the public landing experience.

---

# 🧠 Intelligent OCR Pipeline

LegalMetriX uses a multi-strategy OCR approach rather than relying on a single OCR configuration.

```text
                 Product Image
                      │
                      ▼
               EXIF Rotation
                      │
                      ▼
               Image Resizing
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
   Preprocessing A          Preprocessing B
          │                       │
     ┌────┼────┐             ┌────┼────┐
     ▼    ▼    ▼             ▼    ▼    ▼
   PSM 1 PSM 2 ...          PSM 1 PSM 2 ...
     │    │    │             │    │    │
     └────┴────┴─────────────┴────┴────┘
                      │
                      ▼
             OCR Candidate Results
                      │
                      ▼
              Quality Evaluation
                      │
                      ▼
             Best Result Selection
                      │
                      ▼
             Field Extraction
```

The OCR service also exposes diagnostic information such as the selected PSM strategy to help during inspection and debugging.

---

# 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND                            │
│                                                         │
│       React + Vite + CSS                                │
│                                                         │
│  Landing │ Inspector Dashboard │ Admin Dashboard       │
│                                                         │
└─────────────────────────┬───────────────────────────────┘
                          │
                          │ REST APIs
                          ▼
┌─────────────────────────────────────────────────────────┐
│                     BACKEND                             │
│                                                         │
│                      FastAPI                            │
│                                                         │
│  Authentication │ Inspections │ OCR │ Dashboard        │
│                                                         │
│              Field Extraction                           │
│                     │                                   │
│              Compliance Engine                          │
│                     │                                   │
│               Report Generation                         │
│                                                         │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    DATABASE                             │
│                                                         │
│                    PostgreSQL                           │
│                                                         │
│ Users │ Inspections │ Extracted Fields │ Results        │
│                                                         │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                  Product Images
                   + PDF Reports
```

---

# 🛠️ Technology Stack

## Frontend

* React
* Vite
* JavaScript
* HTML5
* CSS3

## Backend

* Python
* FastAPI
* REST APIs
* Pydantic
* SQLAlchemy

## Database

* PostgreSQL
* Alembic migrations

## OCR & Image Processing

* Tesseract OCR
* Image preprocessing
* OCR multi-strategy processing
* EXIF image orientation handling

## Reporting

* PDF report generation

## Development Tools

* Git
* GitHub
* VS Code
* Swagger / OpenAPI

---

# 📁 Project Structure

```text
SIH26034-LegalMetrology/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── routers/
│   │   │   ├── inspections.py
│   │   │   ├── dashboard.py
│   │   │   └── ocr.py
│   │   │
│   │   ├── services/
│   │   │   ├── ocr_service.py
│   │   │   └── field_extraction_service.py
│   │   │
│   │   ├── compliance/
│   │   │   └── models.py
│   │   │
│   │   └── reports.py
│   │
│   ├── alembic/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── LandingPage.jsx
│   │   │   ├── InspectorDashboard.jsx
│   │   │   └── AdminDashboard.jsx
│   │   │    
│   │   └── ...
│   │
│   ├── package.json
│   └── vite.config.js
│
├── README.md
└── .gitignore
```

> The exact directory structure may vary slightly depending on the current project version.

---

# 🚀 Getting Started

## Prerequisites

Make sure the following are installed:

* Git
* Python 3.10+
* Node.js 18+
* PostgreSQL
* Tesseract OCR
* npm

Verify installations:

```bash
git --version
python --version
node --version
npm --version
psql --version
tesseract --version
```

---

# 📥 Clone the Repository

Clone the repository:

```bash
git clone https://github.com/msk-panigrahi/SIH26034-LegalMetrology.git
```

Move into the project:

```bash
cd SIH26034-LegalMetrology
```

---

# ⚙️ Backend Setup

Navigate to the backend:

```bash
cd backend
```

Create a virtual environment:

### Windows

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 🔑 Environment Configuration

Create a `.env` file inside the backend directory.

Example:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/legalmetrix
SECRET_KEY=your-secret-key
```

Add any additional environment variables required by the project.

> **Never commit `.env` to GitHub.**

Use `.env.example` to document the required variables without exposing secrets.

---

# 🗄️ Database Setup

Create the PostgreSQL database:

```sql
CREATE DATABASE legalmetrix;
```

Run migrations:

```bash
python -m alembic upgrade head
```

Verify that the required tables have been created successfully.

---

# ▶️ Start the Backend

From the backend directory:

```bash
uvicorn app.main:app --reload
```

The API will normally be available at:

```text
http://127.0.0.1:8000
```

---

# 📚 API Documentation

FastAPI automatically provides interactive API documentation.

Open:

```text
http://127.0.0.1:8000/docs
```

Alternative OpenAPI documentation:

```text
http://127.0.0.1:8000/redoc
```

Swagger UI can be used to inspect and test available APIs.

---

# 💻 Frontend Setup

Open another terminal.

Navigate to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

---

# 🧪 Verification

Before using the application, verify:

### Backend

```bash
python -m py_compile <modified-python-files>
```

### Frontend

```bash
npm run build
```

The production build should complete successfully.

You can also run:

```bash
npm run lint
```

to identify code-quality issues.

---

# 🔄 End-to-End Inspection Workflow

A typical LegalMetriX inspection follows:

```text
1. Officer logs into the system
              ↓
2. Creates an inspection
              ↓
3. Uploads product/package image
              ↓
4. OCR analyzes the label
              ↓
5. Relevant declarations are extracted
              ↓
6. Officer reviews extracted information
              ↓
7. Compliance rules evaluate declarations
              ↓
8. System determines inspection status
              ↓
9. Officer reviews findings
              ↓
10. Inspection is saved
              ↓
11. Digital report is generated
```

---

# 📈 Inspection Status

LegalMetriX supports structured inspection statuses such as:

```text
COMPLIANT
NON_COMPLIANT
REVIEW_REQUIRED
INCOMPLETE
```

This distinction allows the platform to represent the actual state of an inspection rather than reducing every uncertain case to a binary result.

---

# 🔎 Inspection Filtering

Inspection records can be filtered according to compliance status.

Supported categories include:

* COMPLIANT
* NON_COMPLIANT
* REVIEW_REQUIRED
* INCOMPLETE

This makes it easier for officers and administrators to locate inspections requiring attention.

---

# 📊 Public Statistics API

The platform provides a public statistics endpoint:

```text
GET /api/public/stats
```

It provides aggregate information such as:

* Inspection count
* Compliance statistics
* Inspector count

The endpoint includes graceful error handling so that the public landing page can continue functioning even if an underlying statistic is temporarily unavailable.

---

# 🔒 Security Considerations

LegalMetriX follows several security practices:

* Environment variables for sensitive configuration
* Role-based access control
* Protected application routes
* Read-only public report access
* Database-backed authentication
* No credentials committed to source control

### Never commit:

```text
.env
API keys
Database passwords
Secret keys
Private credentials
```

Use:

```text
.env.example
```

for sharing configuration requirements.

---

# 🌐 Why LegalMetriX Matters

LegalMetriX is designed around a real operational challenge:

> **How can Legal Metrology Officers reduce repetitive manual effort while improving the consistency, traceability, and speed of packaged-commodity inspections?**

The platform brings together:

```text
Digital Inspection
        +
OCR
        +
Field Extraction
        +
Legal Rule Validation
        +
Human Verification
        +
Digital Reporting
```

This creates a unified workflow instead of forcing officers to work across disconnected manual processes.

---

# 👨‍⚖️ Human-in-the-Loop Design

LegalMetriX is designed as an **officer-assistance system**, not an autonomous enforcement system.

The platform assists by:

* Reading product declarations
* Organizing extracted information
* Applying configured validation rules
* Highlighting potential violations
* Providing compliance classifications
* Generating inspection documentation

The **Legal Metrology Officer remains responsible for final verification and enforcement decisions**.

This human-in-the-loop approach is especially important when OCR results are uncertain, product packaging is unclear, or a declaration requires contextual interpretation.

---

# 🚧 Current Limitations

As with any OCR-based system, accuracy can be affected by:

* Image resolution
* Lighting conditions
* Blur
* Font styles
* Curved packaging
* Reflections
* Occluded text
* Complex label layouts
* Low-quality camera images

Therefore, OCR results should be treated as **inspection assistance**, with officer verification for uncertain cases.

---

# 🔮 Future Roadmap

Potential future enhancements include:

### 📷 Advanced Image Processing

* Automatic label-region detection
* Perspective correction
* Blur detection
* Better low-light processing
* Region-specific OCR

### 🧠 Smarter Field Extraction

* Spatial OCR analysis
* Improved declaration association
* Field-level confidence scores
* Cross-validation between OCR strategies

### ⚖️ Compliance Expansion

* Additional Legal Metrology rules
* Product-category-specific rules
* Configurable regulatory rule sets
* Rule versioning

### 📱 Field Inspection Support

* Mobile-friendly inspection interface
* Camera-first inspection workflow
* Offline inspection support
* Synchronization when connectivity is restored

### 📊 Analytics

* Inspection trends
* Frequently observed violations
* Product-category analytics
* Inspector workload analytics
* Regional inspection analytics

### 📄 Reporting

* Customizable report templates
* Inspection evidence attachments
* Digital signatures
* Exportable inspection datasets

---

# 🤝 Team Collaboration

LegalMetriX is designed to be developed collaboratively.

Recommended workflow:

```text
main
 │
 ├── feature/ocr-improvements
 ├── feature/compliance-rules
 ├── feature/dashboard
 ├── feature/reports
 └── feature/ui-improvements
```

Before merging:

1. Pull the latest `main`
2. Create a feature branch
3. Implement the feature
4. Test backend
5. Test frontend
6. Commit changes
7. Push the branch
8. Open a Pull Request
9. Review
10. Merge into `main`

---

# 🧑‍💻 Contributing

Contributions are welcome.

### 1. Fork the repository

```bash
git clone https://github.com/msk-panigrahi/SIH26034-LegalMetrology.git
```

### 2. Create a branch

```bash
git checkout -b feature/your-feature
```

### 3. Make your changes

### 4. Test the application

```bash
npm run build
```

and verify the backend APIs.

### 5. Commit

```bash
git add .
git commit -m "feat: add your feature"
```

### 6. Push

```bash
git push origin feature/your-feature
```

### 7. Create a Pull Request

Describe:

* What was changed
* Why it was needed
* How it was tested
* Any limitations

---

# 📜 License

This project is currently developed as an academic / hackathon prototype.

License information can be updated based on the team's final distribution requirements.

---

# 👥 Team

**LegalMetriX — Smart Digital Assistance for Legal Metrology Inspections**

Built with the goal of helping inspection teams move from:

```text
Manual Inspection
      ↓
Manual Recording
      ↓
Manual Verification
      ↓
Manual Reporting
```

towards:

```text
Digital Inspection
      ↓
OCR-Assisted Analysis
      ↓
Structured Extraction
      ↓
Rule-Based Validation
      ↓
Officer Verification
      ↓
Digital Reporting
```

---

# ⭐ Project Vision

LegalMetriX aims to demonstrate how modern software can assist regulatory officers in transforming a traditionally manual inspection process into a **faster, structured, traceable, and digitally documented workflow**.

The long-term vision is a platform where a Legal Metrology Officer can capture a product label, receive structured information about its declarations, identify potential compliance issues, review the evidence, and generate a standardized digital inspection record — all from a single platform.

> **LegalMetriX — Bringing intelligence, structure, and accountability to packaged-commodity inspections.**

---

### Built for innovation in Digital Governance, Regulatory Technology & Legal Metrology
