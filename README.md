# 🔍 eBay Ali Hunter

A smart dropshipping opportunity finder that automatically scrapes eBay listings,
finds matching products on AliExpress, calculates profit margins, and exports
profitable products to a formatted Excel file — all through a clean web UI.

---

## 🚀 What It Does

- Scrapes eBay search results for your keywords
- Finds matching AliExpress products via Google search
- Calculates profit margin after eBay fees (13%)
- Filters only products with 25%+ profit margin
- Exports results to color-coded Excel file
- Shows everything live through a web dashboard

---

## 📸 Features

- ✅ Web UI — runs in your browser at localhost:5000
- ✅ Live logs — watch scraper work in real time
- ✅ Keywords manager — add/remove keywords from UI
- ✅ Excel export — color coded by profit margin
- ✅ Clickable links — direct eBay and AliExpress product links
- ✅ Welcome Deal detection — highlights AliExpress deals
- ✅ Anti-detection — human-like delays, stealth browser, session saving
- ✅ One click launch — just double click run.bat

---

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/ebay-ali-hunter.git
cd ebay-ali-hunter
```

### 2. Install dependencies
```bash
pip install playwright playwright-stealth rapidfuzz flask openpyxl
```

### 3. Install Playwright browser
```bash
playwright install chromium
```

### 4. Add your keywords
Open `data/keywords.txt` and add one keyword per line:
```
wireless earbuds
phone stand desk
led strip lights
```

---

## ▶️ How to Run

### Option A — Double click (easiest)
Just double click `run.bat`

### Option B — Terminal
```bash
python ui/app.py
```

Browser opens automatically at `http://localhost:5000`

---

## 📊 Excel Output

Results are saved to `data/results/` with timestamp.

| Color | Meaning |
|-------|---------|
| 🟦 Blue | AliExpress Welcome Deal |
| 🟩 Green | Profit margin 40%+ |
| 🟨 Yellow | Profit margin 25-40% |

---

## 📁 Project Structure
```
ebay_ali_hunter/
├── main.py                 # Run without UI
├── config.py               # All settings
├── run.bat                 # One click launcher
├── data/
│   └── keywords.txt        # Your search keywords
├── scrapers/
│   ├── browser.py          # Playwright browser manager
│   ├── ebay_scraper.py     # eBay scraping logic
│   └── ali_scraper.py      # AliExpress via Google
├── matching/
│   └── matcher.py          # Fuzzy title matching
├── logic/
│   └── profit_calculator.py # Profit margin calculation
├── output/
│   ├── exporter.py         # Excel export
│   └── deduplicator.py     # Remove duplicate results
├── pipeline/
│   └── runner.py           # Main pipeline orchestrator
├── ui/
│   ├── app.py              # Flask web server
│   ├── templates/
│   │   └── index.html      # Main UI page
│   └── static/
│       ├── style.css       # Dark theme styling
│       └── script.js       # Live logs and interactions
└── utils/
    ├── logger.py           # Logging setup
    ├── delays.py           # Human-like delays
    └── session_manager.py  # Browser session saving
```

---

## ⚙️ Configuration

All settings are in `config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `EBAY_FEE_RATE` | 0.13 | eBay fee percentage |
| `MIN_PROFIT_MARGIN` | 0.25 | Minimum profit margin filter |
| `MAX_EBAY_PAGES` | 2 | eBay pages to scrape per keyword |
| `SIMILARITY_THRESHOLD` | 60 | Fuzzy match strictness |
| `HEADLESS` | False | Hide/show browser window |

---

## ⚠️ Disclaimer

This tool is for personal educational use only.
Always respect website terms of service.

---

## 🙏 Built With

- [Playwright](https://playwright.dev/) — browser automation
- [Flask](https://flask.palletsprojects.com/) — web UI
- [RapidFuzz](https://github.com/maxbachmann/RapidFuzz) — fuzzy matching
- [OpenPyXL](https://openpyxl.readthedocs.io/) — Excel export