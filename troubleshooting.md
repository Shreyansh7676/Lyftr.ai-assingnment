# Troubleshooting Guide

## Common Issues and Solutions

### 1. Server Won't Start

#### Problem: "Command not found: python3"
**Solution:**
```bash
# Check if Python is installed
python --version  # Try without the '3'

# If not installed, install Python 3.10+
# macOS (with Homebrew)
brew install python@3.10

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.10

# Windows: Download from python.org
```

#### Problem: "Port 8000 already in use"
**Solution:**
```bash
# Find and kill the process using port 8000
# macOS/Linux
lsof -ti:8000 | xargs kill -9

# Or change the port in run.sh
# Edit line: uvicorn main:app --host 0.0.0.0 --port 8001
```

#### Problem: "Permission denied: ./run.sh"
**Solution:**
```bash
# Make the script executable
chmod +x run.sh
./run.sh
```

### 2. Playwright Installation Issues

#### Problem: "Playwright browsers not installing"
**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Manually install Chromium
playwright install chromium

# If that fails, install dependencies
playwright install-deps chromium
```

#### Problem: "Browser executable doesn't exist"
**Solution:**
```bash
# Clean reinstall
rm -rf ~/.cache/ms-playwright
playwright install chromium
```

#### Problem: "Connection timeout during browser download"
**Solution:**
- Check your internet connection
- If behind a firewall/proxy, configure:
```bash
export HTTPS_PROXY=http://your-proxy:port
playwright install chromium
```

### 3. Scraping Issues

#### Problem: "Scraping takes too long (> 60 seconds)"
**Causes:**
- Very slow website
- Heavy JavaScript rendering
- Multiple interactions

**Solutions:**
1. Increase timeout in code (main.py):
```python
async with httpx.AsyncClient(timeout=60.0) as client:  # Increase to 120.0
```

2. Reduce interaction depth:
```python
for depth in range(3):  # Change to range(2) for faster scraping
```

#### Problem: "Section array is empty"
**Causes:**
- Page blocked automation
- Content behind authentication
- JavaScript not loading

**Solutions:**
1. Check the errors array in response
2. Try a different test URL
3. Verify URL is publicly accessible

#### Problem: "Links/images have relative URLs"
**This should not happen** - the code converts to absolute URLs.
If you see relative URLs, check:
```python
# In _parse_section method, verify urljoin is working:
absolute_href = urljoin(source_url, href)
```

### 4. Frontend Issues

#### Problem: "Frontend shows blank page"
**Solution:**
```bash
# Check if server is running
curl http://localhost:8000/healthz

# Check browser console for errors (F12)
# Verify JavaScript is enabled
```

#### Problem: "Scrape button doesn't work"
**Solution:**
1. Open browser console (F12)
2. Look for JavaScript errors
3. Check network tab for API call
4. Verify CORS if using different domain

#### Problem: "JSON download not working"
**Solution:**
- Check browser's download settings
- Disable popup blockers
- Try "View Raw JSON" instead

### 5. Dependency Issues

#### Problem: "ModuleNotFoundError: No module named 'X'"
**Solution:**
```bash
# Ensure you're in virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Or install specific module
pip install fastapi uvicorn selectolax playwright httpx
```

#### Problem: "selectolax installation fails"
**Solution:**
```bash
# Install build dependencies first
# macOS
brew install gcc

# Ubuntu/Debian
sudo apt-get install build-essential python3-dev

# Then retry
pip install selectolax
```

### 6. Testing Issues

#### Problem: "test_scraper.py fails with connection error"
**Solution:**
```bash
# Ensure server is running in another terminal
./run.sh

# In new terminal, run tests
source venv/bin/activate
python test_scraper.py
```

#### Problem: "Tests timeout"
**Solution:**
Edit test_scraper.py and increase timeouts:
```python
async with httpx.AsyncClient(timeout=120.0) as client:  # Increase from 60.0
```

### 7. Performance Issues

#### Problem: "Memory usage too high"
**Causes:**
- Multiple browser instances
- Large HTML content
- Memory leaks

**Solutions:**
1. Restart the server
2. Reduce number of concurrent scrapes
3. Monitor with:
```bash
# Check memory usage
ps aux | grep python
```

#### Problem: "CPU usage at 100%"
**This is normal during:**
- Playwright browser launch
- JavaScript rendering
- HTML parsing

**If persistent:**
- Check for infinite loops in scraping logic
- Restart server
- Verify no runaway background processes

### 8. Specific Website Issues

#### Problem: "Wikipedia scraping fails"
**Solution:**
- Wikipedia should work with static scraping
- If failing, check internet connection
- Verify URL is exact: `https://en.wikipedia.org/wiki/Artificial_intelligence`

#### Problem: "Vercel.com shows empty sections"
**Solution:**
- Requires JS rendering (normal)
- Should automatically fallback to Playwright
- Check errors array for "using JS rendering" message

#### Problem: "Hacker News pagination not working"
**Solution:**
- Pagination links may have changed
- Check the actual page structure
- Update selectors in `_perform_scroll_pagination` if needed

### 9. Development Issues

#### Problem: "Code changes not reflecting"
**Solution:**
```bash
# Server should auto-reload with --reload flag
# If not, manually restart:
# Press Ctrl+C
./run.sh
```

#### Problem: "Want to debug scraping logic"
**Solution:**
Add print statements or logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# In your code
print(f"Debug: sections found = {len(sections)}")
```

### 10. Production Considerations

#### Problem: "Want to run in production"
**Recommendations:**
1. Remove `--reload` flag from run.sh
2. Use gunicorn with multiple workers:
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```
3. Add rate limiting
4. Implement caching
5. Use process pooling for browsers

#### Problem: "Need to scrape authenticated sites"
**Current Limitation:**
- This MVP doesn't support authentication
- Would need to add cookie/session management
- Or Playwright auth state handling

## Still Having Issues?

### Debugging Steps:
1. Check server logs in terminal
2. Check browser console (F12)
3. Test with curl commands
4. Run the test suite
5. Try a simple test URL first

### Verification Commands:
```bash
# 1. Python version
python3 --version  # Should be 3.10+

# 2. Dependencies installed
pip list | grep -E "fastapi|uvicorn|playwright|httpx|selectolax"

# 3. Server health
curl http://localhost:8000/healthz

# 4. Simple scrape
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Clean Reinstall:
If all else fails:
```bash
# 1. Stop server (Ctrl+C)

# 2. Remove virtual environment
rm -rf venv

# 3. Clean Playwright cache
rm -rf ~/.cache/ms-playwright

# 4. Fresh install
./run.sh
```

## Getting Help

If you're still stuck:
1. Check the error message carefully
2. Search for the specific error online
3. Review the code comments in main.py
4. Check Playwright documentation: playwright.dev
5. Check FastAPI documentation: fastapi.tiangolo.com

## Known Limitations (Not Bugs)

These are expected behaviors:
- JS rendering is slower (10-30s)
- Some sites block automation
- CAPTCHA sites will fail
- Sites requiring login won't work
- Very heavy sites may timeout
- Infinite scroll limited to 3 attempts
- Maximum 3 pagination pages

---

**Remember:** Most issues are environment-related (Python version, dependencies, network). A clean reinstall solves 90% of problems!