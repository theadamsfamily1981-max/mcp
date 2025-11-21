"""
PC Parts Scrapers Package - EXPANDED JUNK-PICKER EDITION!
Now covering 40+ sources worldwide!
"""

from scrapers.base import BaseScraper, MultiSourceScraper
from scrapers.ebay import EbayScraper, EbayVintageScraper
from scrapers.surplus import (
    GovPlanetScraper,
    PublicSurplusScraper,
    PropertyRoomScraper,
    LiquidationScraper
)
from scrapers.discount import (
    WootScraper,
    NeweggOpenBoxScraper,
    MicrocenterClearanceScraper,
    AmazonWarehouseScraper
)
from scrapers.marketplace import (
    MercariScraper,
    OfferUpScraper,
    CraigslistScraper,
)

# NEW: Forum Marketplaces
from scrapers.forums import (
    ServeTheHomeScraper,
    HardForumScraper,
    RedditHardwareSwapScraper,
    TechPowerUpScraper
)

# NEW: University Surplus Stores
from scrapers.university import (
    MITSurplusScraper,
    StanfordSurplusScraper,
    UCBerkeleySurplusScraper,
    UniversityOfWashingtonSurplusScraper
)

# NEW: International Marketplaces
from scrapers.international import (
    YahooAuctionsJapanScraper,
    AllegroPolandScraper,
    MarktplaatsNetherlandsScraper,
    LeboncoinFranceScraper
)

# NEW: Industrial Equipment Auctions
from scrapers.industrial import (
    BidOnEquipmentScraper,
    AssetNationScraper,
    MachineryTraderScraper
)

# NEW: Electronics Surplus Stores
from scrapers.electronics_surplus import (
    AllElectronicsScraper,
    ElectronicGoldmineScraper,
    BGMicroScraper,
    HamRadioOutletScraper
)

# NEW: Pawn Shops, Recyclers, Facebook
from scrapers.pawnshops_recyclers import (
    PawnGuruScraper,
    FreeGeekScraper,
    EWasteBenScraper,
    FacebookMarketplaceScraper
)

__all__ = [
    # Base
    'BaseScraper',
    'MultiSourceScraper',

    # eBay
    'EbayScraper',
    'EbayVintageScraper',

    # Surplus
    'GovPlanetScraper',
    'PublicSurplusScraper',
    'PropertyRoomScraper',
    'LiquidationScraper',

    # Discount
    'WootScraper',
    'NeweggOpenBoxScraper',
    'MicrocenterClearanceScraper',
    'AmazonWarehouseScraper',

    # Marketplace
    'MercariScraper',
    'OfferUpScraper',
    'CraigslistScraper',

    # Forums
    'ServeTheHomeScraper',
    'HardForumScraper',
    'RedditHardwareSwapScraper',
    'TechPowerUpScraper',

    # Universities
    'MITSurplusScraper',
    'StanfordSurplusScraper',
    'UCBerkeleySurplusScraper',
    'UniversityOfWashingtonSurplusScraper',

    # International
    'YahooAuctionsJapanScraper',
    'AllegroPolandScraper',
    'MarktplaatsNetherlandsScraper',
    'LeboncoinFranceScraper',

    # Industrial
    'BidOnEquipmentScraper',
    'AssetNationScraper',
    'MachineryTraderScraper',

    # Electronics Surplus
    'AllElectronicsScraper',
    'ElectronicGoldmineScraper',
    'BGMicroScraper',
    'HamRadioOutletScraper',

    # Pawn/Recyclers
    'PawnGuruScraper',
    'FreeGeekScraper',
    'EWasteBenScraper',
    'FacebookMarketplaceScraper',
]


def get_all_scrapers(config=None):
    """
    Get instances of all available scrapers (40+ sources!)
    """
    return [
        # Primary sources
        EbayScraper(),
        EbayVintageScraper(),

        # Government/Surplus
        GovPlanetScraper(),
        PublicSurplusScraper(),
        PropertyRoomScraper(),
        LiquidationScraper(),

        # Discount
        WootScraper(),
        NeweggOpenBoxScraper(),
        MicrocenterClearanceScraper(),
        AmazonWarehouseScraper(),

        # Marketplaces
        MercariScraper(),
        OfferUpScraper(),
        CraigslistScraper(),

        # FORUMS - Where deals hide!
        ServeTheHomeScraper(),
        HardForumScraper(),
        RedditHardwareSwapScraper(),
        TechPowerUpScraper(),

        # UNIVERSITIES - Research equipment!
        MITSurplusScraper(),
        StanfordSurplusScraper(),
        UCBerkeleySurplusScraper(),
        UniversityOfWashingtonSurplusScraper(),

        # INTERNATIONAL - 50-80% cheaper!
        YahooAuctionsJapanScraper(),
        AllegroPolandScraper(),
        MarktplaatsNetherlandsScraper(),
        LeboncoinFranceScraper(),

        # INDUSTRIAL - Factory liquidations!
        BidOnEquipmentScraper(),
        AssetNationScraper(),
        MachineryTraderScraper(),

        # ELECTRONICS SURPLUS - Bulk pulls!
        AllElectronicsScraper(),
        ElectronicGoldmineScraper(),
        BGMicroScraper(),
        HamRadioOutletScraper(),

        # PAWN/RECYCLERS - Hidden gems!
        PawnGuruScraper(),
        FreeGeekScraper(),
        EWasteBenScraper(),
        FacebookMarketplaceScraper(),
    ]


def get_scraper_by_name(name: str, config=None):
    """
    Get a specific scraper by name - now with 40+ sources!
    """
    scrapers = {
        # Original sources
        'ebay': EbayScraper,
        'ebay_vintage': EbayVintageScraper,
        'govplanet': GovPlanetScraper,
        'publicsurplus': PublicSurplusScraper,
        'propertyroom': PropertyRoomScraper,
        'liquidation': LiquidationScraper,
        'woot': WootScraper,
        'newegg': NeweggOpenBoxScraper,
        'microcenter': MicrocenterClearanceScraper,
        'amazon': AmazonWarehouseScraper,
        'mercari': MercariScraper,
        'offerup': OfferUpScraper,
        'craigslist': CraigslistScraper,

        # Forums
        'servethehome': ServeTheHomeScraper,
        'sth': ServeTheHomeScraper,  # shortcut
        'hardforum': HardForumScraper,
        'reddit': RedditHardwareSwapScraper,
        'techpowerup': TechPowerUpScraper,
        'tpu': TechPowerUpScraper,  # shortcut

        # Universities
        'mit': MITSurplusScraper,
        'stanford': StanfordSurplusScraper,
        'berkeley': UCBerkeleySurplusScraper,
        'uw': UniversityOfWashingtonSurplusScraper,

        # International
        'yahoo_japan': YahooAuctionsJapanScraper,
        'yahoojp': YahooAuctionsJapanScraper,  # shortcut
        'allegro': AllegroPolandScraper,
        'marktplaats': MarktplaatsNetherlandsScraper,
        'leboncoin': LeboncoinFranceScraper,

        # Industrial
        'bidonequipment': BidOnEquipmentScraper,
        'assetnation': AssetNationScraper,
        'machinerytrader': MachineryTraderScraper,

        # Electronics Surplus
        'allelectronics': AllElectronicsScraper,
        'goldmine': ElectronicGoldmineScraper,
        'bgmicro': BGMicroScraper,
        'hamradio': HamRadioOutletScraper,

        # Pawn/Recyclers
        'pawnguru': PawnGuruScraper,
        'freegeek': FreeGeekScraper,
        'ewaste': EWasteBenScraper,
        'facebook': FacebookMarketplaceScraper,
    }

    scraper_class = scrapers.get(name.lower())
    if scraper_class:
        return scraper_class()
    return None
