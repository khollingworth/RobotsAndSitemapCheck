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
    """

    def __init__(self, base_url: str):
        """Initialize the WebsiteChecker with a base URL.

        Args:
            base_url (str): The website's base URL to analyze
        """
        self.base_url = base_url if base_url.endswith('/') else base_url + '/'
        self.robots_parser = robotexclusionrulesparser.RobotExclusionRulesParser()
        self.sitemap_urls: List[str] = []
        
    def is_valid_robots_txt(self, content: str) -> bool:
        """Check if content appears to be a valid robots.txt file.

        Args:
            content (str): The content to check

        Returns:
            bool: True if content appears to be a valid robots.txt file
        """
        content_lower = content.strip().lower()
        return not content_lower.startswith('<!doctype') and \
               ('user-agent:' in content_lower or 'disallow:' in content_lower or 'allow:' in content_lower or 'crawl-delay:' in content_lower)
    
    def is_valid_sitemap(self, content: str) -> bool:
        """Check if content appears to be a valid sitemap file.

        Supports multiple sitemap formats including XML, RSS, and Atom.

        Args:
            content (str): The content to check

        Returns:
            bool: True if content appears to be a valid sitemap
        """
        content_lower = content.strip().lower()
        return not content_lower.startswith('<!doctype html') and \
               any(marker in content_lower for marker in [
                   '<urlset', '<sitemapindex', 
                   '<rss', '<feed',  # RSS and Atom formats
                   '<news:', '<image:', '<video:'  # Special sitemap extensions
               ])

    async def fetch_url(self, session: aiohttp.ClientSession, url: str) -> Tuple[str, Optional[str], Optional[datetime]]:
        """Fetch content from a URL with support for compressed content.

        Args:
            session (aiohttp.ClientSession): The session to use for the request
            url (str): The URL to fetch

        Returns:
            Tuple[str, Optional[str], Optional[datetime]]: URL, content (if successful), and last modified date
        """
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    last_modified = response.headers.get('Last-Modified')
                    last_modified_date = None
                    if last_modified:
                        try:
                            last_modified_date = datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')
                        except ValueError:
                            pass

                    # Handle gzipped content
                    if response.headers.get('Content-Type') == 'application/x-gzip' or url.endswith('.gz'):
                        compressed_data = await response.read()
                        try:
                            with gzip.GzipFile(fileobj=io.BytesIO(compressed_data)) as gz:
                                content = gz.read().decode('utf-8')
                        except Exception as e:
                            print(f"Error decompressing gzipped content from {url}: {str(e)}")
                            return url, None, None
                    else:
                        content = await response.text()
                    return url, content, last_modified_date
                return url, None, None
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return url, None, None

    def parse_sitemap(self, content: str) -> List[str]:
        """Parse a sitemap file and extract all URLs.

        Supports multiple sitemap formats and provides fallback parsing methods.

        Args:
            content (str): The sitemap content to parse

        Returns:
            List[str]: List of URLs found in the sitemap
        """
        if not self.is_valid_sitemap(content):
            print("Warning: Content doesn't appear to be a valid sitemap")
            return []
            
        urls = []
        try:
            # Try parsing with BeautifulSoup first
            soup = BeautifulSoup(content, 'xml')
            
            # Handle regular sitemaps
            for url in soup.find_all('loc'):
                urls.append(url.text.strip())
                
            # Handle RSS feeds
            for item in soup.find_all('item'):
                link = item.find('link')
                if link and link.string:
                    urls.append(link.string.strip())

            # Handle Atom feeds
            for entry in soup.find_all('entry'):
                link = entry.find('link', href=True)
                if link:
                    urls.append(link['href'].strip())

            # Handle special sitemap extensions
            for special_url in soup.find_all(['image:loc', 'video:content_loc', 'news:loc']):
                urls.append(special_url.text.strip())

        except Exception as e:
            print(f"BeautifulSoup parsing failed, trying ElementTree: {str(e)}")
            try:
                # Fallback to ElementTree for simpler XML parsing
                root = ET.fromstring(content)
                # Extract URLs from any element with 'loc' in the tag name
                for elem in root.iter():
                    if 'loc' in elem.tag.lower():
                        urls.append(elem.text.strip())
            except Exception as e:
                print(f"Error parsing sitemap with ElementTree: {str(e)}")
                return []
                
        return list(dict.fromkeys(urls))  # Remove duplicates while preserving order

    def extract_sitemap_from_robots(self, content: str) -> List[str]:
        """Extract sitemap URLs from robots.txt content.

        Args:
            content (str): The robots.txt content

        Returns:
            List[str]: List of sitemap URLs found in robots.txt
        """
        sitemaps = []
        for line in content.splitlines():
            if line.lower().startswith('sitemap:'):
                sitemap_url = line.split(':', 1)[1].strip()
                sitemaps.append(sitemap_url)
        return sitemaps

    def is_url_allowed(self, url: str) -> bool:
        """Check if a URL is allowed to be crawled according to robots.txt rules.

        Args:
            url (str): The URL to check

        Returns:
            bool: True if the URL is allowed to be crawled
        """
        return self.robots_parser.is_allowed("*", url)

    async def process_sitemap(self, session: aiohttp.ClientSession, content: str, url: str, depth: int = 0):
        """Process a sitemap file and its sub-sitemaps recursively.

        Args:
            session (aiohttp.ClientSession): The session to use for requests
            content (str): The sitemap content to process
            url (str): The URL of the sitemap
            depth (int, optional): Current recursion depth. Defaults to 0.
        """
        if depth > 5:  # Prevent infinite recursion
            print(f"Warning: Maximum sitemap depth reached at {url}")
            return

        print(f"\nAnalyzing{'  ' * depth}sitemap: {url}")
        urls = self.parse_sitemap(content)
        
        if not urls:
            print("No URLs found in sitemap")
            return
            
        # Separate sitemap URLs from content URLs
        sitemap_urls = []
        content_urls = []
        
        for url in urls:
            if any(url.endswith(ext) for ext in ['.xml', '.xml.gz']) or 'sitemap' in url.lower():
                sitemap_urls.append(url)
            else:
                content_urls.append(url)
        
        # Process sub-sitemaps first
        if sitemap_urls:
            print(f"\nFound{' ' * depth}{len(sitemap_urls)} sub-sitemaps:")
            for sitemap_url in sitemap_urls:
                print(f"🗺️  {sitemap_url}")
                url, sub_content, date = await self.fetch_url(session, sitemap_url)
                if sub_content and self.is_valid_sitemap(sub_content):
                    await self.process_sitemap(session, sub_content, url, depth + 1)
        
        # Process content URLs
        if content_urls:
            crawlable_urls = []
            uncrawlable_urls = []
            
            for url in content_urls:
                if self.is_url_allowed(url):
                    crawlable_urls.append(url)
                else:
                    uncrawlable_urls.append(url)
            
            if crawlable_urls:
                print(f"\nFound{' ' * depth}{len(crawlable_urls)} unique crawlable content URLs:")
                for url in crawlable_urls:
                    print(f"✅ {url}")
            
            if uncrawlable_urls:
                print(f"\nFound{' ' * depth}{len(uncrawlable_urls)} URLs blocked by robots.txt:")
                for url in uncrawlable_urls:
                    print(f"❌ {url}")

    async def check_website(self):
        """Main method to check a website's robots.txt and sitemaps.

        This method:
        1. Checks for robots.txt
        2. Extracts sitemaps from robots.txt
        3. Checks common sitemap locations
        4. Processes all found sitemaps
        """
        robots_url = urljoin(self.base_url, 'robots.txt')
        common_sitemap_paths = [
            'sitemap.xml',
            'sitemap_index.xml',
            'sitemap-index.xml',
            'sitemap/sitemap.xml',
            'sitemapindex.xml',
            'sitemap.xml.gz',  # Common compressed formats
            'sitemap_index.xml.gz',
            'sitemap-index.xml.gz',
            'news-sitemap.xml',  # Special sitemaps
            'video-sitemap.xml',
            'image-sitemap.xml'
        ]
        
        async with aiohttp.ClientSession() as session:
            # First check robots.txt
            robots_url, robots_content, robots_date = await self.fetch_url(session, robots_url)
            
            sitemap_from_robots = []
            if robots_content:
                if not self.is_valid_robots_txt(robots_content):
                    print(f"❌ Invalid robots.txt found at {robots_url} (appears to be HTML or other content)")
                else:
                    print(f"✅ robots.txt exists at {robots_url}")
                    if robots_date:
                        print(f"   Last modified: {robots_date}")
                    else:
                        print("   Last modified date not available")
                    self.robots_parser.parse(robots_content)
                    
                    print("\nRobots.txt rules:")
                    print(robots_content.strip())
                    
                    # Extract sitemap URLs from robots.txt
                    sitemap_from_robots = self.extract_sitemap_from_robots(robots_content)
                    if sitemap_from_robots:
                        print("\nSitemaps found in robots.txt:")
                        for sitemap in sitemap_from_robots:
                            print(f"🔍 {sitemap}")
            else:
                print(f"❌ robots.txt not found at {robots_url}")
            
            # Try sitemaps from robots.txt first
            sitemap_found = False
            if sitemap_from_robots:
                for sitemap_url in sitemap_from_robots:
                    url, content, date = await self.fetch_url(session, sitemap_url)
                    if content and self.is_valid_sitemap(content):
                        sitemap_found = True
                        print(f"\n✅ Valid sitemap found at {url}")
                        if date:
                            print(f"   Last modified: {date}")
                        await self.process_sitemap(session, content, url)
                        break
            
            # If no sitemap found in robots.txt, try common locations
            if not sitemap_found:
                print("\nChecking common sitemap locations...")
                for path in common_sitemap_paths:
                    sitemap_url = urljoin(self.base_url, path)
                    url, content, date = await self.fetch_url(session, sitemap_url)
                    if content and self.is_valid_sitemap(content):
                        sitemap_found = True
                        print(f"✅ Valid sitemap found at {url}")
                        if date:
                            print(f"   Last modified: {date}")
                        await self.process_sitemap(session, content, url)
                        break
                
                if not sitemap_found:
                    print("❌ No valid sitemap found in any common location")

def main():
    """Entry point of the script."""
    if len(sys.argv) != 2:
        print("Usage: python website_checker.py <website_url>")
        sys.exit(1)

    website_url = sys.argv[1]
    checker = WebsiteChecker(website_url)
    asyncio.run(checker.check_website())

if __name__ == "__main__":
    main()
