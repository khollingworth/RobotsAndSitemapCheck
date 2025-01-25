import pytest
import aiohttp
from bs4 import BeautifulSoup
from website_checker import WebsiteChecker

@pytest.fixture
async def website_checker():
    async with aiohttp.ClientSession() as session:
        checker = WebsiteChecker("https://example.com", session)
        yield checker

@pytest.mark.asyncio
async def test_fetch_robots_txt(website_checker):
    robots_txt = await website_checker.fetch_robots_txt()
    assert robots_txt is not None
    assert isinstance(robots_txt, str)

@pytest.mark.asyncio
async def test_fetch_sitemap(website_checker):
    sitemap_content = await website_checker.fetch_sitemap("https://example.com/sitemap.xml")
    assert sitemap_content is not None
    assert isinstance(sitemap_content, (str, bytes))

@pytest.mark.asyncio
async def test_parse_sitemap_xml():
    sample_sitemap = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/page1</loc>
        </url>
        <url>
            <loc>https://example.com/page2</loc>
        </url>
    </urlset>"""
    
    soup = BeautifulSoup(sample_sitemap, 'xml')
    urls = [url.loc.text for url in soup.find_all('url')]
    assert len(urls) == 2
    assert "https://example.com/page1" in urls
    assert "https://example.com/page2" in urls
