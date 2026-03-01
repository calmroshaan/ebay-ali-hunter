# config.py
# -----------------------------------------------
# Central settings file. Change values here only.
# No logic here — just constants.
# -----------------------------------------------

# --- Profit Settings ---
EBAY_FEE_RATE = 0.13          # eBay takes 13% of sale price
MIN_PROFIT_MARGIN = 0.25      # Only keep products with 25%+ margin

# --- Scraping Limits ---
MAX_EBAY_PAGES = 2            # How many eBay result pages to scrape per keyword
MAX_ALI_RESULTS = 30          # How many AliExpress results to collect per keyword

# --- Fuzzy Matching ---
SIMILARITY_THRESHOLD = 40     # 0-100. Higher = stricter title matching

# --- Delays (in seconds): (average, variation) ---
# Gaussian = more human-like than plain random
PAGE_LOAD_DELAY        = (4.0, 1.2)    # after a page loads
BETWEEN_ITEMS_DELAY    = (0.3, 0.1)    # between reading each product
BETWEEN_KEYWORDS_DELAY = (12.0, 4.0)  # between each keyword run
BETWEEN_SITES_DELAY    = (8.0, 2.5)   # between eBay and AliExpress

# --- Browser Settings ---
HEADLESS = False              # False = you can watch it work. True = no window.
VIEWPORT = {"width": 1366, "height": 768}
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

# --- File Paths ---
KEYWORDS_FILE = "data/keywords.txt"
OUTPUT_DIR    = "data/results/"
PROFILES_DIR  = "data/profiles/"

# --- Site URLs ---
EBAY_BASE_URL = "https://www.ebay.com/sch/i.html"
ALI_BASE_URL  = "https://www.google.com/search"