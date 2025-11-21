"""
Pawn Shops, E-Waste Recyclers, and Salvage Yards
Where people dump tech without knowing its value!
"""

import asyncio
from typing import List, Optional
import re
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper
from utils.models import PCPart


class PawnGuruScraper(BaseScraper):
    """PawnGuru - Pawn shop aggregator, people pawning tech they don't understand"""

    def __init__(self):
        super().__init__(
            name="PawnGuru",
            base_url="https://www.pawnguru.com"
        )

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 5) -> List[PCPart]:
        """Scrape pawn shop listings"""
        parts = []

        search_terms = keywords or ['computer', 'graphics card', 'server', 'fpga', 'electronics']

        try:
            for term in search_terms[:3]:
                search_url = f"{self.base_url}/search?q={term}"

                response = await self.fetch(search_url)
                soup = BeautifulSoup(response.text, 'lxml')

                items = soup.find_all('div', class_=re.compile(r'listing|item'))

                for item in items[:15]:
                    try:
                        title_elem = item.find(['h2', 'h3', 'h4'])
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)

                        link = item.find('a', href=True)
                        item_url = link.get('href', '') if link else ''
                        if item_url and not item_url.startswith('http'):
                            item_url = self.base_url + item_url

                        price_elem = item.find(string=re.compile(r'\$'))
                        price = None
                        if price_elem:
                            price_match = re.search(r'\$\s*([\d,]+\.?\d*)', price_elem)
                            if price_match:
                                price = float(price_match.group(1).replace(',', ''))

                        # Get location
                        location_elem = item.find(class_=re.compile(r'location'))
                        location = location_elem.get_text(strip=True) if location_elem else None

                        part = PCPart(
                            title=f"Pawn: {title}",
                            price=price,
                            url=item_url or search_url,
                            source_name=self.name,
                            condition='used',
                            location=location,
                            description="Pawn shop listing"
                        )
                        parts.append(part)

                    except Exception as e:
                        self.logger.debug(f"Error parsing PawnGuru item: {e}")
                        continue

                await asyncio.sleep(2)

        except Exception as e:
            self.logger.error(f"Error scraping PawnGuru: {e}")

        return parts


class FreeGeekScraper(BaseScraper):
    """FreeGeek - Tech recycler with sales, often has server/enterprise gear"""

    def __init__(self):
        super().__init__(
            name="FreeGeek",
            base_url="https://www.freegeek.org"
        )

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 3) -> List[PCPart]:
        """Scrape FreeGeek store listings"""
        parts = []

        try:
            # FreeGeek has different locations - check Portland store
            url = f"{self.base_url}/shop"

            response = await self.fetch(url)
            soup = BeautifulSoup(response.text, 'lxml')

            items = soup.find_all('div', class_=re.compile(r'product'))

            for item in items:
                try:
                    title_elem = item.find(['h2', 'h3', 'h4'])
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)

                    price_elem = item.find(class_='price')
                    price = None
                    if price_elem:
                        price_match = re.search(r'\$\s*([\d.]+)', price_elem.get_text())
                        if price_match:
                            price = float(price_match.group(1))

                    part = PCPart(
                        title=f"FreeGeek: {title}",
                        price=price,
                        url=url,
                        source_name=self.name,
                        condition='refurbished',
                        location='Portland, OR',
                        description="Tech recycler resale"
                    )
                    parts.append(part)

                except Exception as e:
                    self.logger.debug(f"Error parsing FreeGeek item: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error scraping FreeGeek: {e}")

        return parts


class EWasteBenScraper(BaseScraper):
    """eWaste Ben - E-waste recycler, sometimes sells pulls"""

    def __init__(self):
        super().__init__(
            name="EWaste_Ben",
            base_url="https://www.ewasteben.com"
        )

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 3) -> List[PCPart]:
        """Scrape e-waste sales"""
        parts = []

        try:
            url = f"{self.base_url}/shop"

            response = await self.fetch(url)
            soup = BeautifulSoup(response.text, 'lxml')

            items = soup.find_all('div', class_=re.compile(r'product'))

            for item in items:
                try:
                    title_elem = item.find(['h2', 'h3'])
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)

                    # Only include server/enterprise/interesting stuff
                    if any(kw in title.lower() for kw in [
                        'server', 'workstation', 'enterprise', 'xeon',
                        'gpu', 'graphics', 'card', 'board'
                    ]):
                        price_elem = item.find(class_='price')
                        price = None
                        if price_elem:
                            price_match = re.search(r'\$\s*([\d.]+)', price_elem.get_text())
                            if price_match:
                                price = float(price_match.group(1))

                        part = PCPart(
                            title=f"E-Waste: {title}",
                            price=price,
                            url=url,
                            source_name=self.name,
                            condition='used',
                            description="E-waste recycler pull"
                        )
                        parts.append(part)

                except Exception as e:
                    self.logger.debug(f"Error parsing eWaste item: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error scraping eWaste Ben: {e}")

        return parts


class FacebookMarketplaceScraper(BaseScraper):
    """Facebook Marketplace - Local deals, people don't know what they have!

    Note: Requires authentication, may need Selenium/Playwright
    """

    def __init__(self):
        super().__init__(
            name="Facebook_Marketplace",
            base_url="https://www.facebook.com/marketplace"
        )

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 3) -> List[PCPart]:
        """Scrape Facebook Marketplace (requires auth - placeholder)"""
        parts = []

        # NOTE: Facebook Marketplace requires login and uses heavy JavaScript
        # This is a placeholder - would need Selenium/Playwright in production
        # For now, just log that it requires special handling

        self.logger.warning(
            "Facebook Marketplace scraping requires authentication and Selenium/Playwright. "
            "Consider using manual searches or browser automation for best results."
        )

        try:
            # Would need to:
            # 1. Use Playwright with logged-in session
            # 2. Search for keywords in local area
            # 3. Extract listings with prices
            # 4. Filter for electronics/computer items

            # Placeholder implementation
            search_terms = keywords or ['computer parts', 'server', 'fpga', 'graphics card']

            for term in search_terms[:2]:
                # This would require authenticated session
                search_url = f"{self.base_url}/search?query={term}"

                # Mark as needing manual review
                part = PCPart(
                    title=f"[Manual Search Required] Facebook Marketplace: {term}",
                    price=None,
                    url=search_url,
                    source_name=self.name,
                    condition='varies',
                    description=f"Search Facebook Marketplace manually for: {term}"
                )
                parts.append(part)

        except Exception as e:
            self.logger.error(f"Facebook Marketplace requires manual search: {e}")

        return parts
