# Quick Start Guide

## 🚀 Get Running in 2 Minutes

### Step 1: Clone and Setup
```bash
# Navigate to project directory
cd universal-website-scraper

# Make run script executable and run
chmod +x run.sh
./run.sh
```

The script will automatically:
- Create a virtual environment
- Install all Python dependencies
- Download Playwright's Chromium browser (~150MB)
- Start the server on http://localhost:8000

### Step 2: Test the Server

Open your browser and go to: **http://localhost:8000**

Or test via command line:
```bash
curl http://localhost:8000/healthz
```

Expected response:
```json
{
  "status": "ok"
}
```

### Step 3: Try Scraping

#### Via Web Interface:
1. Open http://localhost:8000
2. Enter a URL (try: `https://en.wikipedia.org/wiki/Artificial_intelligence`)
3. Click "Scrape"
4. View extracted sections
5. Download JSON

#### Via API:
```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://en.wikipedia.org/wiki/Artificial_intelligence"}'
```

### Step 4: Run Test Suite (Optional)

In a new terminal:
```bash
# Activate the virtual environment
source venv/bin/activate

# Run tests
python test_scraper.py
```

## 📝 Recommended Test URLs

### Static Page (Fast - ~2-5 seconds)
```
https://en.wikipedia.org/wiki/Artificial_intelligence
```
- Tests: Static HTML parsing, sections, tables, images
- Expected: 10-20 sections with rich content

### JS-Rendered Page (Moderate - ~10-20 seconds)
```
https://vercel.com/
```
- Tests: JS rendering fallback, tabs, dynamic content
- Expected: Multiple sections with hero, features, pricing

### Pagination (Slow - ~20-30 seconds)
```
https://news.ycombinator.com/
```
- Tests: Pagination links, depth 3, link extraction
- Expected: 3+ pages visited, 90+ links

## ⚙️ Troubleshooting

### "Command not found: python3"
Install Python 3.10+ from python.org

### "Port 8000 already in use"
Kill the process using port 8000:
```bash
# Find process
lsof -ti:8000

# Kill process
kill -9 $(lsof -ti:8000)
```

Or change the port in `run.sh`:
```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

### "Playwright installation failed"
Manually install:
```bash
source venv/bin/activate
playwright install chromium
```

### Slow scraping
- First run downloads browser (~150MB)
- JS rendering takes 10-20s (normal)
- Check your internet connection

## 🎯 What to Expect

### Static Scraping (Wikipedia)
- Time: 2-5 seconds
- Strategy: Static HTTP request
- Sections: 10-20
- Interactions: Minimal

### JS Rendering (Vercel)
- Time: 10-20 seconds
- Strategy: Playwright fallback
- Sections: 5-10
- Interactions: Tab clicks, scrolls

### Pagination (Hacker News)
- Time: 20-30 seconds
- Strategy: Follow pagination links
- Sections: 3-5 per page
- Interactions: 3 page visits

## 📦 Project Files

```
.
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── run.sh              # Setup and run script
├── README.md           # Full documentation
├── design_notes.md     # Implementation details
├── capabilities.json   # Feature matrix
├── test_scraper.py     # Test suite
├── .gitignore          # Git ignore rules
└── QUICKSTART.md       # This file
```

## 🔍 Next Steps

1. ✅ Review `design_notes.md` for implementation details
2. ✅ Check `capabilities.json` for supported features
3. ✅ Read `README.md` for complete documentation
4. ✅ Customize for your use case

## 💡 Tips

- **Speed**: Static scraping is ~5x faster than JS rendering
- **Depth**: Pagination limited to 3 levels for performance
- **Errors**: Check the `errors[]` array in responses
- **Timeouts**: Increase for slow websites (edit `main.py`)
- **Debugging**: Use "View Raw JSON" to inspect full response

## 🆘 Need Help?

Check the full README.md for:
- Detailed API documentation
- Error handling guide
- Performance optimization
- Known limitations
- Development tips

---

Happy Scraping! 🕷️