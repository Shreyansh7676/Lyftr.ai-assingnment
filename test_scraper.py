"""
Test script for the Universal Website Scraper
Run this after starting the server to verify functionality
"""
import httpx
import json
import asyncio
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Test URLs covering different scenarios
TEST_URLS = {
    "static": "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "js_heavy": "https://vercel.com/",
    "pagination": "https://news.ycombinator.com/"
}

async def test_health_check():
    """Test the health check endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/healthz")
            data = response.json()
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert "status" in data, "Missing 'status' field"
            assert data["status"] == "ok", f"Expected 'ok', got {data['status']}"
            
            print("✅ Health check passed")
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

async def test_scrape_url(url_type: str, url: str):
    """Test scraping a specific URL"""
    print("\n" + "="*60)
    print(f"TEST: Scraping {url_type.upper()} - {url}")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            start_time = datetime.now()
            
            response = await client.post(
                f"{BASE_URL}/scrape",
                json={"url": url}
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            result = data["result"]
            
            # Validate required fields
            assert "url" in result, "Missing 'url' field"
            assert result["url"] == url, f"URL mismatch: {result['url']} != {url}"
            
            assert "scrapedAt" in result, "Missing 'scrapedAt' field"
            assert "meta" in result, "Missing 'meta' field"
            assert "sections" in result, "Missing 'sections' field"
            assert "interactions" in result, "Missing 'interactions' field"
            assert "errors" in result, "Missing 'errors' field"
            
            # Validate meta
            meta = result["meta"]
            assert "title" in meta, "Missing meta.title"
            assert "description" in meta, "Missing meta.description"
            assert "language" in meta, "Missing meta.language"
            assert "canonical" in meta, "Missing meta.canonical"
            
            # Validate sections
            sections = result["sections"]
            assert len(sections) > 0, "sections array is empty"
            
            for i, section in enumerate(sections):
                assert "id" in section, f"Section {i} missing 'id'"
                assert "type" in section, f"Section {i} missing 'type'"
                assert "label" in section, f"Section {i} missing 'label'"
                assert "sourceUrl" in section, f"Section {i} missing 'sourceUrl'"
                assert "content" in section, f"Section {i} missing 'content'"
                assert "rawHtml" in section, f"Section {i} missing 'rawHtml'"
                assert "truncated" in section, f"Section {i} missing 'truncated'"
                
                content = section["content"]
                assert "headings" in content, f"Section {i} content missing 'headings'"
                assert "text" in content, f"Section {i} content missing 'text'"
                assert "links" in content, f"Section {i} content missing 'links'"
                assert "images" in content, f"Section {i} content missing 'images'"
                assert "lists" in content, f"Section {i} content missing 'lists'"
                assert "tables" in content, f"Section {i} content missing 'tables'"
            
            # Validate interactions
            interactions = result["interactions"]
            assert "clicks" in interactions, "Missing interactions.clicks"
            assert "scrolls" in interactions, "Missing interactions.scrolls"
            assert "pages" in interactions, "Missing interactions.pages"
            
            # Print summary
            print(f"✅ Scrape successful in {elapsed:.2f}s")
            print(f"\nSummary:")
            print(f"  Title: {meta['title'][:60]}{'...' if len(meta['title']) > 60 else ''}")
            print(f"  Sections: {len(sections)}")
            print(f"  Interactions:")
            print(f"    - Clicks: {len(interactions['clicks'])}")
            print(f"    - Scrolls: {interactions['scrolls']}")
            print(f"    - Pages: {len(interactions['pages'])}")
            print(f"  Errors: {len(result['errors'])}")
            
            # Print first section details
            if sections:
                first = sections[0]
                print(f"\nFirst Section:")
                print(f"  Type: {first['type']}")
                print(f"  Label: {first['label']}")
                print(f"  Text length: {len(first['content']['text'])} chars")
                print(f"  Links: {len(first['content']['links'])}")
                print(f"  Images: {len(first['content']['images'])}")
            
            # Print errors if any
            if result['errors']:
                print(f"\n⚠️  Errors encountered:")
                for error in result['errors']:
                    print(f"  - [{error['phase']}] {error['message']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Scrape failed: {e}")
        return False

async def test_invalid_url():
    """Test error handling with invalid URL"""
    print("\n" + "="*60)
    print("TEST: Invalid URL")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/scrape",
                json={"url": "not-a-valid-url"}
            )
            
            assert response.status_code == 400, f"Expected 400, got {response.status_code}"
            print("✅ Invalid URL properly rejected")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("UNIVERSAL WEBSITE SCRAPER - TEST SUITE")
    print("="*60)
    print(f"Testing server at: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Test 1: Health check
    results.append(await test_health_check())
    
    # Test 2: Invalid URL
    results.append(await test_invalid_url())
    
    # Test 3-5: Different URL types
    for url_type, url in TEST_URLS.items():
        results.append(await test_scrape_url(url_type, url))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(main())