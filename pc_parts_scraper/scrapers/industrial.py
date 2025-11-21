"""
Industrial Equipment & Auction Scrapers
Factory liquidations, datacenter closures, test equipment
"""

import asyncio
from typing import List, Optional
import re
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper
from utils.models import PCPart


class BidOnEquipmentScraper(BaseScraper):
    """BidOnEquipment - Factory and lab liquidations"""

    def __init__(self):
        super().__init__(
            name="BidOnEquipment",
            base_url="https://www.bidonequipment.com"
        )

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 5) -> List[PCPart]:
        """Scrape industrial equipment auctions"""
        parts = []

        # Search for test equipment, electronics
        search_terms = keywords or ['oscilloscope', 'spectrum analyzer', 'test equipment', 'computer', 'server']

        try:
            for term in search_terms[:3]:
                search_url = f"{self.base_url}/catalog?search={term}"

                response = await self.fetch(search_url)
                soup = BeautifulSoup(response.text, 'lxml')

                items = soup.find_all('div', class_=re.compile(r'product|item|listing'))

                for item in items[:20]:
                    try:
                        title_elem = item.find(['h2', 'h3', 'h4', 'a'])
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)

                        # Find auction/sale link
                        link_elem = item.find('a', href=True)
                        item_url = link_elem.get('href', '') if link_elem else ''
                        if item_url and not item_url.startswith('http'):
                            item_url = self.base_url + item_url

                        # Look for current bid or price
                        price_elem = item.find(string=re.compile(r'\$\d+|Current Bid'))
                        price = None
                        if price_elem:
                            price_match = re.search(r'\$\s*([\d,]+(?:\.\d{2})?)', str(price_elem))
                            if price_match:
                                price = float(price_match.group(1).replace(',', ''))

                        # Get image
                        img_elem = item.find('img')
                        image_url = img_elem.get('src') if img_elem else None

                        part = PCPart(
                            title=title,
                            price=price,
                            url=item_url or self.base_url,
                            source_name=self.name,
                            image_url=image_url,
                            condition='used',
                            description=f"Industrial equipment auction: {title}"
                        )
                        parts.append(part)

                    except Exception as e:
                        self.logger.debug(f"Error parsing BidOnEquipment item: {e}")
                        continue

                await asyncio.sleep(2)

        except Exception as e:
            self.logger.error(f"Error scraping BidOnEquipment: {e}")

        return parts


class AssetNationScraper(BaseScraper):
    """Asset Nation - Datacenter closures, IT liquidations"""

    def __init__(self):
        super().__init__(
            name="AssetNation",
            base_url="https://www.assetnation.com"
        )

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 5) -> List[PCPart]:
        """Scrape datacenter liquidation auctions"""
        parts = []

        try:
            # Look for IT/computer equipment category
            search_url = f"{self.base_url}/auctions/categories/computers-it-equipment"

            response = await self.fetch(search_url)
            soup = BeautifulSoup(response.text, 'lxml')

            # Find auction listings
            items = soup.find_all('div', class_=re.compile(r'auction-item|lot'))

            for item in items:
                try:
                    title_elem = item.find(['h2', 'h3', 'h4'])
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)

                    # Get auction URL
                    link = item.find('a', href=True)
                    item_url = link.get('href', '') if link else ''
                    if item_url and not item_url.startswith('http'):
                        item_url = self.base_url + item_url

                    # Current bid
                    bid_elem = item.find(string=re.compile(r'Current Bid|Bid'))
                    price = None
                    if bid_elem:
                        price_match = re.search(r'\$\s*([\d,]+)', str(bid_elem))
                        if price_match:
                            price = float(price_match.group(1).replace(',', ''))

                    part = PCPart(
                        title=title,
                        price=price,
                        url=item_url or search_url,
                        source_name=self.name,
                        condition='used',
                        description=f"Asset Nation auction: {title}"
                    )
                    parts.append(part)

                except Exception as e:
                    self.logger.debug(f"Error parsing AssetNation item: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error scraping AssetNation: {e}")

        return parts


class MachineryTraderScraper(BaseScraper):
    """Machinery Trader - Test equipment and electronics"""

    def __init__(self):
        super().__init__(
            name="MachineryTrader",
            base_url="https://www.machinerytrader.com"
        )

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 3) -> List[PCPart]:
        """Scrape test equipment listings"""
        parts = []

        search_terms = keywords or ['oscilloscope', 'spectrum analyzer', 'network analyzer']

        try:
            for term in search_terms:
                search_url = f"{self.base_url}/listings/search?keywords={term}"

                response = await self.fetch(search_url)
                soup = BeautifulSoup(response.text, 'lxml')

                items = soup.find_all('div', class_=re.compile(r'listing'))

                for item in items[:10]:
                    try:
                        title_elem = item.find(['h2', 'h3'])
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)

                        link = item.find('a', href=True)
                        item_url = link.get('href', '') if link else ''

                        price_elem = item.find(string=re.compile(r'\$'))
                        price = None
                        if price_elem:
                            price_match = re.search(r'\$\s*([\d,]+)', price_elem)
                            if price_match:
                                price = float(price_match.group(1).replace(',', ''))

                        part = PCPart(
                            title=title,
                            price=price,
                            url=item_url if item_url.startswith('http') else self.base_url + item_url,
                            source_name=self.name,
                            condition='used',
                            description="Test equipment listing"
                        )
                        parts.append(part)

                    except Exception as e:
                        self.logger.debug(f"Error parsing MachineryTrader item: {e}")
                        continue

                await asyncio.sleep(2)

        except Exception as e:
            self.logger.error(f"Error scraping MachineryTrader: {e}")

        return parts
