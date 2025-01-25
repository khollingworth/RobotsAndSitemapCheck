import pytest
import aiohttp
import gzip
from bs4 import BeautifulSoup
from website_checker import WebsiteChecker
import pytest_asyncio

@pytest_asyncio.fixture
async def google_checker():
    async with aiohttp.ClientSession() as session:
        yield WebsiteChecker("https://google.com", session)

@pytest.mark.asyncio
async def test_google_robots_txt(google_checker):
    """Test fetching and parsing Google's robots.txt"""
    robots_txt = await google_checker.fetch_robots_txt()
    assert robots_txt is not None
    assert isinstance(robots_txt, str)
    # Check for common Google robots.txt rules
    assert "User-agent: *" in robots_txt
    assert "Disallow: /search" in robots_txt

@pytest.mark.asyncio
async def test_google_sitemap_discovery(google_checker):
    """Test discovering Google's sitemaps from robots.txt"""
    sitemaps = await google_checker.find_sitemaps_in_robots()
    assert sitemaps is not None
    assert isinstance(sitemaps, list)
    assert any("sitemap.xml" in url.lower() for url in sitemaps)

@pytest.mark.asyncio
async def test_google_sitemap_parsing(google_checker):
    """Test parsing Google's sitemap"""
    sitemap_url = "https://www.google.com/sitemap.xml"
    sitemap_content = await google_checker.fetch_sitemap(sitemap_url)
    assert sitemap_content is not None
    
    # Parse the sitemap
    soup = BeautifulSoup(sitemap_content, 'xml')
    sitemaps = soup.find_all('sitemap')
    assert len(sitemaps) > 0
    
    # Check for common Google subsitemaps
    sitemap_locs = [s.loc.text for s in sitemaps]
    assert any("gmail" in url.lower() for url in sitemap_locs)

@pytest.mark.asyncio
async def test_compressed_sitemap_handling(google_checker):
    """Test handling of gzipped sitemaps"""
    # Create a sample gzipped sitemap
    sample_content = """<?xml version="1.0" encoding="UTF-8"?>
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <sitemap>
            <loc>https://www.google.com/gmail/sitemap.xml</loc>
        </sitemap>
    </sitemapindex>"""
    
    compressed = gzip.compress(sample_content.encode('utf-8'))
    decompressed = google_checker.decompress_gzip(compressed)
    assert isinstance(decompressed, str)
    assert "gmail/sitemap.xml" in decompressed

@pytest.mark.asyncio
async def test_url_allowed_by_robots(google_checker):
    """Test URL permission checking against robots.txt"""
    # First fetch and parse robots.txt
    robots_txt = await google_checker.fetch_robots_txt()
    assert robots_txt is not None
    google_checker.robots_parser.parse(robots_txt)
    
    # These URLs should be allowed
    assert google_checker.is_url_allowed("https://www.google.com/about")
    assert google_checker.is_url_allowed("https://www.google.com/")
    
    # These URLs should be blocked
    assert not google_checker.is_url_allowed("https://www.google.com/search?q=test")
    assert not google_checker.is_url_allowed("https://www.google.com/sdch")

@pytest.mark.asyncio
async def test_sitemap_index_handling(google_checker):
    """Test handling of sitemap index files"""
    sample_index = """<?xml version="1.0" encoding="UTF-8"?>
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <sitemap>
            <loc>https://www.google.com/gmail/sitemap.xml</loc>
            <lastmod>2025-01-25</lastmod>
        </sitemap>
    </sitemapindex>"""
    
    urls = google_checker.parse_sitemap_urls(sample_index)
    assert isinstance(urls, list)
    assert "https://www.google.com/gmail/sitemap.xml" in urls

@pytest.mark.asyncio
async def test_invalid_sitemap_handling(google_checker):
    """Test handling of invalid sitemap content"""
    invalid_content = "Not a valid XML"
    urls = google_checker.parse_sitemap_urls(invalid_content)
    assert urls == []

@pytest.mark.asyncio
async def test_connection_error_handling(google_checker):
    """Test handling of connection errors"""
    invalid_url = "https://invalid.example.com/sitemap.xml"
    content = await google_checker.fetch_sitemap(invalid_url)
    assert content is None
