# Website Sitemap Analyzer

A Python script that analyzes websites by checking their robots.txt and sitemap files. It supports multiple sitemap formats and provides detailed information about crawlable URLs.

## Features

- Analyzes robots.txt files
- Supports multiple sitemap formats:
  - Standard XML sitemaps
  - Sitemap index files
  - Compressed (gzipped) sitemaps
  - WordPress sitemaps
  - RSS and Atom feeds
  - News, video, and image sitemaps
- Recursive processing of sitemap hierarchies
- URL crawlability checking against robots.txt rules
- Asynchronous operation for better performance
- Detailed output with emoji indicators

## Requirements

- Python 3.7+
- Required packages (see requirements.txt):
  - aiohttp
  - beautifulsoup4
  - robotexclusionrulesparser
  - lxml

## Installation

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python website_checker.py <website_url>
```

Example:
```bash
python website_checker.py https://example.com
```

## Output Format

The script provides detailed output with the following indicators:

- ✅ Success indicators (valid sitemaps, crawlable URLs)
- ❌ Error/warning indicators (invalid files, blocked URLs)
- 🔍 Discovery indicators (sitemaps found in robots.txt)
- 🗺️ Sitemap indicators (sub-sitemaps)

## Error Handling

The script includes robust error handling for:
- Invalid or malformed XML
- Compressed content
- Network errors
- Invalid datetime formats
- Malformed robots.txt files

## Code Structure

- `website_checker.py`: Main script file
- `requirements.txt`: Python package dependencies
- `README.md`: Documentation

## Contributing

Feel free to submit issues and enhancement requests!
