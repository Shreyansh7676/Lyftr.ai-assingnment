"""
Universal Website Scraper - FastAPI Backend
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl, validator
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import httpx
from selectolax.parser import HTMLParser
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import asyncio
from urllib.parse import urljoin, urlparse
import re
import os

app = FastAPI()

# Serve static files for frontend
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


class ScrapeRequest(BaseModel):
    url: str

    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class LinkItem(BaseModel):
    text: str
    href: str


class ImageItem(BaseModel):
    src: str
    alt: str


class SectionContent(BaseModel):
    headings: List[str]
    text: str
    links: List[LinkItem]
    images: List[ImageItem]
    lists: List[List[str]]
    tables: List[Any]


class Section(BaseModel):
    id: str
    type: str
    label: str
    sourceUrl: str
    content: SectionContent
    rawHtml: str
    truncated: bool


class Meta(BaseModel):
    title: str
    description: str
    language: str
    canonical: Optional[str]


class Interactions(BaseModel):
    clicks: List[str]
    scrolls: int
    pages: List[str]


class Error(BaseModel):
    message: str
    phase: str


class ScrapeResult(BaseModel):
    url: str
    scrapedAt: str
    meta: Meta
    sections: List[Section]
    interactions: Interactions
    errors: List[Error]


class ScrapeResponse(BaseModel):
    result: ScrapeResult


class ScraperEngine:
    """Main scraper engine handling both static and JS rendering"""
    
    def __init__(self, url: str):
        self.url = url
        self.visited_pages = [url]
        self.clicks_performed = []
        self.scroll_count = 0
        self.errors = []
        self.strategy = "static"  # or "js"
        
    async def scrape(self) -> ScrapeResult:
        """Main scraping method with fallback strategy"""
        try:
            # Try static scraping first
            html_content = await self._fetch_static()
            parser = HTMLParser(html_content)
            
            # Check if JS rendering is needed
            if self._needs_js_rendering(parser):
                self.strategy = "js"
                self.errors.append(Error(
                    message="Static content insufficient, using JS rendering",
                    phase="detection"
                ))
                html_content = await self._fetch_with_playwright()
                parser = HTMLParser(html_content)
            
            # Extract metadata
            meta = self._extract_meta(parser)
            
            # Extract sections
            sections = self._extract_sections(parser, self.url)
            
            # Build result
            result = ScrapeResult(
                url=self.url,
                scrapedAt=datetime.now(timezone.utc).isoformat(),
                meta=meta,
                sections=sections,
                interactions=Interactions(
                    clicks=self.clicks_performed,
                    scrolls=self.scroll_count,
                    pages=self.visited_pages
                ),
                errors=self.errors
            )
            
            return result
            
        except Exception as e:
            self.errors.append(Error(
                message=str(e),
                phase="scrape"
            ))
            # Return partial data
            return ScrapeResult(
                url=self.url,
                scrapedAt=datetime.now(timezone.utc).isoformat(),
                meta=Meta(title="", description="", language="en", canonical=None),
                sections=[],
                interactions=Interactions(
                    clicks=self.clicks_performed,
                    scrolls=self.scroll_count,
                    pages=self.visited_pages
                ),
                errors=self.errors
            )
    
    async def _fetch_static(self) -> str:
        """Fetch HTML using httpx"""
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(self.url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                return response.text
        except Exception as e:
            self.errors.append(Error(message=str(e), phase="fetch"))
            raise
    
    def _needs_js_rendering(self, parser: HTMLParser) -> bool:
        """Heuristic to determine if JS rendering is needed"""
        body = parser.css_first('body')
        if not body:
            return True
        
        text_content = body.text(strip=True)
        
        # Check if content is too short
        if len(text_content) < 200:
            return True
        
        # Check for common JS framework indicators
        indicators = [
            'id="root"',
            'id="__next"',
            'id="app"',
            'data-reactroot',
            'ng-app'
        ]
        html_str = parser.html
        if any(ind in html_str for ind in indicators):
            # Check if these containers are empty
            for selector in ['#root', '#__next', '#app']:
                elem = parser.css_first(selector)
                if elem and len(elem.text(strip=True)) < 100:
                    return True
        
        return False
    
    async def _fetch_with_playwright(self) -> str:
        """Fetch and render using Playwright with interactions"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            try:
                # Navigate to URL
                await page.goto(self.url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(2000)  # Additional wait
                
                # Remove noise (cookie banners, modals, etc.)
                await self._remove_noise(page)
                
                # Perform click interactions
                await self._perform_clicks(page)
                
                # Perform scroll/pagination
                await self._perform_scroll_pagination(page)
                
                # Get final HTML
                html_content = await page.content()
                
                await browser.close()
                return html_content
                
            except PlaywrightTimeout as e:
                self.errors.append(Error(
                    message=f"Timeout: {str(e)}",
                    phase="render"
                ))
                html_content = await page.content()
                await browser.close()
                return html_content
            except Exception as e:
                self.errors.append(Error(
                    message=str(e),
                    phase="render"
                ))
                await browser.close()
                raise
    
    async def _remove_noise(self, page):
        """Remove common noise elements"""
        noise_selectors = [
            '[id*="cookie"]',
            '[class*="cookie"]',
            '[id*="banner"]',
            '[class*="banner"]',
            '[id*="modal"]',
            '[class*="modal"]',
            '[id*="popup"]',
            '[class*="popup"]',
            '[role="dialog"]',
            '.newsletter-popup',
            '#onetrust-banner-sdk'
        ]
        
        for selector in noise_selectors:
            try:
                await page.evaluate(f'''
                    document.querySelectorAll("{selector}").forEach(el => el.remove());
                ''')
            except:
                pass
    
    async def _perform_clicks(self, page):
        """Perform click interactions (tabs, load more buttons)"""
        # Try clicking tabs
        tab_selectors = [
            '[role="tab"]',
            'button[aria-controls]',
            '.tab',
            '[data-tab]'
        ]
        
        for selector in tab_selectors:
            try:
                tabs = await page.query_selector_all(selector)
                if tabs and len(tabs) > 1:
                    # Click first few tabs
                    for i, tab in enumerate(tabs[:3]):
                        try:
                            await tab.click(timeout=2000)
                            await page.wait_for_timeout(1000)
                            self.clicks_performed.append(f"{selector}[{i}]")
                        except:
                            pass
                    break
            except:
                pass
        
        # Try clicking "Load more" buttons
        load_more_selectors = [
            'button:has-text("Load more")',
            'button:has-text("Show more")',
            'button:has-text("See more")',
            '[class*="load-more"]',
            '[class*="show-more"]'
        ]
        
        for selector in load_more_selectors:
            try:
                for attempt in range(3):
                    button = await page.query_selector(selector)
                    if button:
                        await button.click(timeout=2000)
                        await page.wait_for_timeout(1500)
                        self.clicks_performed.append(f"{selector}")
                    else:
                        break
            except:
                pass
    
    async def _perform_scroll_pagination(self, page):
        """Perform scrolling and pagination to depth >= 3"""
        current_url = page.url
        
        # Try pagination links first
        pagination_attempted = False
        for depth in range(3):
            next_selectors = [
                'a:has-text("Next")',
                'a:has-text("next")',
                '[rel="next"]',
                '.pagination a:last-child',
                'a[aria-label*="next" i]'
            ]
            
            for selector in next_selectors:
                try:
                    next_link = await page.query_selector(selector)
                    if next_link:
                        await next_link.click(timeout=3000)
                        await page.wait_for_load_state('networkidle', timeout=5000)
                        new_url = page.url
                        if new_url != current_url and new_url not in self.visited_pages:
                            self.visited_pages.append(new_url)
                            current_url = new_url
                            pagination_attempted = True
                            await page.wait_for_timeout(1000)
                        break
                except:
                    continue
            
            if not pagination_attempted:
                break
        
        # If no pagination, try infinite scroll
        if not pagination_attempted or len(self.visited_pages) < 3:
            for i in range(3):
                try:
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await page.wait_for_timeout(2000)
                    self.scroll_count += 1
                except:
                    pass
    
    def _extract_meta(self, parser: HTMLParser) -> Meta:
        """Extract metadata from HTML"""
        title = ""
        title_elem = parser.css_first('title')
        if title_elem:
            title = title_elem.text(strip=True)
        else:
            og_title = parser.css_first('meta[property="og:title"]')
            if og_title:
                title = og_title.attributes.get('content', '')
        
        description = ""
        desc_elem = parser.css_first('meta[name="description"]')
        if desc_elem:
            description = desc_elem.attributes.get('content', '')
        else:
            og_desc = parser.css_first('meta[property="og:description"]')
            if og_desc:
                description = og_desc.attributes.get('content', '')
        
        language = "en"
        html_elem = parser.css_first('html')
        if html_elem:
            language = html_elem.attributes.get('lang', 'en')
        
        canonical = None
        canon_elem = parser.css_first('link[rel="canonical"]')
        if canon_elem:
            canonical = canon_elem.attributes.get('href', '')
        
        return Meta(
            title=title,
            description=description,
            language=language,
            canonical=canonical
        )
    
    def _extract_sections(self, parser: HTMLParser, source_url: str) -> List[Section]:
        """Extract sections from HTML"""
        sections = []
        section_id = 0
        
        # Try to find semantic sections
        semantic_selectors = ['header', 'nav', 'main', 'section', 'article', 'aside', 'footer']
        
        for selector in semantic_selectors:
            elements = parser.css(selector)
            for elem in elements:
                section = self._parse_section(elem, section_id, selector, source_url)
                if section and section.content.text.strip():
                    sections.append(section)
                    section_id += 1
        
        # If no semantic sections found, try divs with substantial content
        if not sections:
            divs = parser.css('body > div')
            for elem in divs[:10]:  # Limit to first 10 divs
                section = self._parse_section(elem, section_id, 'section', source_url)
                if section and len(section.content.text) > 50:
                    sections.append(section)
                    section_id += 1
        
        # Ensure at least one section exists
        if not sections:
            body = parser.css_first('body')
            if body:
                section = self._parse_section(body, 0, 'section', source_url)
                if section:
                    sections.append(section)
        
        return sections if sections else [self._create_empty_section(source_url)]
    
    def _parse_section(self, elem, section_id: int, tag_name: str, source_url: str) -> Optional[Section]:
        """Parse a single section element"""
        # Extract headings
        headings = []
        for h in elem.css('h1, h2, h3, h4, h5, h6'):
            heading_text = h.text(strip=True)
            if heading_text:
                headings.append(heading_text)
        
        # Extract text
        text = elem.text(strip=True)
        
        # Extract links
        links = []
        for a in elem.css('a'):
            link_text = a.text(strip=True)
            href = a.attributes.get('href', '')
            if href:
                absolute_href = urljoin(source_url, href)
                links.append(LinkItem(text=link_text, href=absolute_href))
        
        # Extract images
        images = []
        for img in elem.css('img'):
            src = img.attributes.get('src', '') or img.attributes.get('data-src', '')
            alt = img.attributes.get('alt', '')
            if src:
                absolute_src = urljoin(source_url, src)
                images.append(ImageItem(src=absolute_src, alt=alt))
        
        # Extract lists
        lists = []
        for ul in elem.css('ul, ol'):
            list_items = [li.text(strip=True) for li in ul.css('li')]
            if list_items:
                lists.append(list_items)
        
        # Extract tables (simplified)
        tables = []
        for table in elem.css('table'):
            table_data = []
            for row in table.css('tr'):
                row_data = [cell.text(strip=True) for cell in row.css('td, th')]
                if row_data:
                    table_data.append(row_data)
            if table_data:
                tables.append(table_data)
        
        # Determine section type
        section_type = self._determine_section_type(tag_name, headings, text)
        
        # Generate label
        label = self._generate_label(headings, text, section_type)
        
        # Get raw HTML (truncated)
        raw_html = elem.html
        truncated = False
        if len(raw_html) > 1000:
            raw_html = raw_html[:1000] + '...'
            truncated = True
        
        return Section(
            id=f"{section_type}-{section_id}",
            type=section_type,
            label=label,
            sourceUrl=source_url,
            content=SectionContent(
                headings=headings,
                text=text,
                links=links,
                images=images,
                lists=lists,
                tables=tables
            ),
            rawHtml=raw_html,
            truncated=truncated
        )
    
    def _determine_section_type(self, tag_name: str, headings: List[str], text: str) -> str:
        """Determine section type based on content"""
        tag_map = {
            'header': 'hero',
            'nav': 'nav',
            'footer': 'footer'
        }
        
        if tag_name in tag_map:
            return tag_map[tag_name]
        
        # Check content for type hints
        text_lower = text.lower()
        if any(word in text_lower for word in ['pricing', 'price', '$', 'plan']):
            return 'pricing'
        if any(word in text_lower for word in ['faq', 'question', 'answer']):
            return 'faq'
        if 'grid' in text_lower or 'gallery' in text_lower:
            return 'grid'
        
        return 'section'
    
    def _generate_label(self, headings: List[str], text: str, section_type: str) -> str:
        """Generate a label for the section"""
        if headings:
            return headings[0]
        
        # Use first 5-7 words of text
        words = text.split()[:7]
        if words:
            label = ' '.join(words)
            if len(text.split()) > 7:
                label += '...'
            return label
        
        return section_type.title()
    
    def _create_empty_section(self, source_url: str) -> Section:
        """Create an empty fallback section"""
        return Section(
            id="section-0",
            type="unknown",
            label="Content",
            sourceUrl=source_url,
            content=SectionContent(
                headings=[],
                text="",
                links=[],
                images=[],
                lists=[],
                tables=[]
            ),
            rawHtml="",
            truncated=False
        )


@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_url(request: ScrapeRequest):
    """Scrape a URL and return structured data"""
    try:
        scraper = ScraperEngine(request.url)
        result = await scraper.scrape()
        return ScrapeResponse(result=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend HTML"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Universal Website Scraper</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: #f5f5f5;
                padding: 20px;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            .header {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            h1 { color: #333; margin-bottom: 10px; }
            .subtitle { color: #666; margin-bottom: 20px; }
            .input-group {
                display: flex;
                gap: 10px;
                margin-bottom: 15px;
            }
            input[type="text"] {
                flex: 1;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            input[type="text"]:focus {
                outline: none;
                border-color: #007bff;
            }
            button {
                padding: 12px 30px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
            }
            button:hover { background: #0056b3; }
            button:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            .loading {
                text-align: center;
                padding: 40px;
                color: #666;
            }
            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #007bff;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .error {
                background: #fee;
                border: 1px solid #fcc;
                color: #c33;
                padding: 15px;
                border-radius: 4px;
                margin: 20px 0;
            }
            .results {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .meta-info {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 4px;
                margin-bottom: 20px;
            }
            .meta-info p {
                margin: 5px 0;
                color: #666;
            }
            .meta-info strong { color: #333; }
            .sections { margin-top: 20px; }
            .section {
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-bottom: 10px;
                overflow: hidden;
            }
            .section-header {
                background: #f8f9fa;
                padding: 15px;
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .section-header:hover { background: #e9ecef; }
            .section-title {
                font-weight: 600;
                color: #333;
            }
            .section-type {
                background: #007bff;
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 12px;
            }
            .section-content {
                padding: 20px;
                display: none;
                border-top: 1px solid #ddd;
            }
            .section.expanded .section-content {
                display: block;
            }
            .section.expanded .section-header {
                background: #e9ecef;
            }
            pre {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 4px;
                overflow-x: auto;
                font-size: 12px;
                line-height: 1.5;
            }
            .actions {
                margin: 20px 0;
                display: flex;
                gap: 10px;
            }
            .btn-secondary {
                background: #6c757d;
            }
            .btn-secondary:hover {
                background: #545b62;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌐 Universal Website Scraper</h1>
                <p class="subtitle">Enter a URL to scrape and analyze its content</p>
                
                <div class="input-group">
                    <input 
                        type="text" 
                        id="urlInput" 
                        placeholder="https://example.com"
                        value="https://en.wikipedia.org/wiki/Artificial_intelligence"
                    />
                    <button id="scrapeBtn" onclick="scrapeUrl()">Scrape</button>
                </div>
                
                <div style="font-size: 12px; color: #666;">
                    Try: 
                    <a href="#" onclick="setUrl('https://en.wikipedia.org/wiki/Artificial_intelligence'); return false;">Wikipedia</a> | 
                    <a href="#" onclick="setUrl('https://news.ycombinator.com/'); return false;">Hacker News</a> | 
                    <a href="#" onclick="setUrl('https://vercel.com/'); return false;">Vercel</a>
                </div>
            </div>
            
            <div id="loading" class="loading" style="display: none;">
                <div class="spinner"></div>
                <p>Scraping in progress... This may take a moment.</p>
            </div>
            
            <div id="error" class="error" style="display: none;"></div>
            
            <div id="results" class="results" style="display: none;">
                <div class="actions">
                    <button onclick="downloadJSON()">📥 Download JSON</button>
                    <button class="btn-secondary" onclick="viewRawJSON()">👁️ View Raw JSON</button>
                </div>
                
                <div id="metaInfo" class="meta-info"></div>
                
                <h2>Sections</h2>
                <div id="sections" class="sections"></div>
            </div>
        </div>
        
        <script>
            let currentResult = null;
            
            function setUrl(url) {
                document.getElementById('urlInput').value = url;
            }
            
            async function scrapeUrl() {
                const url = document.getElementById('urlInput').value.trim();
                if (!url) {
                    alert('Please enter a URL');
                    return;
                }
                
                // Hide previous results
                document.getElementById('results').style.display = 'none';
                document.getElementById('error').style.display = 'none';
                document.getElementById('loading').style.display = 'block';
                document.getElementById('scrapeBtn').disabled = true;
                
                try {
                    const response = await fetch('/scrape', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url })
                    });
                    
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.detail || 'Scraping failed');
                    }
                    
                    const data = await response.json();
                    currentResult = data.result;
                    displayResults(data.result);
                    
                } catch (error) {
                    document.getElementById('error').textContent = 'Error: ' + error.message;
                    document.getElementById('error').style.display = 'block';
                } finally {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('scrapeBtn').disabled = false;
                }
            }
            
            function displayResults(result) {
                // Display meta info
                const metaHtml = `
                    <p><strong>URL:</strong> ${result.url}</p>
                    <p><strong>Scraped At:</strong> ${new Date(result.scrapedAt).toLocaleString()}</p>
                    <p><strong>Title:</strong> ${result.meta.title || 'N/A'}</p>
                    <p><strong>Language:</strong> ${result.meta.language}</p>
                    <p><strong>Sections Found:</strong> ${result.sections.length}</p>
                    <p><strong>Interactions:</strong> ${result.interactions.clicks.length} clicks, ${result.interactions.scrolls} scrolls, ${result.interactions.pages.length} pages</p>
                    ${result.errors.length > 0 ? `<p><strong>Errors:</strong> ${result.errors.length}</p>` : ''}
                `;
                document.getElementById('metaInfo').innerHTML = metaHtml;
                
                // Display sections
                const sectionsHtml = result.sections.map((section, idx) => `
                    <div class="section" id="section-${idx}">
                        <div class="section-header" onclick="toggleSection(${idx})">
                            <span class="section-title">${section.label}</span>
                            <span class="section-type">${section.type}</span>
                        </div>
                        <div class="section-content">
                            <h4>Content</h4>
                            <p><strong>Headings:</strong> ${section.content.headings.length > 0 ? section.content.headings.join(', ') : 'None'}</p>
                            <p><strong>Text:</strong> ${section.content.text.substring(0, 300)}${section.content.text.length > 300 ? '...' : ''}</p>
                            <p><strong>Links:</strong> ${section.content.links.length}</p>
                            <p><strong>Images:</strong> ${section.content.images.length}</p>
                            <p><strong>Lists:</strong> ${section.content.lists.length}</p>
                            <p><strong>Tables:</strong> ${section.content.tables.length}</p>
                            <br>
                            <details>
                                <summary style="cursor: pointer; font-weight: 600; margin-bottom: 10px;">View Full JSON</summary>
                                <pre>${JSON.stringify(section, null, 2)}</pre>
                            </details>
                        </div>
                    </div>
                `).join('');
                document.getElementById('sections').innerHTML = sectionsHtml;
                
                // Show results
                document.getElementById('results').style.display = 'block';
            }
            
            function toggleSection(idx) {
                const section = document.getElementById(`section-${idx}`);
                section.classList.toggle('expanded');
            }
            
            function downloadJSON() {
                if (!currentResult) return;
                
                const dataStr = JSON.stringify({ result: currentResult }, null, 2);
                const blob = new Blob([dataStr], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `scrape-${Date.now()}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }
            
            function viewRawJSON() {
                if (!currentResult) return;
                
                const jsonWindow = window.open('', '_blank');
                jsonWindow.document.write('<html><head><title>Raw JSON</title>');
                jsonWindow.document.write('<style>body { font-family: monospace; padding: 20px; background: #f5f5f5; } pre { background: white; padding: 20px; border-radius: 4px; overflow-x: auto; }</style>');
                jsonWindow.document.write('</head><body>');
                jsonWindow.document.write('<pre>' + JSON.stringify({ result: currentResult }, null, 2) + '</pre>');
                jsonWindow.document.write('</body></html>');
                jsonWindow.document.close();
            }
            
            // Allow Enter key to submit
            document.getElementById('urlInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    scrapeUrl();
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)   