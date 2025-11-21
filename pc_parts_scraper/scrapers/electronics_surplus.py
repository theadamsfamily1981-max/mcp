"""
Electronics Surplus Store Scrapers
All Electronics, Electronic Goldmine, BG Micro, etc.
Bulk pulls, overstock, liquidations
"""

import asyncio
from typing import List, Optional
import re
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper
from utils.models import PCPart


class AllElectronicsScraper(BaseScraper):
    """All Electronics - Surplus electronics and parts"""

    def __init__(self):
        super().__init__(
            name="AllElectronics",
            base_url="https://www.allelectronics.com"
        )

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 5) -> List[PCPart]:
        """Scrape All Electronics catalog"""
        parts = []

        try:
            # Check computer/electronics categories
            categories = [
                '/category/9/computer.html',
                '/category/10/test-equipment.html',
                '/category/60/boards-kits.html'
            ]

            for category in categories:
                url = self.base_url + category

                response = await self.fetch(url)
                soup = BeautifulSoup(response.text, 'lxml')

                items = soup.find_all('div', class_=re.compile(r'product'))

                for item in items:
                    try:
                        title_elem = item.find(['h3', 'h4', 'a'], class_=re.compile(r'title|name'))
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)

                        link = item.find('a', href=True)
                        item_url = link.get('href', '') if link else ''
                        if item_url and not item_url.startswith('http'):
                            item_url = self.base_url + item_url

                        price_elem = item.find(class_=re.compile(r'price'))
                        price = None
                        if price_elem:
                            price_match = re.search(r'\$\s*([\d.]+)', price_elem.get_text())
                            if price_match:
                                price = float(price_match.group(1))

                        img_elem = item.find('img')
                        image_url = img_elem.get('src') if img_elem else None

                        part = PCPart(
                            title=title,
                            price=price,
                            url=item_url or url,
                            source_name=self.name,
                            image_url=image_url,
                            condition='new_surplus',
                            description="Electronics surplus"
                        )
                        parts.append(part)

                    except Exception as e:
                        self.logger.debug(f"Error parsing AllElectronics item: {e}")
                        continue

                await asyncio.sleep(2)

        except Exception as e:
            self.logger.error(f"Error scraping AllElectronics: {e}")

        return parts


class ElectronicGoldmineScraper(BaseScraper):
    """Electronic Goldmine - Surplus electronics treasure trove"""

    def __init__(self):
        super().__init__(
            name="ElectronicGoldmine",
            base_url="https://www.goldmine-elec-products.com"
        )

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 5) -> List[PCPart]:
        """Scrape Electronic Goldmine"""
        parts = []

        try:
            # Computer and test equipment sections
            search_url = f"{self.base_url}/collections/all"

            response = await self.fetch(search_url)
            soup = BeautifulSoup(response.text, 'lxml')

            items = soup.find_all('div', class_=re.compile(r'product'))

            for item in items[:50]:
                try:
                    title_elem = item.find(['h3', 'h2', 'a'])
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)

                    # Only include electronics/computer related
                    if any(kw in title.lower() for kw in [
                        'board', 'module', 'card', 'fpga', 'cpu', 'memory',
                        'oscilloscope', 'test', 'analyzer', 'usb', 'interface'
                    ]):
                        link = item.find('a', href=True)
                        item_url = link.get('href', '') if link else ''
                        if item_url and not item_url.startswith('http'):
                            item_url = self.base_url + item_url

                        price_elem = item.find(class_=re.compile(r'price'))
                        price = None
                        if price_elem:
                            price_match = re.search(r'\$\s*([\d.]+)', price_elem.get_text())
                            if price_match:
                                price = float(price_match.group(1))

                        part = PCPart(
                            title=title,
                            price=price,
                            url=item_url or search_url,
                            source_name=self.name,
                            condition='new_surplus',
                            description="Electronic Goldmine surplus"
                        )
                        parts.append(part)

                except Exception as e:
                    self.logger.debug(f"Error parsing Goldmine item: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error scraping Electronic Goldmine: {e}")

        return parts


class BGMicroScraper(BaseScraper):
    """BG Micro - Electronics parts and surplus"""

    def __init__(self):
        super().__init__(
            name="BGMicro",
            base_url="https://www.bgmicro.com"
        )

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 3) -> List[PCPart]:
        """Scrape BG Micro catalog"""
        parts = []

        try:
            # Computer parts category
            url = f"{self.base_url}/catalog/computer-parts-peripherals"

            response = await self.fetch(url)
            soup = BeautifulSoup(response.text, 'lxml')

            items = soup.find_all('div', class_=re.compile(r'product'))

            for item in items:
                try:
                    title_elem = item.find(['h3', 'h4'])
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
                        title=title,
                        price=price,
                        url=url,
                        source_name=self.name,
                        condition='new_surplus',
                        description="BG Micro surplus"
                    )
                    parts.append(part)

                except Exception as e:
                    self.logger.debug(f"Error parsing BGMicro item: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error scraping BG Micro: {e}")

        return parts


class HamRadioOutletScraper(BaseScraper):
    """Ham Radio Outlet - SDR and RF equipment (often FPGA-based)"""

    def __init__(self):
        super().__init__(
            name="HamRadioOutlet",
            base_url="https://www.hamradio.com"
        )

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 3) -> List[PCPart]:
        """Scrape used/clearance ham radio equipment"""
        parts = []

        try:
            # Used equipment and clearance
            url = f"{self.base_url}/used-equipment.html"

            response = await self.fetch(url)
            soup = BeautifulSoup(response.text, 'lxml')

            items = soup.find_all('div', class_=re.compile(r'product'))

            for item in items:
                try:
                    title_elem = item.find(['h2', 'h3'])
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)

                    # Focus on SDR, spectrum analyzers, test equipment
                    if any(kw in title.lower() for kw in ['sdr', 'spectrum', 'analyzer', 'usrp', 'hackrf']):
                        price_elem = item.find(class_='price')
                        price = None
                        if price_elem:
                            price_match = re.search(r'\$\s*([\d,]+\.?\d*)', price_elem.get_text())
                            if price_match:
                                price = float(price_match.group(1).replace(',', ''))

                        part = PCPart(
                            title=title,
                            price=price,
                            url=url,
                            source_name=self.name,
                            condition='used',
                            description="Ham radio equipment (may contain FPGAs)"
                        )
                        parts.append(part)

                except Exception as e:
                    self.logger.debug(f"Error parsing HamRadio item: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error scraping Ham Radio Outlet: {e}")

        return parts
