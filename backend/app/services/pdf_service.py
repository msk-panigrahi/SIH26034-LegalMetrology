"""
PDF Report Generation Service — generates professional LegalMetriX inspection reports.

Uses ReportLab to create PDF reports containing:
- Header with branding
- Product information
- Extracted declarations
- Compliance assessment
- Rule-by-rule findings
- Disclaimer
"""

import logging
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, Image as RLImage,
)
from reportlab.platypus.flowables import Flowable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / "storage" / "reports"


def _ensure_storage_dir() -> None:
    """Create the reports storage directory if it does not exist."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

def _get_styles():
    """Create custom styles for the report."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='ReportTitle',
        parent=styles['Title'],
        fontSize=22,
        leading=28,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=4,
        fontName='Helvetica-Bold',
    ))

    styles.add(ParagraphStyle(
        name='ReportSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=20,
        fontName='Helvetica',
    ))

    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading2'],
        fontSize=13,
        leading=18,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=16,
        spaceAfter=10,
        fontName='Helvetica-Bold',
        borderPadding=(0, 0, 4, 0),
    ))

    styles.add(ParagraphStyle(
        name='FieldLabel',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748b'),
        fontName='Helvetica-Bold',
    ))

    styles.add(ParagraphStyle(
        name='FieldValue',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica',
    ))

    styles.add(ParagraphStyle(
        name='SmallText',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#64748b'),
        fontName='Helvetica',
    ))

    styles.add(ParagraphStyle(
        name='DisclaimerText',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#92400e'),
        fontName='Helvetica-Oblique',
    ))

    styles.add(ParagraphStyle(
        name='MetaRight',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#334155'),
        alignment=TA_RIGHT,
        fontName='Helvetica',
    ))

    styles.add(ParagraphStyle(
        name='MetaLabel',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748b'),
        alignment=TA_RIGHT,
        fontName='Helvetica',
    ))

    styles.add(ParagraphStyle(
        name='TableCell',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155'),
        fontName='Helvetica',
    ))

    styles.add(ParagraphStyle(
        name='TableHeader',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#ffffff'),
        fontName='Helvetica-Bold',
    ))

    return styles


# ---------------------------------------------------------------------------
# Status color mapping
# ---------------------------------------------------------------------------

STATUS_COLORS = {
    'COMPLIANT': colors.HexColor('#16a34a'),
    'PASS': colors.HexColor('#16a34a'),
    'NON_COMPLIANT': colors.HexColor('#dc2626'),
    'FAIL': colors.HexColor('#dc2626'),
    'REVIEW_REQUIRED': colors.HexColor('#d97706'),
    'WARNING': colors.HexColor('#d97706'),
    'NOT_VERIFIABLE': colors.HexColor('#2563eb'),
    'NOT_APPLICABLE': colors.HexColor('#64748b'),
    'INCOMPLETE': colors.HexColor('#64748b'),
}


def _status_color(status: str) -> colors.Color:
    return STATUS_COLORS.get(status, colors.HexColor('#64748b'))


# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------

def generate_pdf_report(
    report_number: str,
    inspection_data: dict,
    extracted_fields: dict,
    compliance_data: dict,
    image_path: Optional[str] = None,
) -> str:
    """
    Generate a PDF inspection report.

    Args:
        report_number: Unique report identifier (e.g., LM-2026-000001).
        inspection_data: Dict with inspection metadata.
        extracted_fields: Dict of extracted product fields.
        compliance_data: Dict with compliance results.
        image_path: Optional path to the uploaded package image.

    Returns:
        Path to the generated PDF file.
    """
    _ensure_storage_dir()
    pdf_path = STORAGE_DIR / f"report_{inspection_data.get('id', 'unknown')}.pdf"

    styles = _get_styles()

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    elements = []

    # ---- Header ----
    elements.append(Paragraph("LegalMetriX", styles['ReportTitle']))
    elements.append(Paragraph(
        "Legal Metrology Inspection &amp; Compliance Platform",
        styles['ReportSubtitle']
    ))
    elements.append(Paragraph(
        "Automated Inspection Report",
        ParagraphStyle(
            'ReportType',
            parent=styles['Normal'],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#1e40af'),
            fontName='Helvetica-Bold',
            spaceAfter=12,
        )
    ))

    # ---- Report metadata ----
    meta_data = [
        [Paragraph('<b>Report Number:</b>', styles['SmallText']),
         Paragraph(report_number, styles['FieldValue']),
         Paragraph('<b>Inspection ID:</b>', styles['SmallText']),
         Paragraph(f"#{inspection_data.get('id', '—')}", styles['FieldValue'])],
        [Paragraph('<b>Inspection Date:</b>', styles['SmallText']),
         Paragraph(inspection_data.get('date', '—'), styles['FieldValue']),
         Paragraph('<b>Inspector:</b>', styles['SmallText']),
         Paragraph(inspection_data.get('inspector_name', '—'), styles['FieldValue'])],
        [Paragraph('<b>Report Generated:</b>', styles['SmallText']),
         Paragraph(datetime.now(timezone.utc).strftime('%d %B %Y, %H:%M UTC'), styles['FieldValue']),
         Paragraph('<b>Rule Version:</b>', styles['SmallText']),
         Paragraph('LM-PCR-2026', styles['FieldValue'])],
    ]

    meta_table = Table(meta_data, colWidths=[80, 150, 80, 150])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 16))

    # ---- Divider ----
    elements.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor('#e2e8f0'),
        spaceAfter=12, spaceBefore=8,
    ))

    # ---- Product Information ----
    elements.append(Paragraph("Product Information", styles['SectionTitle']))

    product_fields = [
        ('Product Name', extracted_fields.get('product_name')),
        ('Common / Generic Name', extracted_fields.get('brand_name')),
        ('Manufacturer', extracted_fields.get('manufacturer')),
        ('Packer', extracted_fields.get('marketer')),
        ('Manufacturer Address', extracted_fields.get('manufacturer_address')),
        ('Country of Origin', extracted_fields.get('country_of_origin')),
        ('Batch / Lot Number', extracted_fields.get('batch_number')),
        ('Net Quantity', _format_net_quantity(extracted_fields.get('net_quantity'))),
        ('MRP', _format_mrp(extracted_fields.get('mrp'))),
        ('Manufacturing Date', extracted_fields.get('manufacturing_date')),
        ('Best Before / Expiry', extracted_fields.get('best_before') or extracted_fields.get('expiry_date')),
        ('Consumer Care', _format_customer_care(extracted_fields.get('customer_care'))),
    ]

    product_data = []
    for label, value in product_fields:
        display_value = value if value else 'Not detected'
        product_data.append([
            Paragraph(f'<b>{label}</b>', styles['SmallText']),
            Paragraph(str(display_value), styles['FieldValue']),
        ])

    product_table = Table(product_data, colWidths=[130, 330])
    product_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -2), 0.25, colors.HexColor('#f1f5f9')),
        ('LINEBELOW', (0, -1), (-1, -1), 0.25, colors.HexColor('#f1f5f9')),
    ]))
    elements.append(product_table)
    elements.append(Spacer(1, 12))

    # ---- Package Image ----
    if image_path and os.path.exists(image_path):
        elements.append(HRFlowable(
            width="100%", thickness=1,
            color=colors.HexColor('#e2e8f0'),
            spaceAfter=12, spaceBefore=8,
        ))
        elements.append(Paragraph("Package Image", styles['SectionTitle']))
        try:
            img = RLImage(image_path, width=160, height=160, kind='proportional')
            elements.append(img)
            elements.append(Spacer(1, 12))
        except Exception as e:
            logger.warning(f"Could not embed image in PDF: {e}")

    # ---- OCR Summary ----
    ocr_confidence = inspection_data.get('ocr_confidence')
    if ocr_confidence is not None:
        elements.append(HRFlowable(
            width="100%", thickness=1,
            color=colors.HexColor('#e2e8f0'),
            spaceAfter=12, spaceBefore=8,
        ))
        elements.append(Paragraph("OCR Analysis Summary", styles['SectionTitle']))
        ocr_data = [
            [Paragraph('<b>OCR Confidence:</b>', styles['SmallText']),
             Paragraph(f'{ocr_confidence:.1f}%', styles['FieldValue'])],
        ]
        ocr_table = Table(ocr_data, colWidths=[130, 330])
        ocr_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(ocr_table)
        elements.append(Spacer(1, 8))

    # ---- Compliance Summary ----
    elements.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor('#e2e8f0'),
        spaceAfter=12, spaceBefore=8,
    ))
    elements.append(Paragraph("Compliance Assessment", styles['SectionTitle']))

    overall_status = compliance_data.get('overall_status', 'NOT_EVALUATED')
    status_color = _status_color(overall_status)

    status_style = ParagraphStyle(
        'StatusLarge',
        parent=styles['Normal'],
        fontSize=16,
        leading=20,
        textColor=status_color,
        fontName='Helvetica-Bold',
        spaceAfter=8,
    )
    elements.append(Paragraph(f"Overall Assessment: {overall_status.replace('_', ' ')}", status_style))

    # Summary counts
    summary = compliance_data.get('summary', {})
    summary_data = [
        [Paragraph('<b>Rules Checked</b>', styles['SmallText']),
         Paragraph('<b>Passed</b>', styles['SmallText']),
         Paragraph('<b>Failed</b>', styles['SmallText']),
         Paragraph('<b>Warnings</b>', styles['SmallText']),
         Paragraph('<b>Not Verifiable</b>', styles['SmallText']),
         Paragraph('<b>Not Applicable</b>', styles['SmallText'])],
        [Paragraph(str(summary.get('rules_checked', 0)), styles['FieldValue']),
         Paragraph(str(summary.get('passed', 0)), styles['FieldValue']),
         Paragraph(str(summary.get('failed', 0)), styles['FieldValue']),
         Paragraph(str(summary.get('warnings', 0)), styles['FieldValue']),
         Paragraph(str(summary.get('not_verifiable', 0)), styles['FieldValue']),
         Paragraph(str(summary.get('not_applicable', 0)), styles['FieldValue'])],
    ]

    summary_table = Table(summary_data, colWidths=[77, 77, 77, 77, 77, 77])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 16))

    # ---- Rule-by-Rule Findings ----
    findings = compliance_data.get('findings', [])
    if findings:
        elements.append(Paragraph("Rule-by-Rule Assessment", styles['SectionTitle']))

        # Table header
        header = [
            Paragraph('<b>Rule</b>', styles['TableHeader']),
            Paragraph('<b>Requirement</b>', styles['TableHeader']),
            Paragraph('<b>Status</b>', styles['TableHeader']),
            Paragraph('<b>Evidence / Message</b>', styles['TableHeader']),
        ]

        table_data = [header]
        for rule in findings:
            rule_status = rule.get('status', '')
            rule_color = _status_color(rule_status)
            status_para_style = ParagraphStyle(
                'RuleStatus',
                parent=styles['TableCell'],
                textColor=rule_color,
                fontName='Helvetica-Bold',
                fontSize=8,
            )

            evidence = rule.get('evidence') or rule.get('message', '—')
            if len(str(evidence)) > 120:
                evidence = str(evidence)[:117] + '...'

            table_data.append([
                Paragraph(f"<b>{rule.get('rule_id', '')}</b>", styles['TableCell']),
                Paragraph(rule.get('rule_name', ''), styles['TableCell']),
                Paragraph(rule_status.replace('_', ' '), status_para_style),
                Paragraph(str(evidence), styles['TableCell']),
            ])

        findings_table = Table(table_data, colWidths=[55, 110, 65, 230])
        findings_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('LINEBELOW', (0, 0), (-1, -1), 0.25, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))
        elements.append(findings_table)

    # ---- Disclaimer ----
    elements.append(Spacer(1, 24))
    elements.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor('#fde68a'),
        spaceAfter=12, spaceBefore=8,
    ))

    disclaimer_style = ParagraphStyle(
        'DisclaimerBox',
        parent=styles['DisclaimerText'],
        backColor=colors.HexColor('#fffbeb'),
        borderPadding=8,
        borderWidth=0.5,
        borderColor=colors.HexColor('#fde68a'),
    )
    elements.append(Paragraph(
        "<b>Disclaimer:</b> This report is an automated inspection-assistance document "
        "generated from the uploaded package image and extracted declarations. "
        "It does not constitute a final legal determination. "
        "Final verification and enforcement decisions remain with the authorized "
        "Legal Metrology officer.",
        disclaimer_style
    ))

    # ---- Build PDF ----
    doc.build(elements)
    logger.info(f"PDF report generated: {pdf_path}")
    return str(pdf_path)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _format_mrp(mrp_data: Optional[dict]) -> str:
    """Format MRP for display."""
    if not mrp_data:
        return 'Not detected'
    value = mrp_data.get('value')
    currency = mrp_data.get('currency', 'INR')
    if value is not None:
        return f"₹{value:,.2f}" if currency == 'INR' else f"{currency} {value:,.2f}"
    return 'Not detected'


def _format_net_quantity(nq_data: Optional[dict]) -> str:
    """Format net quantity for display."""
    if not nq_data:
        return 'Not detected'
    value = nq_data.get('value')
    unit = nq_data.get('unit', '')
    if value is not None:
        return f"{value} {unit}".strip()
    return 'Not detected'


def _format_customer_care(cc_data: Optional[dict]) -> str:
    """Format customer care for display."""
    if not cc_data:
        return 'Not detected'
    parts = []
    if cc_data.get('phone'):
        parts.append(f"Phone: {cc_data['phone']}")
    if cc_data.get('email'):
        parts.append(f"Email: {cc_data['email']}")
    if cc_data.get('address'):
        parts.append(f"Address: {cc_data['address']}")
    return '; '.join(parts) if parts else 'Not detected'
