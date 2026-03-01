# logic/profit_calculator.py
# -----------------------------------------------
# Calculates profit margin for a matched product.
# Formula:
#   Revenue  = eBay sale price
#   Costs    = AliExpress price + shipping + eBay fee
#   Profit   = Revenue - Costs
#   Margin   = Profit / Revenue
# Only returns result if margin >= 25%
# -----------------------------------------------

from config import EBAY_FEE_RATE, MIN_PROFIT_MARGIN
from utils.logger import get_logger

logger = get_logger(__name__)


def calculate_profit(
    ebay_price: float,
    ebay_shipping: float,
    ali_price: float,
    ali_shipping: float
) -> dict | None:
    """
    Calculate net profit margin.
    Returns None if margin is below minimum threshold.

    Example:
        eBay price    = $30.00
        eBay fee      = $3.90  (13%)
        AliExpress    = $8.00
        Ali shipping  = $0.00
        ---------------------------
        Profit        = $30.00 - $3.90 - $8.00 = $18.10
        Margin        = $18.10 / $30.00 = 60.3%  ✓ passes
    """
    try:
        if ebay_price <= 0:
            return None

        ebay_fee   = ebay_price * EBAY_FEE_RATE
        total_cost = ali_price + ali_shipping + ebay_fee
        profit     = ebay_price - total_cost
        margin     = profit / ebay_price

        logger.debug(
            f"eBay=${ebay_price:.2f} | "
            f"Ali=${ali_price:.2f} | "
            f"Fee=${ebay_fee:.2f} | "
            f"Profit=${profit:.2f} | "
            f"Margin={margin:.1%}"
        )

        # Reject if below minimum margin
        if margin < MIN_PROFIT_MARGIN:
            logger.debug(f"Margin {margin:.1%} below {MIN_PROFIT_MARGIN:.0%} threshold — skipped")
            return None

        return {
            "ebay_price"   : round(ebay_price, 2),
            "ebay_fee"     : round(ebay_fee, 2),
            "ali_price"    : round(ali_price, 2),
            "ali_shipping" : round(ali_shipping, 2),
            "profit"       : round(profit, 2),
            "margin_pct"   : round(margin * 100, 2),
        }

    except Exception as e:
        logger.error(f"Profit calculation error: {e}", exc_info=True)
        return None