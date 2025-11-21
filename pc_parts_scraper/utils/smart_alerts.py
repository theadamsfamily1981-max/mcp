"""
Smart Alert System for Price Drops and Rare Finds

Advanced alerting that only notifies for truly important events:
- Significant price drops (e.g., >20% decrease)
- Rare items matching saved searches
- Items from whitelisted sellers
- Market opportunities above threshold
- New listings for watched items

Integrates with Discord, Slack, Email, and SMS.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio


@dataclass
class AlertRule:
    """
    Rule for triggering alerts

    Defines conditions that must be met to send an alert.
    """
    rule_id: str
    name: str
    enabled: bool = True

    # Matching criteria
    keywords: List[str] = None
    categories: List[str] = None
    sources: List[str] = None

    # Price conditions
    max_price: Optional[float] = None
    min_discount_percent: Optional[float] = None  # e.g., 20 = notify if 20%+ off

    # Quality filters
    min_rarity_score: Optional[float] = None
    min_seller_trust: Optional[float] = None
    min_opportunity_score: Optional[float] = None

    # Alert channels
    discord: bool = False
    slack: bool = False
    email: bool = False
    sms: bool = False

    # Rate limiting
    max_alerts_per_hour: int = 5
    cooldown_hours: int = 24  # Don't re-alert for same item

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'enabled': self.enabled,
            'keywords': self.keywords,
            'categories': self.categories,
            'sources': self.sources,
            'max_price': self.max_price,
            'min_discount_percent': self.min_discount_percent,
            'min_rarity_score': self.min_rarity_score,
            'min_seller_trust': self.min_seller_trust,
            'min_opportunity_score': self.min_opportunity_score,
            'discord': self.discord,
            'slack': self.slack,
            'email': self.email,
            'sms': self.sms,
            'max_alerts_per_hour': self.max_alerts_per_hour,
            'cooldown_hours': self.cooldown_hours
        }


class SmartAlertManager:
    """
    Manage smart alerts with rate limiting and deduplication

    Prevents alert fatigue by:
    - Deduplicating alerts for same item
    - Rate limiting per rule
    - Cooldown periods
    - Importance-based prioritization
    """

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.alert_history: List[Dict] = []  # Recent alerts
        self.logger = logging.getLogger(self.__class__.__name__)

    def add_rule(self, rule: AlertRule):
        """Add or update alert rule"""
        self.rules[rule.rule_id] = rule
        self.logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, rule_id: str):
        """Remove alert rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            self.logger.info(f"Removed alert rule: {rule_id}")

    def check_item(
        self,
        item: Dict,
        price_drop_percent: Optional[float] = None,
        seller_trust: Optional[float] = None,
        opportunity_score: Optional[float] = None
    ) -> List[AlertRule]:
        """
        Check if item matches any alert rules

        Args:
            item: Item to check
            price_drop_percent: Optional price drop percentage
            seller_trust: Optional seller trust score
            opportunity_score: Optional market opportunity score

        Returns:
            List of matching alert rules
        """
        matching_rules = []

        for rule in self.rules.values():
            if not rule.enabled:
                continue

            # Check if already alerted recently
            if self._recently_alerted(rule.rule_id, item.get('url', '')):
                continue

            # Check if rule matches item
            if self._matches_rule(item, rule, price_drop_percent, seller_trust, opportunity_score):
                matching_rules.append(rule)

        return matching_rules

    def _matches_rule(
        self,
        item: Dict,
        rule: AlertRule,
        price_drop_percent: Optional[float],
        seller_trust: Optional[float],
        opportunity_score: Optional[float]
    ) -> bool:
        """Check if item matches rule criteria"""

        # Keywords
        if rule.keywords:
            title = item.get('title', '').lower()
            desc = item.get('description', '').lower()
            combined = f"{title} {desc}"

            if not any(kw.lower() in combined for kw in rule.keywords):
                return False

        # Categories
        if rule.categories:
            if item.get('category') not in rule.categories:
                return False

        # Sources
        if rule.sources:
            if item.get('source_name') not in rule.sources:
                return False

        # Price
        if rule.max_price is not None:
            if item.get('price', float('inf')) > rule.max_price:
                return False

        # Price drop
        if rule.min_discount_percent is not None and price_drop_percent is not None:
            if price_drop_percent < rule.min_discount_percent:
                return False

        # Rarity
        if rule.min_rarity_score is not None:
            if item.get('rarity_score', 0) < rule.min_rarity_score:
                return False

        # Seller trust
        if rule.min_seller_trust is not None and seller_trust is not None:
            if seller_trust < rule.min_seller_trust:
                return False

        # Opportunity score
        if rule.min_opportunity_score is not None and opportunity_score is not None:
            if opportunity_score < rule.min_opportunity_score:
                return False

        # Passed all checks
        return True

    def _recently_alerted(self, rule_id: str, item_url: str) -> bool:
        """Check if we recently alerted for this item"""

        cutoff = datetime.now() - timedelta(hours=self.rules[rule_id].cooldown_hours)

        for alert in self.alert_history:
            if (alert['rule_id'] == rule_id and
                alert['item_url'] == item_url and
                alert['timestamp'] > cutoff):
                return True

        return False

    def _check_rate_limit(self, rule_id: str) -> bool:
        """Check if rule has exceeded rate limit"""

        rule = self.rules.get(rule_id)
        if not rule:
            return False

        cutoff = datetime.now() - timedelta(hours=1)

        recent_alerts = [
            alert for alert in self.alert_history
            if alert['rule_id'] == rule_id and alert['timestamp'] > cutoff
        ]

        if len(recent_alerts) >= rule.max_alerts_per_hour:
            self.logger.warning(
                f"Rate limit exceeded for rule {rule.name}: "
                f"{len(recent_alerts)}/{rule.max_alerts_per_hour} in last hour"
            )
            return True

        return False

    async def send_alert(
        self,
        item: Dict,
        rule: AlertRule,
        extra_info: Dict = None
    ):
        """
        Send alert through configured channels

        Args:
            item: Item to alert about
            rule: Alert rule that triggered
            extra_info: Additional context (price drop %, etc.)
        """

        # Check rate limit
        if self._check_rate_limit(rule.rule_id):
            self.logger.info(f"Skipping alert due to rate limit: {rule.name}")
            return

        # Record alert
        self.alert_history.append({
            'rule_id': rule.rule_id,
            'item_url': item.get('url', ''),
            'timestamp': datetime.now()
        })

        # Build alert message
        message = self._build_alert_message(item, rule, extra_info)

        # Send to configured channels
        tasks = []

        if rule.discord:
            tasks.append(self._send_discord(message))

        if rule.slack:
            tasks.append(self._send_slack(message))

        if rule.email:
            tasks.append(self._send_email(message, item))

        if rule.sms:
            tasks.append(self._send_sms(message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        self.logger.info(f"Sent alert via {len(tasks)} channel(s): {item.get('title', 'Unknown')}")

    def _build_alert_message(
        self,
        item: Dict,
        rule: AlertRule,
        extra_info: Dict = None
    ) -> str:
        """Build formatted alert message"""

        title = item.get('title', 'Unknown Item')
        price = item.get('price')
        source = item.get('source_name', 'Unknown')
        url = item.get('url', '')
        rarity = item.get('rarity_score', 0)

        message = f"🔥 **ALERT: {rule.name}**\n\n"
        message += f"**{title}**\n"
        message += f"Source: {source}\n"

        if price:
            message += f"Price: ${price:.2f}\n"

        if rarity >= 70:
            message += f"Rarity: {rarity}/100 ⭐\n"

        if extra_info:
            if 'price_drop_percent' in extra_info:
                message += f"Price Drop: {extra_info['price_drop_percent']:.1f}% ↓\n"

            if 'seller_trust' in extra_info:
                message += f"Seller Trust: {extra_info['seller_trust']:.0f}/100\n"

            if 'opportunity_score' in extra_info:
                message += f"Opportunity Score: {extra_info['opportunity_score']:.0f}/100\n"

        message += f"\n🔗 {url}"

        return message

    async def _send_discord(self, message: str):
        """Send Discord webhook"""
        # Placeholder - integrate with existing Discord webhook
        self.logger.info(f"Would send Discord: {message[:100]}...")

    async def _send_slack(self, message: str):
        """Send Slack webhook"""
        # Placeholder - integrate with existing Slack webhook
        self.logger.info(f"Would send Slack: {message[:100]}...")

    async def _send_email(self, message: str, item: Dict):
        """Send email alert"""
        # Placeholder - integrate with existing email system
        self.logger.info(f"Would send email: {message[:100]}...")

    async def _send_sms(self, message: str):
        """Send SMS alert (via Twilio, etc.)"""
        # Placeholder - requires Twilio or similar service
        self.logger.info(f"Would send SMS: {message[:50]}...")


class PriceDropDetector:
    """
    Detect significant price drops for tracked items

    Monitors price history and alerts when items drop below thresholds.
    """

    def __init__(self, min_drop_percent: float = 15.0):
        """
        Initialize price drop detector

        Args:
            min_drop_percent: Minimum drop % to consider significant
        """
        self.min_drop_percent = min_drop_percent
        self.logger = logging.getLogger(self.__class__.__name__)

    def detect_drops(
        self,
        current_items: List[Dict],
        historical_prices: Dict[str, List[Tuple[datetime, float]]]
    ) -> List[Tuple[Dict, float]]:
        """
        Detect price drops in current items

        Args:
            current_items: Current scraped items
            historical_prices: Dict of {item_id: [(datetime, price), ...]}

        Returns:
            List of (item, drop_percent) tuples for items with significant drops
        """
        drops = []

        for item in current_items:
            item_id = item.get('id') or item.get('url')
            current_price = item.get('price')

            if not item_id or not current_price:
                continue

            # Get price history
            history = historical_prices.get(item_id, [])
            if len(history) < 2:
                continue

            # Find previous price (most recent before now)
            previous_prices = [p for dt, p in history]
            if not previous_prices:
                continue

            previous_price = previous_prices[-1]

            # Calculate drop
            drop_percent = ((previous_price - current_price) / previous_price) * 100

            if drop_percent >= self.min_drop_percent:
                drops.append((item, drop_percent))

                self.logger.info(
                    f"Price drop detected: {item.get('title', 'Unknown')} - "
                    f"${previous_price:.2f} → ${current_price:.2f} ({drop_percent:.1f}% off)"
                )

        return drops
