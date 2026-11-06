# ============================================================
# GRADE CARD
# Builds the downloadable Student Grade Card (A4 portrait PDF).
#
# This file only DRAWS a result. It never calculates one:
# totals, percentage, grades and Pass/Fail all come from the
# report built by student_manager.get_student_report(), which
# uses grade_functions.py. The PDF therefore always matches what
# the app shows on screen.
# ============================================================

import re
from datetime import datetime
from io import BytesIO

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from grade_functions import PASS_MARK, calculate_percentage, get_student_result

# ------------------------------------------------------------
# DESIGN TOKENS
# ------------------------------------------------------------

PAGE_W, PAGE_H = A4
MARGIN = 34
CONTENT_W = PAGE_W - 2 * MARGIN

REGULAR = "Helvetica"
BOLD = "Helvetica-Bold"

NAVY = HexColor("#13264F")
NAVY_TABLE = HexColor("#1B2F5E")
SLATE = HexColor("#2B3A57")
MUTED = HexColor("#5E6F8D")
PANEL = HexColor("#E8EEFB")
PANEL_STRIP = HexColor("#DCE6F8")
BORDER = HexColor("#C5D1E8")
ROW_ALT = HexColor("#F1F5FD")
GRID = HexColor("#CBD5E6")
WHITE = white

GREEN_BG, GREEN_FG = HexColor("#C9F0D2"), HexColor("#0E6B2C")
RED_BG, RED_FG = HexColor("#F8C9C9"), HexColor("#B3261E")

# Pastel pill colours for each grade, matching the reference design.
GRADE_BG = {
    "A": HexColor("#C6EFCE"),
    "B": HexColor("#CFE0FA"),
    "C": HexColor("#FCE8A6"),
    "D": HexColor("#FAD7B5"),
    "E": HexColor("#F8C4B0"),
    "F": HexColor("#F5B8B8"),
}

# Display text for the grade scale. app.py passes in its own GRADE_BANDS so
# there is a single source of truth; this copy is only a fallback.
DEFAULT_GRADE_BANDS = [
    ("A", "90 to 100"),
    ("B", "80 to 89"),
    ("C", "70 to 79"),
    ("D", "60 to 69"),
    ("E", "40 to 59"),
    ("F", "below 40"),
]

# ------------------------------------------------------------
# TEXT HELPERS
# ------------------------------------------------------------


def _safe(text):
    """Make text safe for the built-in PDF fonts (Latin-1 range)."""
    text = "" if text is None else str(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.encode("cp1252", "replace").decode("cp1252")


def _fmt(value):
    """Show whole numbers without .0 and keep decimals short."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def _ellipsize(text, font, size, width):
    """Shorten text with '...' so it never exceeds the width."""
    if stringWidth(text, font, size) <= width:
        return text
    while text and stringWidth(text + "...", font, size) > width:
        text = text[:-1]
    return text.rstrip() + "..."


def _wrap(text, font, size, width, max_lines=2, min_size=None):
    """
    Fit text inside a width. First wrap to several lines, then shrink the
    font towards min_size, and as a last resort cut with '...'.
    Returns (lines, font_size).
    """
    text = _safe(text)
    min_size = min_size or size
    current = size
    while True:
        lines = simpleSplit(text, font, current, width) or [""]
        fits = len(lines) <= max_lines and all(
            stringWidth(line, font, current) <= width for line in lines
        )
        if fits or current <= min_size:
            break
        current -= 0.5

    if len(lines) > max_lines:
        lines = lines[: max_lines - 1] + [" ".join(lines[max_lines - 1:])]
    lines = [_ellipsize(line, font, current, width) for line in lines]
    return lines, current


def _file_safe(text):
    """Turn a name into something safe to use in a file name."""
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", str(text or "")).strip("_")
    return cleaned[:60]


def grade_card_filename(report):
    """Meaningful download name, e.g. Anjali_Menon_GradeCard.pdf."""
    base = _file_safe(report.get("name")) or _file_safe(report.get("id")) or "Student"
    return f"{base}_GradeCard.pdf"


# ------------------------------------------------------------
# DRAWING HELPERS (all positions are measured from the TOP of the page)
# ------------------------------------------------------------


def _y(top):
    return PAGE_H - top


def _box(c, x, top, w, h, radius=0, fill=None, stroke=None, line=0.8):
    c.saveState()
    if fill is not None:
        c.setFillColor(fill)
    if stroke is not None:
        c.setStrokeColor(stroke)
        c.setLineWidth(line)
    c.roundRect(
        x, _y(top) - h, w, h, radius,
        stroke=1 if stroke is not None else 0,
        fill=1 if fill is not None else 0,
    )
    c.restoreState()


def _hline(c, x1, x2, top, colour=GRID, width=0.7):
    c.saveState()
    c.setStrokeColor(colour)
    c.setLineWidth(width)
    c.line(x1, _y(top), x2, _y(top))
    c.restoreState()


def _vline(c, x, top1, top2, colour=GRID, width=0.7):
    c.saveState()
    c.setStrokeColor(colour)
    c.setLineWidth(width)
    c.line(x, _y(top1), x, _y(top2))
    c.restoreState()


def _text(c, x, baseline_top, text, font=REGULAR, size=10, colour=SLATE, align="left"):
    c.saveState()
    c.setFont(font, size)
    c.setFillColor(colour)
    if align == "center":
        c.drawCentredString(x, _y(baseline_top), text)
    elif align == "right":
        c.drawRightString(x, _y(baseline_top), text)
    else:
        c.drawString(x, _y(baseline_top), text)
    c.restoreState()


def _pill(c, cx, mid_top, w, h, text, bg, fg, size=11):
    """A rounded label centred on (cx, mid_top)."""
    _box(c, cx - w / 2, mid_top - h / 2, w, h, radius=min(h / 2.4, 8), fill=bg)
    _text(c, cx, mid_top + size * 0.35, text, BOLD, size, fg, align="center")


def _clip_round_rect(c, x, top, w, h, radius):
    path = c.beginPath()
    path.roundRect(x, _y(top) - h, w, h, radius)
    c.clipPath(path, stroke=0, fill=0)


# ------------------------------------------------------------
# DECORATION AND ICONS
# ------------------------------------------------------------


def _draw_background(c):
    """White page with soft light-blue corner shapes (real vector paths)."""
    c.saveState()
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    # Top-left wave, two layers.
    for colour, size in ((HexColor("#DCE7FB"), 1.0), (HexColor("#C4D6F7"), 0.62)):
        p = c.beginPath()
        p.moveTo(0, PAGE_H)
        p.lineTo(190 * size, PAGE_H)
        p.curveTo(130 * size, PAGE_H - 20, 50 * size, PAGE_H - 55 * size, 0, PAGE_H - 105 * size)
        p.close()
        c.setFillColor(colour)
        c.drawPath(p, stroke=0, fill=1)

    # Bottom-right wave, two layers.
    for colour, size in ((HexColor("#DCE7FB"), 1.0), (HexColor("#C4D6F7"), 0.62)):
        p = c.beginPath()
        p.moveTo(PAGE_W, 0)
        p.lineTo(PAGE_W - 240 * size, 0)
        p.curveTo(PAGE_W - 150 * size, 14, PAGE_W - 60 * size, 38 * size, PAGE_W, 110 * size)
        p.close()
        c.setFillColor(colour)
        c.drawPath(p, stroke=0, fill=1)

    # Bottom-left soft shape.
    p = c.beginPath()
    p.moveTo(0, 0)
    p.lineTo(140, 0)
    p.curveTo(90, 12, 35, 22, 0, 48)
    p.close()
    c.setFillColor(HexColor("#E6EEFC"))
    c.drawPath(p, stroke=0, fill=1)
    c.restoreState()


def _draw_logo(c, x, base_top):
    """Three rising bars: the Gradebook mark."""
    bars = [(9, 15, HexColor("#F5B50A")), (9, 28, HexColor("#3F83E8")), (9, 40, NAVY_TABLE)]
    cursor = x
    for width, height, colour in bars:
        _box(c, cursor, base_top - height, width, height, radius=2.5, fill=colour)
        cursor += width + 4


def _draw_avatar(c, cx, cy_top, radius=38):
    """Round avatar with a graduation cap."""
    cy = _y(cy_top)
    c.saveState()
    c.setFillColor(HexColor("#CBD9F4"))
    c.circle(cx, cy, radius, stroke=0, fill=1)

    # Clip the body to the circle.
    clip = c.beginPath()
    clip.circle(cx, cy, radius)
    c.clipPath(clip, stroke=0, fill=0)

    c.setFillColor(NAVY)
    c.ellipse(cx - 28, cy - 58, cx + 28, cy - 8, stroke=0, fill=1)  # shoulders
    c.circle(cx, cy + 1, 12.5, stroke=0, fill=1)  # head

    # Cap: board + band + tassel.
    c.setFillColor(HexColor("#0C1B3D"))
    board = c.beginPath()
    board.moveTo(cx - 29, cy + 16)
    board.lineTo(cx, cy + 28)
    board.lineTo(cx + 29, cy + 16)
    board.lineTo(cx, cy + 6)
    board.close()
    c.drawPath(board, stroke=0, fill=1)
    c.setFillColor(HexColor("#1B2F5E"))
    c.rect(cx - 12, cy + 9, 24, 7, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#0C1B3D"))
    c.setLineWidth(1.4)
    c.line(cx + 24, cy + 17, cx + 24, cy + 5)
    c.restoreState()


def _draw_award(c, x, mid_top):
    """Small award rosette used in the Summary title."""
    cy = _y(mid_top)
    c.saveState()
    c.setFillColor(NAVY_TABLE)
    for dx in (-3.5, 3.5):
        tail = c.beginPath()
        tail.moveTo(x + dx - 3, cy - 2)
        tail.lineTo(x + dx + 3, cy - 2)
        tail.lineTo(x + dx + (2 if dx > 0 else -2), cy - 11)
        tail.close()
        c.drawPath(tail, stroke=0, fill=1)
    c.circle(x, cy + 2, 7.5, stroke=0, fill=1)
    c.setFillColor(PANEL_STRIP)
    c.circle(x, cy + 2, 3.2, stroke=0, fill=1)
    c.restoreState()


def _draw_mini_bars(c, x, base_top):
    for i, height in enumerate((7, 12, 17)):
        _box(c, x + i * 7, base_top - height, 5, height, radius=1.2, fill=NAVY_TABLE)


def _draw_calendar(c, x, mid_top):
    top = mid_top - 8
    _box(c, x, top, 16, 16, radius=3, stroke=NAVY_TABLE, line=1.2)
    _box(c, x, top, 16, 5, radius=2, fill=NAVY_TABLE)
    for i in range(3):
        for j in range(2):
            _box(c, x + 3 + i * 4, top + 8 + j * 4, 2, 2, fill=NAVY_TABLE)


# ------------------------------------------------------------
# SECTIONS
# ------------------------------------------------------------


def _section_header(c):
    top = 34
    _draw_logo(c, MARGIN + 6, top + 44)
    _text(c, MARGIN + 58, top + 25, "Gradebook", BOLD, 26, NAVY)
    _text(c, MARGIN + 58, top + 42, "Student Grade Management System", REGULAR, 9.5, SLATE)

    divider_x = MARGIN + 272
    _vline(c, divider_x, top + 4, top + 54, colour=HexColor("#8795B2"), width=0.9)

    centre = (divider_x + PAGE_W - MARGIN) / 2
    title_size = 23
    while stringWidth("Student Grade Card", BOLD, title_size) > (PAGE_W - MARGIN - divider_x - 16):
        title_size -= 0.5
    _text(c, centre, top + 24, "Student Grade Card", BOLD, title_size, NAVY, align="center")
    _text(c, centre, top + 43, "Academic Performance Report", REGULAR, 13, MUTED, align="center")
    return top + 62


def _section_student(c, top, report):
    """Rounded information panel. Height grows with long names/classes."""
    text_x = MARGIN + 130
    colon_x = text_x + 102
    value_x = colon_x + 14
    right_edge = MARGIN + CONTENT_W - 16
    value_w = right_edge - value_x
    name_w = right_edge - text_x

    name_lines, name_size = _wrap(report.get("name", ""), BOLD, 20, name_w, 2, 13)

    fields = [
        ("Class / Course", report.get("class", "")),
        ("Student ID", report.get("id", "")),
    ]
    # Only shown when the saved record actually has it.
    academic_year = _safe(report.get("academic_year", ""))
    if academic_year:
        fields.append(("Academic Year", academic_year))

    laid_out = []
    rows_h = 0
    for label, value in fields:
        lines, size = _wrap(value, REGULAR, 11.5, value_w, 2, 9)
        laid_out.append((label, lines, size))
        rows_h += 17 + (len(lines) - 1) * 13

    name_h = len(name_lines) * (name_size + 3)
    pad = 17
    height = max(104, pad + name_h + 8 + rows_h + pad - 4)

    _box(c, MARGIN, top, CONTENT_W, height, radius=14, fill=PANEL)
    _draw_avatar(c, MARGIN + 60, top + height / 2)
    _vline(c, MARGIN + 112, top + 18, top + height - 18, colour=HexColor("#9FB0D0"), width=0.8)

    cursor = top + pad + name_size - 2
    for line in name_lines:
        _text(c, text_x, cursor, line, BOLD, name_size, NAVY)
        cursor += name_size + 3
    cursor += 6

    for label, lines, size in laid_out:
        _text(c, text_x, cursor, label, BOLD, 11, NAVY)
        _text(c, colon_x, cursor, ":", BOLD, 11, NAVY)
        for index, line in enumerate(lines):
            _text(c, value_x, cursor + index * 13, line, REGULAR, size, SLATE)
        cursor += 17 + (len(lines) - 1) * 13
    return top + height


def _section_table(c, top, subject_rows, row_h):
    """Subject marks table with navy header and alternating rows."""
    widths = [42, 165, 100, 80, 82, 58]
    assert abs(sum(widths) - CONTENT_W) < 1.0
    xs = [MARGIN]
    for w in widths:
        xs.append(xs[-1] + w)
    header_h = 29
    total_h = header_h + row_h * len(subject_rows)

    c.saveState()
    _clip_round_rect(c, MARGIN, top, CONTENT_W, total_h, 9)
    _box(c, MARGIN, top, CONTENT_W, header_h, fill=NAVY_TABLE)
    for index in range(len(subject_rows)):
        row_top = top + header_h + index * row_h
        _box(c, MARGIN, row_top, CONTENT_W, row_h, fill=WHITE if index % 2 == 0 else ROW_ALT)
    c.restoreState()

    # Horizontal lines and column dividers.
    for index in range(1, len(subject_rows)):
        _hline(c, MARGIN, MARGIN + CONTENT_W, top + header_h + index * row_h)
    for x in xs[1:-1]:
        _vline(c, x, top, top + header_h, colour=HexColor("#4A5F8F"))
        _vline(c, x, top + header_h, top + total_h)

    headers = ["No.", "Subject", "Marks Obtained", "Total Marks", "Percentage", "Grade"]
    for index, label in enumerate(headers):
        if index == 1:
            _text(c, xs[index] + 14, top + 18.5, label, BOLD, 10.5, WHITE)
        else:
            _text(c, (xs[index] + xs[index + 1]) / 2, top + 18.5, label, BOLD, 10.5, WHITE, align="center")

    for index, row in enumerate(subject_rows):
        mid = top + header_h + index * row_h + row_h / 2
        base = mid + 4
        failing = row["failing"]

        _text(c, (xs[0] + xs[1]) / 2, base, str(index + 1), REGULAR, 11, SLATE, align="center")

        subject_lines, subject_size = _wrap(row["subject"], REGULAR, 11.5, widths[1] - 22, 1, 8)
        _text(c, xs[1] + 14, base, subject_lines[0], REGULAR, subject_size, SLATE)

        mark_font, mark_colour = (BOLD, RED_FG) if failing else (REGULAR, SLATE)
        _text(c, (xs[2] + xs[3]) / 2, base, row["mark"], mark_font, 11.5, mark_colour, align="center")
        _text(c, (xs[3] + xs[4]) / 2, base, row["out_of"], REGULAR, 11.5, SLATE, align="center")
        _text(c, (xs[4] + xs[5]) / 2, base, row["percentage"], mark_font, 11.5, mark_colour, align="center")

        _pill(c, (xs[5] + xs[6]) / 2, mid, 36, 17, row["grade"], GRADE_BG.get(row["grade"], PANEL), NAVY, 10.5)

    _box(c, MARGIN, top, CONTENT_W, total_h, radius=9, stroke=BORDER, line=0.9)
    return top + total_h


def _section_overall(c, top, summary):
    height = 68
    _box(c, MARGIN, top, CONTENT_W, height, radius=12, fill=PANEL)

    widths = [200, 160, CONTENT_W - 360]
    xs = [MARGIN]
    for w in widths:
        xs.append(xs[-1] + w)
    for x in xs[1:-1]:
        _vline(c, x, top + 12, top + height - 12, colour=HexColor("#9FB0D0"), width=0.8)

    centres = [(xs[i] + xs[i + 1]) / 2 for i in range(3)]
    for centre, label in zip(centres, ("Overall Percentage", "Result", "Overall Grade")):
        _text(c, centre, top + 19, label, BOLD, 12, NAVY, align="center")

    _text(c, centres[0], top + 54, summary["percentage"], BOLD, 31, NAVY, align="center")

    passed = summary["result"] == "Pass"
    _pill(c, centres[1], top + 43, 96, 28, summary["result"].upper(),
          GREEN_BG if passed else RED_BG, GREEN_FG if passed else RED_FG, 17)
    _pill(c, centres[2], top + 43, 76, 28, summary["grade"],
          GRADE_BG.get(summary["grade"], PANEL_STRIP), NAVY, 18)
    return top + height


def _section_note(c, top, summary):
    """One line that explains the pass rule, or why the result is Fail."""
    if summary["failing"]:
        names = ", ".join(f"{s} ({m})" for s, m in summary["failing"])
        message = f"Result is FAIL: below the pass mark of {PASS_MARK} in {names}."
        colour = RED_FG
    else:
        message = f"A student passes by scoring at least {PASS_MARK} marks in every subject."
        colour = MUTED
    lines, size = _wrap(message, REGULAR, 8.5, CONTENT_W - 8, 2, 7.5)
    for index, line in enumerate(lines):
        _text(c, MARGIN + 4, top + 11 + index * 10.5, line, REGULAR, size, colour)
    return top + 8 + len(lines) * 10.5


def _section_grade_scale(c, x, top, w, h, bands):
    _box(c, x, top, w, h, radius=11, fill=WHITE)
    c.saveState()
    _clip_round_rect(c, x, top, w, h, 11)
    _box(c, x, top, w, 30, fill=PANEL)
    c.restoreState()
    _box(c, x, top, w, h, radius=11, stroke=BORDER, line=0.9)

    _draw_mini_bars(c, x + 14, top + 22)
    _text(c, x + 44, top + 20, "Grade Scale", BOLD, 13.5, NAVY)

    inner_x, inner_w = x + 13, w - 26
    table_top = top + 40
    head_h = 21
    row_h = (h - 40 - head_h - 12) / len(bands)

    _box(c, inner_x, table_top, inner_w, head_h, fill=PANEL_STRIP)
    split = inner_x + inner_w * 0.38
    _text(c, (inner_x + split) / 2, table_top + 14.5, "Grade", BOLD, 10.5, NAVY, align="center")
    _text(c, (split + inner_x + inner_w) / 2, table_top + 14.5, "Marks Range", BOLD, 10.5, NAVY, align="center")

    for index, (grade, text) in enumerate(bands):
        row_top = table_top + head_h + index * row_h
        _hline(c, inner_x, inner_x + inner_w, row_top, colour=GRID)
        _pill(c, (inner_x + split) / 2, row_top + row_h / 2, (split - inner_x) - 22, row_h - 5,
              grade, GRADE_BG.get(grade, PANEL), NAVY, 10.5)
        label = text[:1].upper() + text[1:]
        _text(c, (split + inner_x + inner_w) / 2, row_top + row_h / 2 + 4, label, REGULAR, 11, SLATE, align="center")

    bottom = table_top + head_h + row_h * len(bands)
    _hline(c, inner_x, inner_x + inner_w, bottom, colour=GRID)
    _box(c, inner_x, table_top, inner_w, bottom - table_top, stroke=GRID, line=0.7)
    _vline(c, split, table_top, bottom, colour=GRID)


def _section_summary(c, x, top, w, h, summary):
    _box(c, x, top, w, h, radius=11, fill=WHITE)
    c.saveState()
    _clip_round_rect(c, x, top, w, h, 11)
    _box(c, x, top, w, 30, fill=PANEL)
    c.restoreState()
    _box(c, x, top, w, h, radius=11, stroke=BORDER, line=0.9)

    _draw_award(c, x + 20, top + 15)
    _text(c, x + 38, top + 20, "Summary", BOLD, 13.5, NAVY)

    rows = [
        ("Total Marks", summary["maximum"], None),
        ("Marks Obtained", summary["total"], None),
        ("Percentage", summary["percentage"], None),
        ("Overall Grade", summary["grade"], None),
        ("Result", summary["result"].upper(), GREEN_FG if summary["result"] == "Pass" else RED_FG),
    ]
    body_top = top + 30
    row_h = (h - 30 - 6) / len(rows)
    for index, (label, value, colour) in enumerate(rows):
        row_top = body_top + 3 + index * row_h
        base = row_top + row_h / 2 + 4
        _text(c, x + 18, base, label, REGULAR, 11.5, SLATE)
        _text(c, x + 124, base, ":", REGULAR, 11.5, SLATE)
        _text(c, x + 146, base, value, BOLD if colour else REGULAR, 12 if colour else 11.5, colour or SLATE)
        if index < len(rows) - 1:
            _hline(c, x + 14, x + w - 14, row_top + row_h, colour=GRID)


def _section_footer(c, top, generated_on):
    _hline(c, MARGIN, MARGIN + CONTENT_W, top, colour=HexColor("#D5DDEC"), width=0.6)
    _text(c, MARGIN + 6, top + 22, "Generated by ", REGULAR, 10.5, SLATE)
    offset = stringWidth("Generated by ", REGULAR, 10.5)
    _text(c, MARGIN + 6 + offset, top + 22, "Gradebook", BOLD, 10.5, NAVY)
    _text(c, MARGIN + 6, top + 35, "Student Grade Management System", REGULAR, 10, SLATE)

    divider_x = MARGIN + 270
    _vline(c, divider_x, top + 10, top + 42, colour=HexColor("#8795B2"), width=0.9)
    _draw_calendar(c, divider_x + 56, top + 26)
    _text(c, divider_x + 80, top + 30, f"Generated on: {generated_on}", REGULAR, 10.5, SLATE)


# ------------------------------------------------------------
# PUBLIC FUNCTION
# ------------------------------------------------------------


def _prepare(report):
    """
    Collect everything to print from the report. Nothing is recalculated:
    values come straight from get_student_report() / get_student_result().
    """
    if "subject_results" not in report:
        # A raw saved record was passed in; use the app's own function.
        report = {**report, **get_student_result(report["marks"])}

    subject_results = report["subject_results"]
    count = max(len(subject_results), 1)
    per_subject_max = report["maximum_marks"] // count

    rows = []
    for subject, details in subject_results.items():
        mark = details["mark"]
        rows.append({
            "subject": _safe(subject),
            "mark": _fmt(mark),
            "out_of": _fmt(per_subject_max),
            # Same function the app uses for percentages (every subject is out of 100).
            "percentage": f"{_fmt(calculate_percentage({subject: mark}))}%",
            "grade": details["grade"],
            "failing": details["result"] == "Fail",
        })

    summary = {
        "maximum": _fmt(report["maximum_marks"]),
        "total": _fmt(report["total"]),
        "percentage": f"{_fmt(report['percentage'])}%",
        "grade": report["grade"],
        "result": report["result"],
        "failing": [
            (_safe(subject), _fmt(details["mark"]))
            for subject, details in subject_results.items()
            if details["result"] == "Fail"
        ],
    }
    return report, rows, summary


def generate_grade_card_pdf(report, grade_bands=None, generated_on=None):
    """
    Build the grade card for one student and return the PDF as bytes.

    report       : dict from student_manager.get_student_report(student_id)
    grade_bands  : list of (grade, range text) for the Grade Scale box
    generated_on : optional datetime, defaults to now
    """
    report, rows, summary = _prepare(report)
    bands = grade_bands or DEFAULT_GRADE_BANDS
    stamp = (generated_on or datetime.now()).strftime("%d %b %Y")

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setTitle(f"Student Grade Card - {_safe(report.get('name', ''))}")
    c.setAuthor("Gradebook")
    c.setSubject("Academic Performance Report")

    _draw_background(c)
    top = _section_header(c)
    top = _section_student(c, top + 2, report)

    # Pick a row height that always leaves room for the lower sections,
    # even when a record has more subjects than the usual five.
    footer_top = PAGE_H - 84
    lower_h = 20 + 68 + 8 + 21 + 20 + 178 + 14
    available = footer_top - (top + 22 + 29) - lower_h
    row_h = max(17, min(30, available / max(len(rows), 1)))

    top = _section_table(c, top + 22, rows, row_h)
    top = _section_overall(c, top + 20, summary)
    top = _section_note(c, top + 4, summary)

    panel_top = top + 16
    panel_h = 178
    gap = 16
    left_w = 250
    _section_grade_scale(c, MARGIN, panel_top, left_w, panel_h, bands)
    _section_summary(c, MARGIN + left_w + gap, panel_top, CONTENT_W - left_w - gap, panel_h, summary)

    _section_footer(c, footer_top, stamp)

    c.showPage()
    c.save()
    return buffer.getvalue()
