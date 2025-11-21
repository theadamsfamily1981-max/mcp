"""
University Surplus Store Scrapers - Research lab cleanouts!
MIT, Stanford, Berkeley, etc. - Premium equipment for pennies
"""

import asyncio
from typing import List, Optional
import re
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper
from utils.models import PCPart


class MITSurplusScraper(BaseScraper):
    """MIT Surplus - Research grade equipment"""

    def __init__(self):
        super().__init__(
            name="MIT_Surplus",
            base_url="https://property.mit.edu"
        )
        self.surplus_url = f"{self.base_url}/surplus-sales"

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 5) -> List[PCPart]:
        """Scrape MIT surplus store"""
        parts = []

        try:
            response = await self.fetch(self.surplus_url)
            soup = BeautifulSoup(response.text, 'lxml')

            # Find electronics/computer items
            items = soup.find_all('div', class_='surplus-item')  # Adjust selector based on actual HTML

            for item in items:
                try:
                    title_elem = item.find('h3') or item.find('h4')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)

                    # Look for price
                    price_elem = item.find(string=re.compile(r'\$\d+'))
                    price = None
                    if price_elem:
                        price_match = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', price_elem)
                        price = float(price_match.group(1).replace(',', '')) if price_match else None

                    desc_elem = item.find('p') or item.find('div', class_='description')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    part = PCPart(
                        title=f"MIT Surplus: {title}",
                        price=price,
                        url=self.surplus_url,
                        source_name=self.name,
                        condition='used',
                        location='Cambridge, MA',
                        description=description
                    )
                    parts.append(part)

                except Exception as e:
                    self.logger.debug(f"Error parsing MIT item: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error scraping MIT Surplus: {e}")

        return parts


class StanfordSurplusScraper(BaseScraper):
    """Stanford Surplus - Silicon Valley research equipment"""

    def __init__(self):
        super().__init__(
            name="Stanford_Surplus",
            base_url="https://sustainable.stanford.edu"
        )
        self.surplus_url = f"{self.base_url}/services/cardinal-reuse"

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 5) -> List[PCPart]:
        """Scrape Stanford surplus"""
        parts = []

        try:
            response = await self.fetch(self.surplus_url)
            soup = BeautifulSoup(response.text, 'lxml')

            # Generic item extraction
            items = soup.find_all('div', class_=['item', 'product', 'listing'])

            for item in items:
                try:
                    title = item.find(['h2', 'h3', 'h4', 'a'])
                    if not title:
                        continue

                    title_text = title.get_text(strip=True)

                    # Only include if keywords match or electronics-related
                    if any(kw in title_text.lower() for kw in [
                        'computer', 'server', 'fpga', 'board', 'card',
                        'gpu', 'cpu', 'memory', 'oscilloscope', 'test'
                    ]):
                        part = PCPart(
                            title=f"Stanford: {title_text}",
                            price=None,  # Often contact for price
                            url=self.surplus_url,
                            source_name=self.name,
                            condition='used',
                            location='Stanford, CA',
                            description=f"University surplus: {title_text}"
                        )
                        parts.append(part)

                except Exception as e:
                    self.logger.debug(f"Error parsing Stanford item: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error scraping Stanford Surplus: {e}")

        return parts


class UCBerkeleySurplusScraper(BaseScraper):
    """UC Berkeley Surplus - Bay Area research gear"""

    def __init__(self):
        super().__init__(
            name="Berkeley_Surplus",
            base_url="https://ucberkeleysurplus.com"
        )

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 5) -> List[PCPart]:
        """Scrape Berkeley surplus"""
        parts = []

        try:
            response = await self.fetch(self.base_url)
            soup = BeautifulSoup(response.text, 'lxml')

            # Look for electronics category
            items = soup.find_all(['div', 'li'], class_=re.compile(r'item|product'))

            for item in items:
                try:
                    title = item.find(['h2', 'h3', 'a'])
                    if not title:
                        continue

                    title_text = title.get_text(strip=True)

                    price_text = item.find(string=re.compile(r'\$\d+'))
                    price = None
                    if price_text:
                        price_match = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', price_text)
                        price = float(price_match.group(1).replace(',', '')) if price_match else None

                    part = PCPart(
                        title=f"Berkeley Surplus: {title_text}",
                        price=price,
                        url=self.base_url,
                        source_name=self.name,
                        condition='used',
                        location='Berkeley, CA',
                        description=f"UC Berkeley surplus sale"
                    )
                    parts.append(part)

                except Exception as e:
                    self.logger.debug(f"Error parsing Berkeley item: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error scraping Berkeley Surplus: {e}")

        return parts


class UniversityOfWashingtonSurplusScraper(BaseScraper):
    """UW Surplus - Pacific Northwest research equipment"""

    def __init__(self):
        super().__init__(
            name="UW_Surplus",
            base_url="https://uw.edu/facilities/services/recycling/surplus-sales"
        )

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 5) -> List[PCPart]:
        """Scrape UW surplus store"""
        parts = []

        try:
            response = await self.fetch(self.base_url)
            soup = BeautifulSoup(response.text, 'lxml')

            items = soup.find_all(['div', 'li'], class_=re.compile(r'item|listing'))

            for item in items:
                try:
                    title = item.find(['h2', 'h3', 'h4'])
                    if not title:
                        continue

                    title_text = title.get_text(strip=True)

                    part = PCPart(
                        title=f"UW Surplus: {title_text}",
                        price=None,
                        url=self.base_url,
                        source_name=self.name,
                        condition='used',
                        location='Seattle, WA',
                        description="University of Washington surplus"
                    )
                    parts.append(part)

                except Exception as e:
                    self.logger.debug(f"Error parsing UW item: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error scraping UW Surplus: {e}")

        return parts
