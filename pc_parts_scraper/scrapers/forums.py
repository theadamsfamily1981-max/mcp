"""
Forum Marketplace Scrapers - Where enthusiasts sell gold for pennies!
ServeTheHome, HardForum, TechPowerUp, etc.
"""

import asyncio
from typing import List, Optional, Dict
from datetime import datetime
import re
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper
from utils.models import PCPart


class ServeTheHomeScraper(BaseScraper):
    """ServeTheHome Forums - Enterprise/datacenter hardware paradise!"""

    def __init__(self):
        super().__init__(
            name="ServeTheHome",
            base_url="https://forums.servethehome.com"
        )
        self.marketplace_url = f"{self.base_url}/index.php?forums/marketplace.7/"

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 5) -> List[PCPart]:
        """Scrape STH marketplace for enterprise gear"""
        parts = []

        try:
            for page in range(1, max_pages + 1):
                url = f"{self.marketplace_url}page-{page}" if page > 1 else self.marketplace_url

                response = await self.fetch(url)
                soup = BeautifulSoup(response.text, 'lxml')

                # Find all thread listings
                threads = soup.find_all('div', class_='structItem-title')

                for thread in threads:
                    try:
                        link = thread.find('a')
                        if not link:
                            continue

                        title = link.get_text(strip=True)
                        thread_url = self.base_url + link.get('href', '')

                        # Look for price in title
                        price_match = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', title)
                        price = float(price_match.group(1).replace(',', '')) if price_match else None

                        # Check if "SOLD" or "FS:" (For Sale)
                        if 'SOLD' in title.upper():
                            continue

                        if any(indicator in title.upper() for indicator in ['FS:', 'WTS:', 'FOR SALE']):
                            part = PCPart(
                                title=title,
                                price=price,
                                url=thread_url,
                                source_name=self.name,
                                image_url=None,
                                condition='used',
                                location=None,
                                description=f"Forum post: {title}"
                            )
                            parts.append(part)

                    except Exception as e:
                        self.logger.debug(f"Error parsing thread: {e}")
                        continue

                await asyncio.sleep(2)  # Be respectful to forums

        except Exception as e:
            self.logger.error(f"Error scraping ServeTheHome: {e}")

        return parts


class HardForumScraper(BaseScraper):
    """[H]ardForum Marketplace - Serious hardware traders"""

    def __init__(self):
        super().__init__(
            name="HardForum",
            base_url="https://www.hardocp.com"
        )
        # Note: HardOCP forums may require authentication
        self.marketplace_url = f"{self.base_url}/forum/forums/for-sale-trade.18/"

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 5) -> List[PCPart]:
        """Scrape HardForum marketplace"""
        parts = []

        try:
            for page in range(1, max_pages + 1):
                url = f"{self.marketplace_url}page-{page}" if page > 1 else self.marketplace_url

                response = await self.fetch(url)
                soup = BeautifulSoup(response.text, 'lxml')

                threads = soup.find_all('div', class_='structItem-title')

                for thread in threads:
                    try:
                        link = thread.find('a')
                        if not link:
                            continue

                        title = link.get_text(strip=True)
                        thread_url = link.get('href', '')

                        if not thread_url.startswith('http'):
                            thread_url = self.base_url + thread_url

                        # Extract price from title
                        price_match = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', title)
                        price = float(price_match.group(1).replace(',', '')) if price_match else None

                        if 'SOLD' not in title.upper():
                            part = PCPart(
                                title=title,
                                price=price,
                                url=thread_url,
                                source_name=self.name,
                                condition='used',
                                description=f"HardForum listing: {title}"
                            )
                            parts.append(part)

                    except Exception as e:
                        self.logger.debug(f"Error parsing thread: {e}")
                        continue

                await asyncio.sleep(2)

        except Exception as e:
            self.logger.error(f"Error scraping HardForum: {e}")

        return parts


class RedditHardwareSwapScraper(BaseScraper):
    """Reddit r/hardwareswap - Underpriced enthusiast sales"""

    def __init__(self):
        super().__init__(
            name="RedditHardwareSwap",
            base_url="https://old.reddit.com"
        )
        self.subreddit_url = f"{self.base_url}/r/hardwareswap/new"

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 3) -> List[PCPart]:
        """Scrape r/hardwareswap for deals"""
        parts = []

        try:
            # Use old.reddit.com for easier scraping
            url = self.subreddit_url

            response = await self.fetch(url, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; PCPartsScraper/1.0)'
            })
            soup = BeautifulSoup(response.text, 'lxml')

            posts = soup.find_all('div', class_='thing')

            for post in posts[:50]:  # First 50 posts
                try:
                    title_elem = post.find('a', class_='title')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    post_url = title_elem.get('href', '')

                    # Only "[USA-XX] [H] Item [W] $$$" format
                    if not title.startswith('[USA-'):
                        continue

                    # Extract price from title
                    price_match = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', title)
                    price = float(price_match.group(1).replace(',', '')) if price_match else None

                    # Extract location
                    location_match = re.search(r'\[USA-([A-Z]{2})\]', title)
                    location = f"USA-{location_match.group(1)}" if location_match else "USA"

                    # Skip if marked as closed/sold
                    if any(marker in title.upper() for marker in ['CLOSED', 'SOLD']):
                        continue

                    # Look for [H] (have) items
                    if '[H]' in title.upper():
                        part = PCPart(
                            title=title,
                            price=price,
                            url=post_url,
                            source_name=self.name,
                            condition='used',
                            location=location,
                            description=f"Reddit post: {title}"
                        )
                        parts.append(part)

                except Exception as e:
                    self.logger.debug(f"Error parsing Reddit post: {e}")
                    continue

            await asyncio.sleep(2)

        except Exception as e:
            self.logger.error(f"Error scraping Reddit: {e}")

        return parts


class TechPowerUpScraper(BaseScraper):
    """TechPowerUp Forums Marketplace"""

    def __init__(self):
        super().__init__(
            name="TechPowerUp",
            base_url="https://www.techpowerup.com"
        )
        self.marketplace_url = f"{self.base_url}/forums/forums/marketplace.57/"

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 3) -> List[PCPart]:
        """Scrape TPU marketplace"""
        parts = []

        try:
            for page in range(1, max_pages + 1):
                url = f"{self.marketplace_url}page-{page}" if page > 1 else self.marketplace_url

                response = await self.fetch(url)
                soup = BeautifulSoup(response.text, 'lxml')

                threads = soup.find_all('div', class_='structItem-title')

                for thread in threads:
                    try:
                        link = thread.find('a')
                        if not link:
                            continue

                        title = link.get_text(strip=True)
                        thread_url = link.get('href', '')

                        if not thread_url.startswith('http'):
                            thread_url = self.base_url + thread_url

                        price_match = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', title)
                        price = float(price_match.group(1).replace(',', '')) if price_match else None

                        if 'SOLD' not in title.upper() and any(tag in title.upper() for tag in ['WTS', 'FS', 'FOR SALE']):
                            part = PCPart(
                                title=title,
                                price=price,
                                url=thread_url,
                                source_name=self.name,
                                condition='used',
                                description=f"TPU listing: {title}"
                            )
                            parts.append(part)

                    except Exception as e:
                        self.logger.debug(f"Error parsing thread: {e}")
                        continue

                await asyncio.sleep(2)

        except Exception as e:
            self.logger.error(f"Error scraping TechPowerUp: {e}")

        return parts
