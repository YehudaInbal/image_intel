import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

try:
    from bidi.algorithm import get_display
except Exception:
    get_display = None


PAGE_WIDTH, PAGE_HEIGHT = A4
DEFAULT_FONT_NAME = "Helvetica"
UNICODE_FONT_NAME = "DejaVuSans"


def _looks_like_hebrew(text: str) -> bool:
    return any("\u0590" <= char <= "\u05FF" for char in str(text))


def _resolve_font_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidate_paths = [
        os.path.join(base_dir, "static", "fonts", "DejaVuSans.ttf"),
        os.path.join(base_dir, "fonts", "DejaVuSans.ttf"),
        os.path.join(os.path.dirname(base_dir), "fonts", "DejaVuSans.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/local/share/fonts/DejaVuSans.ttf",
        "C:/Windows/Fonts/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]

    for path in candidate_paths:
        if os.path.exists(path):
            return path
    return None


def _register_unicode_font():
    if UNICODE_FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return UNICODE_FONT_NAME

    font_path = _resolve_font_path()
    if not font_path:
        return DEFAULT_FONT_NAME

    try:
        pdfmetrics.registerFont(TTFont(UNICODE_FONT_NAME, font_path))
        return UNICODE_FONT_NAME
    except Exception:
        return DEFAULT_FONT_NAME


ACTIVE_FONT_NAME = _register_unicode_font()


def _rtl_text(text):
    value = str(text or "")
    if not value:
        return ""

    if _looks_like_hebrew(value):
        if get_display is not None:
            return get_display(value)
        return value[::-1]

    return value


def _safe(value, fallback="N/A"):
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _build_styles(font_name):
    base_styles = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "IntelTitle",
            parent=base_styles["Title"],
            fontName=font_name,
            fontSize=21,
            leading=26,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=6,
            alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "IntelSubtitle",
            parent=base_styles["Normal"],
            fontName=font_name,
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor("#475569"),
            spaceAfter=8,
            alignment=TA_LEFT,
        ),
        "section": ParagraphStyle(
            "IntelSection",
            parent=base_styles["Heading2"],
            fontName=font_name,
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=8,
            spaceBefore=4,
            alignment=TA_LEFT,
        ),
        "body": ParagraphStyle(
            "IntelBody",
            parent=base_styles["BodyText"],
            fontName=font_name,
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#111827"),
            spaceAfter=4,
            alignment=TA_LEFT,
        ),
        "body_rtl": ParagraphStyle(
            "IntelBodyRTL",
            parent=base_styles["BodyText"],
            fontName=font_name,
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#111827"),
            spaceAfter=4,
            alignment=TA_RIGHT,
        ),
        "small": ParagraphStyle(
            "IntelSmall",
            parent=base_styles["BodyText"],
            fontName=font_name,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#64748B"),
            alignment=TA_LEFT,
        ),
    }


def _section_title(text, styles):
    return Paragraph(text, styles["section"])


def _stat_table(analysis, styles):
    date_range = analysis.get("date_range", {}) or {}
    rows = [
        ["Total Images", _safe(analysis.get("total_images", 0), "0")],
        ["Images with GPS", _safe(analysis.get("images_with_gps", 0), "0")],
        ["Images with Date/Time", _safe(analysis.get("images_with_datetime", 0), "0")],
        ["Unique Cameras", str(len(analysis.get("unique_cameras", []) or []))],
        ["Date Range", f"{_safe(date_range.get('start'))} → {_safe(date_range.get('end'))}"],
    ]

    table = Table(rows, colWidths=[58 * mm, 112 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("FONTNAME", (0, 0), (-1, -1), ACTIVE_FONT_NAME),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0F172A")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def _insights_story(analysis, styles):
    insights = analysis.get("insights", []) or []
    if not insights:
        return [Paragraph("No automated insights were generated.", styles["body"])]

    story = []
    for insight in insights:
        style = styles["body_rtl"] if _looks_like_hebrew(str(insight)) else styles["body"]
        story.append(Paragraph(f"• {_rtl_text(insight)}", style))
        story.append(Spacer(1, 2))
    return story


def _images_table(images_data, styles):
    header = [
        Paragraph("Filename", styles["body"]),
        Paragraph("Date/Time", styles["body"]),
        Paragraph("Camera", styles["body"]),
        Paragraph("GPS", styles["body"]),
    ]

    rows = [header]
    for img in images_data:
        filename = _safe(img.get("filename"))
        dt = _safe(img.get("datetime"))
        camera = _safe(img.get("camera_model") or img.get("camera_make"))
        gps = "YES" if img.get("has_gps") else "NO"

        rows.append(
            [
                Paragraph(filename, styles["body"]),
                Paragraph(dt, styles["body"]),
                Paragraph(_rtl_text(camera), styles["body_rtl"] if _looks_like_hebrew(camera) else styles["body"]),
                Paragraph(gps, styles["body"]),
            ]
        )

    table = Table(
        rows,
        colWidths=[55 * mm, 45 * mm, 56 * mm, 18 * mm],
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("FONTNAME", (0, 0), (-1, -1), ACTIVE_FONT_NAME),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _draw_page_chrome(canvas, doc):
    canvas.saveState()

    canvas.setFillColor(colors.HexColor("#0F172A"))
    canvas.rect(0, PAGE_HEIGHT - 16, PAGE_WIDTH, 16, fill=1, stroke=0)

    canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
    canvas.setLineWidth(0.7)
    canvas.line(doc.leftMargin, 18 * mm, PAGE_WIDTH - doc.rightMargin, 18 * mm)

    canvas.setFont(ACTIVE_FONT_NAME, 8)
    canvas.setFillColor(colors.HexColor("#475569"))
    canvas.drawString(doc.leftMargin, 12 * mm, "Image Intel | Visual EXIF Intelligence Report")
    canvas.drawRightString(PAGE_WIDTH - doc.rightMargin, 12 * mm, f"Page {canvas.getPageNumber()}")

    canvas.restoreState()


def export_report_to_pdf(images_data, analysis, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    styles = _build_styles(ACTIVE_FONT_NAME)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=22 * mm,
        bottomMargin=22 * mm,
        title="Image Intel Report",
        author="Image Intel",
    )

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    story = [
        Paragraph("IMAGE INTEL", styles["title"]),
        Paragraph("OSINT-style EXIF analysis report", styles["subtitle"]),
        Paragraph(f"Generated: {generated_at}", styles["small"]),
        Spacer(1, 8),
        _section_title("Executive Summary", styles),
        _stat_table(analysis, styles),
        Spacer(1, 10),
        _section_title("Automated Insights", styles),
    ]

    story.extend(_insights_story(analysis, styles))
    story.extend(
        [
            Spacer(1, 8),
            _section_title("Image Inventory", styles),
            _images_table(images_data, styles),
        ]
    )

    doc.build(story, onFirstPage=_draw_page_chrome, onLaterPages=_draw_page_chrome)
    return output_path