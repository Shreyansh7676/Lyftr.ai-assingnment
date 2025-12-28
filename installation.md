# Installation Guide

Complete installation instructions for all operating systems.

## 📋 Prerequisites

- **Python 3.10 or higher**
- **pip** (Python package manager)
- **2GB free disk space** (for Playwright browser)
- **Internet connection** (for package installation)

## 🖥️ Platform-Specific Installation

### macOS

#### 1. Install Python (if not already installed)

**Option A: Using Homebrew (Recommended)**
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.10+
brew install python@3.10
```

**Option B: From Python.org**
- Download from: https://www.python.org/downloads/macos/
- Install the .pkg file
- Follow installer instructions

#### 2. Verify Installation
```bash
python3 --version  # Should show 3.10 or higher
pip3 --version     # Should show pip version
```

#### 3. Run the Scraper
```bash
# Clone/download the project
cd universal-website-scraper

# Run the setup script
chmod +x run.sh
./run.sh
```

**Potential macOS Issues:**

**Issue: "xcrun: error: invalid active developer path"**
```bash
# Install Xcode Command Line Tools
xcode-select --install
```

**Issue: "SSL: CERTIFICATE_VERIFY_FAILED"**
```bash
# Fix SSL certificates
cd /Applications/Python\ 3.10/
./Install\ Certificates.command
```

---

### Linux (Ubuntu/Debian)

#### 1. Install Python 3.10+

**Ubuntu 22.04+ (Python 3.10 included)**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**Ubuntu 20.04 (Need to add repository)**
```bash
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev
```

#### 2. Install Build Dependencies
```bash
# Required for selectolax compilation
sudo apt install build-essential python3-dev

# Required for Playwright browser
sudo apt install libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libpango-1.0-0 libasound2
```

#### 3. Verify Installation
```bash
python3 --version  # Should show 3.10+
pip3 --version     # Should show pip version
```

#### 4. Run the Scraper
```bash
cd universal-website-scraper
chmod +x run.sh
./run.sh
```

**Potential Linux Issues:**

**Issue: "python3.10: command not found"**
```bash
# Use python3.10 explicitly
alias python3=python3.10
```

**Issue: Playwright browser dependencies missing**
```bash
# Install all playwright dependencies
source venv/bin/activate
playwright install-deps chromium
```

---

### Windows

#### 1. Install Python

**Download and Install:**
1. Go to: https://www.python.org/downloads/windows/
2. Download Python 3.10+ installer (64-bit recommended)
3. **IMPORTANT:** Check "Add Python to PATH" during installation
4. Click "Install Now"

#### 2. Verify Installation

Open **Command Prompt** or **PowerShell**:
```powershell
python --version   # Should show 3.10+
pip --version      # Should show pip version
```

#### 3. Install Visual C++ Build Tools (Required for some packages)

Download and install from:
https://visualstudio.microsoft.com/visual-cpp-build-tools/

Or:
```powershell
# Using chocolatey (if installed)
choco install visualstudio2019buildtools
```

#### 4. Run the Scraper

**Option A: Using Git Bash (Recommended)**
```bash
cd universal-website-scraper
chmod +x run.sh
./run.sh
```

**Option B: Using PowerShell**
```powershell
cd universal-website-scraper

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Start server
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Option C: Using Command Prompt**
```cmd
cd universal-website-scraper

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Start server
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Potential Windows Issues:**

**Issue: "Python not found"**
- Ensure "Add to PATH" was checked during installation
- Manually add Python to PATH: Control Panel → System → Advanced → Environment Variables

**Issue: "Access is denied" when installing**
```powershell
# Run as Administrator
# Right-click Command Prompt/PowerShell → "Run as Administrator"
```

**Issue: "SSL: CERTIFICATE_VERIFY_FAILED"**
```powershell
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

---

## 🔧 Manual Installation (All Platforms)

If `run.sh` doesn't work, follow these steps manually:

### 1. Create Virtual Environment
```bash
python3 -m venv venv
```

### 2. Activate Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

### 3. Upgrade pip
```bash
pip install --upgrade pip
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Install Playwright Browsers
```bash
playwright install chromium
```

### 6. Start Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 7. Verify
Open browser to: http://localhost:8000

---

## 🐳 Docker Installation (Optional)

If you prefer Docker:

### 1. Create Dockerfile
```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Build and Run
```bash
# Build image
docker build -t web-scraper .

# Run container
docker run -p 8000:8000 web-scraper
```

---

## ✅ Verification Steps

After installation, verify everything works:

### 1. Check Server Health
```bash
curl http://localhost:8000/healthz
```

Expected output:
```json
{
  "status": "ok"
}
```

### 2. Test Scraping
```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

Should return JSON with sections.

### 3. Test Frontend
Open browser to: http://localhost:8000

Should see the scraper interface.

### 4. Run Test Suite
```bash
python test_scraper.py
```

All tests should pass.

---

## 🚨 Common Issues Across All Platforms

### Issue: Port 8000 Already in Use

**Solution:**
```bash
# Find process using port 8000
# macOS/Linux:
lsof -ti:8000 | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or change the port:
uvicorn main:app --host 0.0.0.0 --port 8001
```

### Issue: Module Not Found

**Solution:**
```bash
# Ensure virtual environment is activated
# Then reinstall:
pip install -r requirements.txt
```

### Issue: Playwright Installation Fails

**Solution:**
```bash
# Try manual installation
source venv/bin/activate  # or activate on Windows
playwright install chromium

# If still failing, install dependencies:
playwright install-deps chromium
```

### Issue: Slow Scraping

**Causes:**
- First run downloads browser (~150MB)
- Slow internet connection
- Heavy websites

**Solution:**
- Wait for first download to complete
- Subsequent runs will be faster

---

## 📦 Requirements

Here's what gets installed:

```
fastapi==0.104.1      # Web framework
uvicorn==0.24.0       # ASGI server
pydantic==2.5.0       # Data validation
httpx==0.25.1         # HTTP client
selectolax==0.3.17    # HTML parser
playwright==1.40.0    # Browser automation
```

Total installation size: ~200-250MB

---

## 🆘 Getting Help

If you still have issues:

1. Check **TROUBLESHOOTING.md** for specific errors
2. Verify Python version: `python3 --version`
3. Check pip version: `pip3 --version`
4. Try clean reinstall:
   ```bash
   rm -rf venv
   ./run.sh
   ```

---

## ✨ Next Steps

After successful installation:

1. Read **QUICKSTART.md** for usage
2. Check **README.md** for full documentation
3. Review **design_notes.md** for implementation details
4. Run **test_scraper.py** to verify everything works

Happy scraping! 🕷️