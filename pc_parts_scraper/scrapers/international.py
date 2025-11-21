"""
International Marketplace Scrapers - Global junk-picking!
Yahoo Japan, Allegro.pl, Marktplaats, Leboncoin, etc.
Often 50-80% cheaper than US markets!
"""

import asyncio
from typing import List, Optional
import re
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper
from utils.models import PCPart


class YahooAuctionsJapanScraper(BaseScraper):
    """Yahoo Auctions Japan - Industrial surplus heaven!

    Notes: Requires proxy/VPN for access outside Japan
    Many sellers don't ship internationally (use proxy shipping service)
    """

    def __init__(self):
        super().__init__(
            name="YahooJP_Auctions",
            base_url="https://auctions.yahoo.co.jp"
        )

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 5) -> List[PCPart]:
        """Scrape Yahoo Japan auctions"""
        parts = []

        # Search for FPGA, Zynq, server boards
        search_terms = keywords or ['FPGA', 'Zynq', 'Xilinx', 'サーバー', 'ワークステーション']

        try:
            for term in search_terms[:3]:  # Limit searches
                search_url = f"{self.base_url}/search/search?p={term}&tab_ex=commerce"

                response = await self.fetch(search_url, headers={
                    'Accept-Language': 'ja-JP,ja;q=0.9,en;q=0.8'
                })
                soup = BeautifulSoup(response.text, 'lxml')

                # Find auction items
                items = soup.find_all('li', class_=re.compile(r'Product'))

                for item in items[:20]:  # First 20 per search
                    try:
                        title_elem = item.find('a', class_=re.compile(r'Product__title'))
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        item_url = title_elem.get('href', '')

                        # Extract price in yen
                        price_elem = item.find(string=re.compile(r'¥|円'))
                        price_jpy = None
                        if price_elem:
                            price_match = re.search(r'([\d,]+)', price_elem)
                            if price_match:
                                price_jpy = int(price_match.group(1).replace(',', ''))
                                # Convert JPY to USD (approximate: 1 USD = 150 JPY)
                                price = price_jpy / 150.0

                        # Get image
                        img_elem = item.find('img')
                        image_url = img_elem.get('src') if img_elem else None

                        part = PCPart(
                            title=f"[JP] {title}",
                            price=price,
                            url=item_url if item_url.startswith('http') else self.base_url + item_url,
                            source_name=self.name,
                            image_url=image_url,
                            condition='used',
                            location='Japan',
                            description=f"Yahoo JP auction - {price_jpy}¥ (~${price:.0f} USD)" if price else "Yahoo JP auction"
                        )
                        parts.append(part)

                    except Exception as e:
                        self.logger.debug(f"Error parsing Yahoo JP item: {e}")
                        continue

                await asyncio.sleep(3)  # Be respectful

        except Exception as e:
            self.logger.error(f"Error scraping Yahoo Japan: {e}")

        return parts


class AllegroPolandScraper(BaseScraper):
    """Allegro.pl - Polish marketplace with Eastern European pricing"""

    def __init__(self):
        super().__init__(
            name="Allegro_Poland",
            base_url="https://allegro.pl"
        )

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 3) -> List[PCPart]:
        """Scrape Allegro.pl"""
        parts = []

        search_terms = keywords or ['FPGA', 'Xilinx', 'GPU', 'serwer', 'stacja robocza']

        try:
            for term in search_terms[:3]:
                search_url = f"{self.base_url}/listing?string={term}"

                response = await self.fetch(search_url)
                soup = BeautifulSoup(response.text, 'lxml')

                items = soup.find_all('article', {'data-role': 'offer'})

                for item in items[:15]:
                    try:
                        title_elem = item.find('a', class_=re.compile(r'title'))
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        item_url = title_elem.get('href', '')

                        # Extract price in PLN
                        price_elem = item.find(string=re.compile(r'zł'))
                        price = None
                        if price_elem:
                            price_match = re.search(r'([\d\s,]+)', price_elem)
                            if price_match:
                                price_pln = float(price_match.group(1).replace(' ', '').replace(',', '.'))
                                # Convert PLN to USD (approximate: 1 USD = 4 PLN)
                                price = price_pln / 4.0

                        part = PCPart(
                            title=f"[PL] {title}",
                            price=price,
                            url=item_url if item_url.startswith('http') else self.base_url + item_url,
                            source_name=self.name,
                            condition='used',
                            location='Poland',
                            description="Allegro.pl listing"
                        )
                        parts.append(part)

                    except Exception as e:
                        self.logger.debug(f"Error parsing Allegro item: {e}")
                        continue

                await asyncio.sleep(2)

        except Exception as e:
            self.logger.error(f"Error scraping Allegro: {e}")

        return parts


class MarktplaatsNetherlandsScraper(BaseScraper):
    """Marktplaats.nl - Dutch marketplace with enterprise gear dumps"""

    def __init__(self):
        super().__init__(
            name="Marktplaats_NL",
            base_url="https://www.marktplaats.nl"
        )

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 3) -> List[PCPart]:
        """Scrape Marktplaats.nl"""
        parts = []

        search_terms = keywords or ['FPGA', 'server', 'workstation', 'Xilinx']

        try:
            for term in search_terms[:3]:
                search_url = f"{self.base_url}/q/{term}/"

                response = await self.fetch(search_url)
                soup = BeautifulSoup(response.text, 'lxml')

                items = soup.find_all('li', class_=re.compile(r'listing'))

                for item in items[:15]:
                    try:
                        title_elem = item.find('a', class_=re.compile(r'title'))
                        if not title_elem:
                            title_elem = item.find('h3')

                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        item_url = title_elem.get('href', '') if title_elem.name == 'a' else ''

                        # Extract price in EUR
                        price_elem = item.find(string=re.compile(r'€'))
                        price = None
                        if price_elem:
                            price_match = re.search(r'€\s*([\d.,]+)', price_elem)
                            if price_match:
                                price_eur = float(price_match.group(1).replace('.', '').replace(',', '.'))
                                # Convert EUR to USD (approximate: 1 EUR = 1.1 USD)
                                price = price_eur * 1.1

                        part = PCPart(
                            title=f"[NL] {title}",
                            price=price,
                            url=item_url if item_url.startswith('http') else self.base_url + item_url,
                            source_name=self.name,
                            condition='used',
                            location='Netherlands',
                            description="Marktplaats.nl listing"
                        )
                        parts.append(part)

                    except Exception as e:
                        self.logger.debug(f"Error parsing Marktplaats item: {e}")
                        continue

                await asyncio.sleep(2)

        except Exception as e:
            self.logger.error(f"Error scraping Marktplaats: {e}")

        return parts


class LeboncoinFranceScraper(BaseScraper):
    """Leboncoin.fr - French marketplace, labs selling old equipment"""

    def __init__(self):
        super().__init__(
            name="Leboncoin_FR",
            base_url="https://www.leboncoin.fr"
        )

    async def scrape(self, keywords: Optional[List[str]] = None, max_pages: int = 3) -> List[PCPart]:
        """Scrape Leboncoin.fr"""
        parts = []

        search_terms = keywords or ['FPGA', 'serveur', 'carte graphique', 'workstation']

        try:
            for term in search_terms[:3]:
                search_url = f"{self.base_url}/recherche?text={term}"

                response = await self.fetch(search_url)
                soup = BeautifulSoup(response.text, 'lxml')

                # Leboncoin uses React/dynamic loading, may need Selenium
                items = soup.find_all('a', attrs={'data-qa-id': 'adlink'})

                for item in items[:15]:
                    try:
                        title = item.get('title', '').strip()
                        if not title:
                            title_elem = item.find(attrs={'data-qa-id': 'adlink_title'})
                            title = title_elem.get_text(strip=True) if title_elem else ''

                        item_url = item.get('href', '')

                        # Extract price
                        price_elem = item.find(attrs={'data-qa-id': 'adlink_price'})
                        price = None
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            price_match = re.search(r'([\d\s]+)', price_text)
                            if price_match:
                                price_eur = float(price_match.group(1).replace(' ', ''))
                                price = price_eur * 1.1  # EUR to USD

                        part = PCPart(
                            title=f"[FR] {title}",
                            price=price,
                            url=item_url if item_url.startswith('http') else self.base_url + item_url,
                            source_name=self.name,
                            condition='used',
                            location='France',
                            description="Leboncoin.fr listing"
                        )
                        parts.append(part)

                    except Exception as e:
                        self.logger.debug(f"Error parsing Leboncoin item: {e}")
                        continue

                await asyncio.sleep(2)

        except Exception as e:
            self.logger.error(f"Error scraping Leboncoin: {e}")

        return parts
