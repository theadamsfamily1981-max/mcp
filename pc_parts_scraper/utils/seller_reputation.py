"""
Seller Reputation and Trust System

Tracks seller reliability, flags scammers, and maintains
whitelist/blacklist for automated filtering.
"""

import json
import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum


class SellerStatus(Enum):
    """Seller trust status"""
    UNKNOWN = "unknown"
    TRUSTED = "trusted"
    WATCH = "watch"
    BLACKLISTED = "blacklisted"


@dataclass
class SellerRecord:
    """Record for tracking seller reputation"""
    seller_id: str
    seller_name: str
    status: str  # SellerStatus enum value
    trust_score: float  # 0-100
    total_listings_seen: int
    successful_purchases: int
    failed_purchases: int
    scam_reports: int
    positive_feedback_count: int
    negative_feedback_count: int
    first_seen: str  # ISO datetime
    last_seen: str  # ISO datetime
    notes: str
    tags: List[str]  # e.g., ["responsive", "ships_fast", "overpriced"]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'SellerRecord':
        """Create from dictionary"""
        return cls(**data)


class SellerReputationManager:
    """
    Manage seller reputation database

    Features:
    - Track seller history
    - Whitelist/blacklist management
    - Auto-scoring based on behavior
    - Notes and tagging
    """

    def __init__(self, db_path: str = "data/seller_reputation.json"):
        """
        Initialize reputation manager

        Args:
            db_path: Path to reputation database file
        """
        self.db_path = Path(db_path)
        self.sellers: Dict[str, SellerRecord] = {}
        self.whitelist: Set[str] = set()
        self.blacklist: Set[str] = set()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Create data directory if needed
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing data
        self.load()

    def load(self):
        """Load reputation database from disk"""
        if not self.db_path.exists():
            self.logger.info("No existing reputation database found")
            return

        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)

            # Load sellers
            for seller_id, seller_data in data.get('sellers', {}).items():
                self.sellers[seller_id] = SellerRecord.from_dict(seller_data)

            # Load lists
            self.whitelist = set(data.get('whitelist', []))
            self.blacklist = set(data.get('blacklist', []))

            self.logger.info(
                f"Loaded {len(self.sellers)} sellers, "
                f"{len(self.whitelist)} whitelisted, "
                f"{len(self.blacklist)} blacklisted"
            )

        except Exception as e:
            self.logger.error(f"Failed to load reputation database: {e}")

    def save(self):
        """Save reputation database to disk"""
        try:
            data = {
                'sellers': {
                    seller_id: seller.to_dict()
                    for seller_id, seller in self.sellers.items()
                },
                'whitelist': list(self.whitelist),
                'blacklist': list(self.blacklist),
                'last_updated': datetime.now().isoformat()
            }

            with open(self.db_path, 'w') as f:
                json.dump(data, f, indent=2)

            self.logger.debug(f"Saved reputation database to {self.db_path}")

        except Exception as e:
            self.logger.error(f"Failed to save reputation database: {e}")

    def get_or_create_seller(self, seller_id: str, seller_name: str = None) -> SellerRecord:
        """
        Get existing seller or create new record

        Args:
            seller_id: Unique seller identifier
            seller_name: Display name

        Returns:
            SellerRecord
        """
        if seller_id not in self.sellers:
            now = datetime.now().isoformat()
            self.sellers[seller_id] = SellerRecord(
                seller_id=seller_id,
                seller_name=seller_name or seller_id,
                status=SellerStatus.UNKNOWN.value,
                trust_score=50.0,  # Neutral starting score
                total_listings_seen=0,
                successful_purchases=0,
                failed_purchases=0,
                scam_reports=0,
                positive_feedback_count=0,
                negative_feedback_count=0,
                first_seen=now,
                last_seen=now,
                notes="",
                tags=[]
            )
            self.logger.info(f"Created new seller record: {seller_id}")

        return self.sellers[seller_id]

    def update_trust_score(self, seller_id: str):
        """
        Recalculate trust score based on history

        Scoring factors:
        - Successful purchases: +10 each
        - Failed purchases: -15 each
        - Scam reports: -30 each
        - Positive feedback: +2 each
        - Negative feedback: -5 each
        - Time active (bonus for longevity)
        """
        seller = self.sellers.get(seller_id)
        if not seller:
            return

        score = 50.0  # Start neutral

        # Purchase history
        score += seller.successful_purchases * 10
        score -= seller.failed_purchases * 15
        score -= seller.scam_reports * 30

        # Feedback
        score += seller.positive_feedback_count * 2
        score -= seller.negative_feedback_count * 5

        # Longevity bonus
        first_seen = datetime.fromisoformat(seller.first_seen)
        days_active = (datetime.now() - first_seen).days
        if days_active > 365:  # Active for over a year
            score += 10

        # Clamp to 0-100
        score = max(0.0, min(100.0, score))

        seller.trust_score = score

        # Auto-update status based on score
        if score >= 80:
            seller.status = SellerStatus.TRUSTED.value
        elif score <= 20:
            seller.status = SellerStatus.BLACKLISTED.value
            self.blacklist.add(seller_id)
        elif score <= 40:
            seller.status = SellerStatus.WATCH.value

        self.logger.info(f"Updated trust score for {seller_id}: {score:.1f}")

    def record_listing(self, seller_id: str, seller_name: str = None):
        """Record that we saw a listing from this seller"""
        seller = self.get_or_create_seller(seller_id, seller_name)
        seller.total_listings_seen += 1
        seller.last_seen = datetime.now().isoformat()
        self.save()

    def record_purchase(self, seller_id: str, success: bool, notes: str = ""):
        """
        Record a purchase attempt

        Args:
            seller_id: Seller identifier
            success: Whether purchase was successful
            notes: Additional notes
        """
        seller = self.sellers.get(seller_id)
        if not seller:
            self.logger.warning(f"Cannot record purchase for unknown seller: {seller_id}")
            return

        if success:
            seller.successful_purchases += 1
        else:
            seller.failed_purchases += 1

        if notes:
            seller.notes += f"\n[{datetime.now().isoformat()}] {notes}"

        self.update_trust_score(seller_id)
        self.save()

    def report_scam(self, seller_id: str, reason: str):
        """
        Report seller as scammer

        Args:
            seller_id: Seller to report
            reason: Reason for report
        """
        seller = self.sellers.get(seller_id)
        if not seller:
            self.logger.warning(f"Cannot report unknown seller: {seller_id}")
            return

        seller.scam_reports += 1
        seller.notes += f"\n[SCAM REPORT {datetime.now().isoformat()}] {reason}"

        # Auto-blacklist after 2 reports
        if seller.scam_reports >= 2:
            self.blacklist_seller(seller_id, f"Auto-blacklisted: {seller.scam_reports} scam reports")

        self.update_trust_score(seller_id)
        self.save()

        self.logger.warning(f"Scam report filed against {seller_id}: {reason}")

    def whitelist_seller(self, seller_id: str, reason: str = ""):
        """Add seller to whitelist (always show their items)"""
        seller = self.get_or_create_seller(seller_id)
        self.whitelist.add(seller_id)
        seller.status = SellerStatus.TRUSTED.value
        seller.trust_score = max(seller.trust_score, 90.0)

        if reason:
            seller.notes += f"\n[WHITELISTED {datetime.now().isoformat()}] {reason}"

        self.save()
        self.logger.info(f"Whitelisted seller: {seller_id}")

    def blacklist_seller(self, seller_id: str, reason: str = ""):
        """Add seller to blacklist (never show their items)"""
        seller = self.get_or_create_seller(seller_id)
        self.blacklist.add(seller_id)
        seller.status = SellerStatus.BLACKLISTED.value
        seller.trust_score = 0.0

        if reason:
            seller.notes += f"\n[BLACKLISTED {datetime.now().isoformat()}] {reason}"

        self.save()
        self.logger.warning(f"Blacklisted seller: {seller_id}")

    def is_blacklisted(self, seller_id: str) -> bool:
        """Check if seller is blacklisted"""
        return seller_id in self.blacklist

    def is_whitelisted(self, seller_id: str) -> bool:
        """Check if seller is whitelisted"""
        return seller_id in self.whitelist

    def should_show_listing(
        self,
        seller_id: str,
        min_trust_score: float = 30.0
    ) -> Tuple[bool, str]:
        """
        Determine if listing should be shown

        Args:
            seller_id: Seller to check
            min_trust_score: Minimum acceptable trust score

        Returns:
            (should_show, reason) tuple
        """
        # Always block blacklisted
        if seller_id in self.blacklist:
            return False, "Seller is blacklisted"

        # Always show whitelisted
        if seller_id in self.whitelist:
            return True, "Seller is whitelisted"

        # Check trust score
        seller = self.sellers.get(seller_id)
        if not seller:
            return True, "Unknown seller (neutral)"

        if seller.trust_score < min_trust_score:
            return False, f"Trust score too low: {seller.trust_score:.1f}"

        return True, f"Trust score acceptable: {seller.trust_score:.1f}"

    def get_seller_stats(self, seller_id: str) -> Optional[Dict]:
        """Get detailed stats for a seller"""
        seller = self.sellers.get(seller_id)
        if not seller:
            return None

        return {
            'seller_id': seller.seller_id,
            'seller_name': seller.seller_name,
            'status': seller.status,
            'trust_score': seller.trust_score,
            'is_whitelisted': seller_id in self.whitelist,
            'is_blacklisted': seller_id in self.blacklist,
            'stats': {
                'listings_seen': seller.total_listings_seen,
                'successful_purchases': seller.successful_purchases,
                'failed_purchases': seller.failed_purchases,
                'scam_reports': seller.scam_reports,
                'positive_feedback': seller.positive_feedback_count,
                'negative_feedback': seller.negative_feedback_count
            },
            'history': {
                'first_seen': seller.first_seen,
                'last_seen': seller.last_seen,
                'days_active': (
                    datetime.now() - datetime.fromisoformat(seller.first_seen)
                ).days
            },
            'tags': seller.tags,
            'notes': seller.notes
        }

    def get_top_sellers(self, limit: int = 10) -> List[Dict]:
        """Get top-rated sellers"""
        sorted_sellers = sorted(
            self.sellers.values(),
            key=lambda s: s.trust_score,
            reverse=True
        )

        return [
            self.get_seller_stats(seller.seller_id)
            for seller in sorted_sellers[:limit]
        ]

    def get_suspicious_sellers(self, limit: int = 10) -> List[Dict]:
        """Get most suspicious sellers"""
        sorted_sellers = sorted(
            self.sellers.values(),
            key=lambda s: s.trust_score
        )

        return [
            self.get_seller_stats(seller.seller_id)
            for seller in sorted_sellers[:limit]
            if seller.trust_score < 50
        ]
