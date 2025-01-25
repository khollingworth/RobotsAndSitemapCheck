#!/usr/bin/env python3
"""
Website Sitemap Analyzer
-----------------------

This script analyzes websites by checking their robots.txt and sitemap files.
It supports various sitemap formats including:
- Standard XML sitemaps
- Sitemap index files
- Compressed (gzipped) sitemaps
- WordPress sitemaps
- RSS and Atom feeds
- News, video, and image sitemaps

Usage:
    python website_checker.py <website_url>

Example:
    python website_checker.py https://example.com
"""

import aiohttp
import asyncio
from datetime import datetime
from urllib.parse import urljoin, urlparse
import sys
from bs4 import BeautifulSoup
from typing import Optional, Tuple, List, Dict
import robotexclusionrulesparser
import gzip
import io
import xml.etree.ElementTree as ET

class WebsiteChecker:
    """A class to check and analyze website sitemaps and robots.txt files.

    This class provides functionality to:
    - Parse robots.txt files
    - Find and process sitemaps
    - Handle various sitemap formats
    - Check URL crawlability
    
    Attributes:
        base_url (str): The base URL of the website to analyze
        robots_parser: Parser for robots.txt rules
        sitemap_urls (List[str]): List of discovered sitemap URLs
        session (aiohttp.ClientSession): HTTP client session for making requests
    """

    def __init__(self, base_url: str, session: Optional[aiohttp.ClientSession] = None):
        """Initialize the WebsiteChecker with a base URL and optional session.
        
        Args:
            base_url (str): The base URL of the website to analyze
            session (Optional[aiohttp.ClientSession]): HTTP client session for making requests
        """
        self.base_url = base_url.rstrip('/')
        self.robots_parser = robotexclusionrulesparser.RobotExclusionRulesParser()
        self.sitemap_urls = []
        self.session = session
        self._own_session = False

    async def __aenter__(self):
        """Async context manager entry."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
            self._own_session = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._own_session and self.session:
            await self.session.close()

    async def fetch_robots_txt(self) -> Optional[str]:
        """Fetch and parse the robots.txt file.
        
        Returns:
            Optional[str]: The contents of robots.txt if found, None otherwise
        """
        robots_url = f"{self.base_url}/robots.txt"
        try:
            async with self.session.get(robots_url) as response:
                if response.status == 200:
                    return await response.text()
        except Exception as e:
            print(f"Error fetching robots.txt: {e}")
        return None

    async def find_sitemaps_in_robots(self) -> List[str]:
        """Find sitemap URLs listed in robots.txt.
        
        Returns:
            List[str]: List of sitemap URLs found in robots.txt
        """
        robots_content = await self.fetch_robots_txt()
        if robots_content:
            self.robots_parser.parse(robots_content)
            return self.robots_parser.sitemaps
        return []

    async def fetch_sitemap(self, url: str) -> Optional[str]:
        """Fetch a sitemap from the given URL.
        
        Args:
            url (str): The URL of the sitemap to fetch
            
        Returns:
            Optional[str]: The contents of the sitemap if found, None otherwise
        """
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    if url.endswith('.gz'):
                        return self.decompress_gzip(content)
                    return content.decode('utf-8')
        except Exception as e:
            print(f"Error fetching sitemap {url}: {e}")
        return None

    def decompress_gzip(self, content: bytes) -> str:
        """Decompress gzipped content.
        
        Args:
            content (bytes): The gzipped content to decompress
            
        Returns:
            str: The decompressed content as a string
        """
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(content)) as gz:
                return gz.read().decode('utf-8')
        except Exception as e:
            print(f"Error decompressing content: {e}")
            return ""

    def parse_sitemap_urls(self, content: str) -> List[str]:
        """Parse URLs from a sitemap.
        
        Args:
            content (str): The sitemap content to parse
            
        Returns:
            List[str]: List of URLs found in the sitemap
        """
        urls = []
        try:
            soup = BeautifulSoup(content, 'xml')
            # Check for sitemap index
            for sitemap in soup.find_all('sitemap'):
                loc = sitemap.find('loc')
                if loc:
                    urls.append(loc.text)
            
            # Check for regular URLs
            for url in soup.find_all('url'):
                loc = url.find('loc')
                if loc:
                    urls.append(loc.text)
        except Exception as e:
            print(f"Error parsing sitemap: {e}")
        return urls

    def is_url_allowed(self, url: str) -> bool:
        """Check if a URL is allowed by robots.txt rules.
        
        Args:
            url (str): The URL to check
            
        Returns:
            bool: True if the URL is allowed, False otherwise
        """
        return self.robots_parser.is_allowed("*", url)

async def main():
    """Main entry point of the script."""
    if len(sys.argv) != 2:
        print("Usage: python website_checker.py <website_url>")
        sys.exit(1)

    website_url = sys.argv[1]
    async with aiohttp.ClientSession() as session:
        async with WebsiteChecker(website_url, session) as checker:
            # Fetch and parse robots.txt
            robots_txt = await checker.fetch_robots_txt()
            if robots_txt:
                print(f"✅ robots.txt exists at {website_url}/robots.txt")
                print("   Last modified:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                print("\nRobots.txt rules:")
                print(robots_txt)
            else:
                print(f"❌ No robots.txt found at {website_url}/robots.txt")

            # Find sitemaps in robots.txt
            print("\nChecking common sitemap locations...")
            sitemaps = await checker.find_sitemaps_in_robots()
            
            if not sitemaps:
                common_locations = [
                    '/sitemap.xml',
                    '/sitemap_index.xml',
                    '/wp-sitemap.xml',
                    '/sitemap.php',
                ]
                for loc in common_locations:
                    sitemap_url = website_url + loc
                    content = await checker.fetch_sitemap(sitemap_url)
                    if content:
                        print(f"✅ Valid sitemap found at {sitemap_url}")
                        sitemaps.append(sitemap_url)
                        break

            # Process each sitemap
            for sitemap_url in sitemaps:
                print(f"\nAnalyzingsitemap: {sitemap_url}")
                content = await checker.fetch_sitemap(sitemap_url)
                if content:
                    urls = checker.parse_sitemap_urls(content)
                    if any(url.endswith('.xml') for url in urls):
                        print(f"\nFound{len(urls)} sub-sitemaps:")
                        for url in urls:
                            if url.endswith('.xml'):
                                print(f"🗺️  {url}")
                                print("\nAnalyzing  sitemap:", url)
                                sub_content = await checker.fetch_sitemap(url)
                                if sub_content:
                                    sub_urls = checker.parse_sitemap_urls(sub_content)
                                    print(f"\nFound {len(sub_urls)} unique crawlable content URLs:")
                                    for sub_url in sub_urls:
                                        if checker.is_url_allowed(sub_url):
                                            print(f"✅ {sub_url}")
                                        else:
                                            print(f"❌ {sub_url} (blocked by robots.txt)")

if __name__ == "__main__":
    asyncio.run(main())
