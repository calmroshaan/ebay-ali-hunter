# output/exporter.py
# -----------------------------------------------
# Saves profitable product matches to Excel file.
# Each run creates a new timestamped .xlsx file.
# Color coding:
#   Green  = margin 40%+  (great deal)
#   Yellow = margin 25-40% (decent deal)
# -----------------------------------------------

import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from config import OUTPUT_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

# --- Color definitions ---
COLOR_GREEN       = "C6EFCE"   # high margin 40%+
COLOR_YELLOW      = "FFEB9C"   # decent margin 25-40%
COLOR_HEADER_BG   = "2F4F7F"   # dark blue header
COLOR_HEADER_FONT = "FFFFFF"   # white header text

COLUMNS = [
    ("Keyword",         "keyword",       20),
    ("eBay Title",      "title",         40),
    ("eBay Price $",    "ebay_price",    12),
    ("eBay Shipping $", "ebay_shipping", 14),
    ("eBay Fee $",      "ebay_fee",      12),
    ("eBay URL",        "ebay_url",      30),
    ("Ali Title",       "ali_title",     40),
    ("Ali Price $",     "ali_price",     12),
    ("Ali Shipping $",  "ali_shipping",  14),
    ("Ali URL",         "ali_url",       30),
    ("Profit $",        "profit",        12),
    ("Margin %",        "margin_pct",    12),
    ("Match Score",     "match_score",   12),
    ("Sold Count",      "sold_count",    12),
    ("Seller Rating",   "seller_rating", 14),
]


def export_results(results: list[dict]) -> str | None:
    """
    Takes a list of profitable product dicts.
    Writes them to a formatted .xlsx Excel file.
    Returns the file path or None if nothing to save.
    """
    if not results:
        logger.info("No results to export")
        return None

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename  = f"results_{timestamp}.xlsx"
    filepath  = os.path.join(OUTPUT_DIR, filename)

    wb = Workbook()
    ws = wb.active
    ws.title = "Profitable Products"

    # --- Write header row ---
    _write_header(ws)

    # --- Write data rows ---
    for row_idx, product in enumerate(results, start=2):
        _write_row(ws, row_idx, product)

    # --- Freeze top row so header stays visible when scrolling ---
    ws.freeze_panes = "A2"

    # --- Auto filter on header row ---
    ws.auto_filter.ref = ws.dimensions

    try:
        wb.save(filepath)
        logger.info(f"Exported {len(results)} results -> {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        return None


def _write_header(ws):
    """Write styled header row."""
    header_fill = PatternFill("solid", fgColor=COLOR_HEADER_BG)
    header_font = Font(bold=True, color=COLOR_HEADER_FONT, size=11)
    thin_border = _get_border()

    for col_idx, (header, _, width) in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill      = header_fill
        cell.font      = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border    = thin_border
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    ws.row_dimensions[1].height = 20


def _write_row(ws, row_idx: int, product: dict):
    """Write one product row with color coding based on margin."""
    margin = product.get("margin_pct", 0)

    # Pick row color based on margin
    if margin >= 40:
        fill = PatternFill("solid", fgColor=COLOR_GREEN)
    else:
        fill = PatternFill("solid", fgColor=COLOR_YELLOW)

    thin_border = _get_border()

    for col_idx, (_, key, _) in enumerate(COLUMNS, start=1):
        value = product.get(key, "")

        # Round floats to 2 decimal places
        if isinstance(value, float):
            value = round(value, 2)

        cell = ws.cell(row=row_idx, column=col_idx, value=value)
        cell.fill      = fill
        cell.border    = thin_border
        cell.alignment = Alignment(vertical="center", wrap_text=False)

        # Make URLs clickable
        if key in ("ebay_url", "ali_url") and value:
            cell.hyperlink = str(value)
            cell.font      = Font(color="0000FF", underline="single")


def _get_border():
    """Thin border for all cells."""
    thin = Side(style="thin", color="CCCCCC")
    return Border(left=thin, right=thin, top=thin, bottom=thin)