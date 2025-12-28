# System Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                            │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │           Frontend (Embedded HTML/CSS/JS)                 │ │
│  │                                                           │ │
│  │  • URL Input                                              │ │
│  │  • Scrape Button                                          │ │
│  │  • Loading Indicator                                      │ │
│  │  • Results Display (Sections)                             │ │
│  │  • JSON Download                                          │ │
│  └───────────────────────────────────────────────────────────┘ │
│                           │  │                                  │
└───────────────────────────┼──┼──────────────────────────────────┘
                            │  │
                    HTTP    │  │ HTTP POST /scrape
                    GET /   │  │ (JSON: {url: "..."})
                            ↓  ↓
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend Server                        │
│                    (localhost:8000)                              │
│                                                                  │
│  ┌────────────────┐    ┌────────────────┐    ┌───────────────┐ │
│  │ GET /healthz   │    │  GET /         │    │ POST /scrape  │ │
│  │                │    │                │    │               │ │
│  │ Health Check   │    │ Serve Frontend │    │ Scrape Engine │ │
│  └────────────────┘    └────────────────┘    └───────┬───────┘ │
│                                                       │         │
│                                                       ↓         │
│                                            ┌──────────────────┐ │
│                                            │ ScraperEngine    │ │
│                                            │                  │ │
│                                            │ • URL Validation │ │
│                                            │ • Strategy       │ │
│                                            │   Selection      │ │
│                                            │ • Orchestration  │ │
│                                            └─────────┬────────┘ │
│                                                      │          │
│                                     ┌────────────────┴─────┐    │
│                                     │                      │    │
│                                     ↓                      ↓    │
│                          ┌──────────────────┐  ┌────────────────┐
│                          │ Static Scraping  │  │ JS Rendering   │
│                          │                  │  │                │
│                          │ • httpx          │  │ • Playwright   │
│                          │ • selectolax     │  │ • Chromium     │
│                          │ • Fast           │  │ • Slower       │
│                          └────────┬─────────┘  └───────┬────────┘
│                                   │                    │         │
│                                   └──────────┬─────────┘         │
│                                              │                   │
│                                              ↓                   │
│                                   ┌────────────────────┐         │
│                                   │ HTML Parser        │         │
│                                   │                    │         │
│                                   │ • Section Extract  │         │
│                                   │ • Content Parse    │         │
│                                   │ • Meta Extract     │         │
│                                   │ • Link Convert     │         │
│                                   └─────────┬──────────┘         │
│                                             │                    │
│                                             ↓                    │
│                                   ┌────────────────────┐         │
│                                   │ Interactions       │         │
│                                   │                    │         │
│                                   │ • Click Tabs       │         │
│                                   │ • Load More        │         │
│                                   │ • Scroll/Paginate  │         │
│                                   │ • Track Actions    │         │
│                                   └─────────┬──────────┘         │
│                                             │                    │
│                                             ↓                    │
│                                   ┌────────────────────┐         │
│                                   │ JSON Builder       │         │
│                                   │                    │         │
│                                   │ • Format Response  │         │
│                                   │ • Add Metadata     │         │
│                                   │ • Include Errors   │         │
│                                   └─────────┬──────────┘         │
│                                             │                    │
└─────────────────────────────────────────────┼────────────────────┘
                                              │
                                              ↓
                                    ┌──────────────────┐
                                    │  JSON Response   │
                                    │                  │
                                    │ • url            │
                                    │ • scrapedAt      │
                                    │ • meta           │
                                    │ • sections[]     │
                                    │ • interactions   │
                                    │ • errors[]       │
                                    └──────────────────┘
```

## Component Details

### 1. Frontend Layer

**Technology:** Vanilla JavaScript, HTML5, CSS3

**Responsibilities:**
- User interface rendering
- URL input collection
- API communication
- Results display
- JSON download

**Key Features:**
- Responsive design
- Loading states
- Error handling
- Accordion sections
- JSON viewer

### 2. API Layer

**Technology:** FastAPI (Python)

**Endpoints:**
```
GET  /           → Serve frontend HTML
GET  /healthz    → Health check
POST /scrape     → Scrape URL
```

**Responsibilities:**
- Request validation
- Routing
- Response formatting
- Error handling

### 3. Scraper Engine

**Core Class:** `ScraperEngine`

**Workflow:**
```
1. Receive URL
   ↓
2. Validate URL (http/https only)
   ↓
3. Try Static Scraping (httpx)
   ↓
4. Evaluate Result (heuristics)
   ↓
5. If insufficient → Use Playwright
   ↓
6. Parse HTML (selectolax)
   ↓
7. Perform Interactions (clicks, scrolls)
   ↓
8. Extract Sections
   ↓
9. Build JSON Response
   ↓
10. Return Result
```

### 4. Static Scraping Module

**Technology:** httpx + selectolax

**Process:**
```python
async def _fetch_static(url):
    1. HTTP GET request
    2. Receive HTML
    3. Parse with selectolax
    4. Return HTML string
```

**Advantages:**
- Fast (2-5 seconds)
- Low resource usage
- No browser needed

**Limitations:**
- No JavaScript execution
- No dynamic content
- No interactions

### 5. JS Rendering Module

**Technology:** Playwright (Chromium)

**Process:**
```python
async def _fetch_with_playwright(url):
    1. Launch browser
    2. Create page context
    3. Navigate to URL
    4. Wait for network idle
    5. Remove noise (modals, banners)
    6. Perform clicks (tabs, buttons)
    7. Perform scrolls/pagination
    8. Extract final HTML
    9. Close browser
    10. Return HTML string
```

**Advantages:**
- Full JavaScript support
- Dynamic content
- User interactions
- Complete rendering

**Limitations:**
- Slower (10-30 seconds)
- Higher resource usage
- Requires browser binary

### 6. HTML Parser

**Technology:** selectolax (fast HTML parser)

**Extraction Pipeline:**

```
HTML String
    ↓
┌───────────────────┐
│ Extract Meta      │ → title, description, language, canonical
├───────────────────┤
│ Find Sections     │ → <header>, <nav>, <main>, <section>, <footer>
├───────────────────┤
│ Parse Content     │ → headings, text, links, images, lists, tables
├───────────────────┤
│ Determine Type    │ → hero, nav, section, footer, pricing, faq, etc.
├───────────────────┤
│ Generate Label    │ → From headings or first 5-7 words
├───────────────────┤
│ Truncate HTML     │ → Limit to 1000 chars
└───────────────────┘
    ↓
Section Objects[]
```

### 7. Interaction Handler

**Click Strategy:**
```
1. Search for tabs: [role="tab"], button[aria-controls]
   → Click up to 3 tabs
   
2. Search for load more: button:has-text("Load more")
   → Click up to 3 times
   
3. Record all clicks in interactions.clicks[]
```

**Scroll/Pagination Strategy:**
```
1. Try pagination first:
   a. Find "next" links
   b. Click and navigate
   c. Record URL in interactions.pages[]
   d. Repeat up to depth 3
   
2. If pagination fails, infinite scroll:
   a. Scroll to bottom
   b. Wait for content load
   c. Increment interactions.scrolls
   d. Repeat 3 times
```

### 8. Noise Filter

**Removed Elements:**
- Cookie consent banners
- Modal overlays
- Popup dialogs
- Newsletter signups
- Generic banners

**Method:** CSS selector matching + DOM removal

### 9. Error Handling

**Strategy:** Graceful degradation

```
Try Operation
   ↓
   └─→ Success → Continue
   └─→ Failure → Log error
                 ↓
          Add to errors[]
                 ↓
          Return partial data
```

**Error Structure:**
```json
{
  "message": "Timeout waiting for element",
  "phase": "render"
}
```

## Data Flow

### Successful Scrape Flow

```
User enters URL
      ↓
Frontend POST to /scrape
      ↓
Backend validates URL
      ↓
ScraperEngine initialized
      ↓
Static scrape attempted (httpx)
      ↓
HTML parsed (selectolax)
      ↓
Content evaluated (heuristics)
      ↓
   Sufficient?
      ├─ Yes → Extract sections
      │           ↓
      │        Build response
      │           ↓
      │        Return JSON
      │
      └─ No → Playwright fallback
                  ↓
              Launch browser
                  ↓
              Navigate & wait
                  ↓
              Remove noise
                  ↓
              Perform interactions
                  ↓
              Extract HTML
                  ↓
              Parse sections
                  ↓
              Build response
                  ↓
              Return JSON
                  ↓
Frontend displays results
      ↓
User views/downloads
```

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | HTML/CSS/JS | User interface |
| Backend | FastAPI | API server |
| HTTP Client | httpx | Static requests |
| HTML Parser | selectolax | Fast parsing |
| JS Renderer | Playwright | Dynamic content |
| Browser | Chromium | Page rendering |
| Server | Uvicorn | ASGI server |
| Language | Python 3.10+ | Core logic |

## Performance Characteristics

| Operation | Time | Resources |
|-----------|------|-----------|
| Static scrape | 2-5s | Low CPU, 50MB RAM |
| JS rendering | 10-30s | High CPU, 200MB+ RAM |
| Browser launch | 2-3s | 150MB RAM |
| HTML parsing | <1s | Low CPU |
| API response | <100ms | Minimal |

## Scalability Considerations

**Current MVP:**
- Single-threaded per request
- One browser instance per scrape
- No caching
- No rate limiting

**Production Improvements:**
- Browser context pooling
- Redis caching
- Request queuing
- Rate limiting
- Horizontal scaling
- Load balancing

## Security Considerations

**Current Implementation:**
- URL validation (http/https only)
- Timeout limits
- Error boundaries
- No credential storage

**Production Needs:**
- Rate limiting per IP
- CAPTCHA detection
- Proxy rotation
- Request sanitization
- Output validation

---

This architecture provides a solid foundation for web scraping while maintaining clean separation of concerns and allowing for future enhancements.