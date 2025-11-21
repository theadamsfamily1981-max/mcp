"""
Market Trends Analysis and Price Intelligence

Tracks historical pricing, identifies trends, and provides
insights for optimal buying decisions.

Features:
- Price trend analysis (up/down/stable)
- Best time to buy recommendations
- Source performance tracking
- Market opportunity scoring
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


class PriceHistoryTracker:
    """
    Track price history and identify trends

    Analyzes historical data to determine:
    - Current trend direction
    - Rate of price change
    - Best time to buy
    - Price volatility
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def calculate_trend(
        self,
        prices: List[Tuple[datetime, float]],
        window_days: int = 30
    ) -> Dict[str, any]:
        """
        Calculate price trend over time window

        Args:
            prices: List of (datetime, price) tuples
            window_days: Analysis window in days

        Returns:
            Dict with trend analysis:
            {
                'direction': 'rising'|'falling'|'stable',
                'change_percent': float,
                'change_per_day': float,
                'volatility': float,
                'current_price': float,
                'avg_price': float,
                'min_price': float,
                'max_price': float,
                'recommendation': str
            }
        """
        if not prices or len(prices) < 2:
            return {
                'direction': 'unknown',
                'change_percent': 0.0,
                'change_per_day': 0.0,
                'volatility': 0.0,
                'recommendation': 'Insufficient data'
            }

        # Sort by date
        sorted_prices = sorted(prices, key=lambda x: x[0])

        # Filter to window
        cutoff_date = datetime.now() - timedelta(days=window_days)
        recent_prices = [
            (dt, price) for dt, price in sorted_prices
            if dt >= cutoff_date
        ]

        if len(recent_prices) < 2:
            recent_prices = sorted_prices[-10:]  # Use last 10 if window too narrow

        # Extract price values
        price_values = [p[1] for p in recent_prices]

        current_price = price_values[-1]
        oldest_price = price_values[0]
        avg_price = statistics.mean(price_values)
        min_price = min(price_values)
        max_price = max(price_values)

        # Calculate trend
        change_percent = ((current_price - oldest_price) / oldest_price) * 100 if oldest_price > 0 else 0

        # Days in window
        time_span = (recent_prices[-1][0] - recent_prices[0][0]).days
        change_per_day = change_percent / time_span if time_span > 0 else 0

        # Volatility (coefficient of variation)
        std_dev = statistics.stdev(price_values) if len(price_values) > 1 else 0
        volatility = (std_dev / avg_price) * 100 if avg_price > 0 else 0

        # Determine direction
        if change_percent > 5:
            direction = 'rising'
        elif change_percent < -5:
            direction = 'falling'
        else:
            direction = 'stable'

        # Generate recommendation
        recommendation = self._generate_recommendation(
            direction, change_percent, current_price, avg_price, min_price
        )

        return {
            'direction': direction,
            'change_percent': round(change_percent, 2),
            'change_per_day': round(change_per_day, 3),
            'volatility': round(volatility, 2),
            'current_price': current_price,
            'avg_price': round(avg_price, 2),
            'min_price': min_price,
            'max_price': max_price,
            'days_analyzed': len(recent_prices),
            'recommendation': recommendation
        }

    def _generate_recommendation(
        self,
        direction: str,
        change_percent: float,
        current_price: float,
        avg_price: float,
        min_price: float
    ) -> str:
        """Generate buying recommendation"""

        if direction == 'falling':
            if change_percent < -15:
                return "🔥 BUY NOW - Steep downtrend, prices dropping fast!"
            else:
                return "✅ GOOD TIME TO BUY - Prices declining"

        elif direction == 'rising':
            if change_percent > 15:
                return "🚫 WAIT - Steep uptrend, likely to reverse"
            else:
                return "⏳ MONITOR - Prices rising slowly"

        else:  # stable
            if current_price < avg_price * 0.95:
                return "✅ GOOD DEAL - Below average price"
            elif current_price > avg_price * 1.05:
                return "⏳ WAIT - Above average price"
            else:
                return "💰 FAIR PRICE - Near market average"

    def find_best_time_to_buy(
        self,
        prices: List[Tuple[datetime, float]]
    ) -> Dict[str, any]:
        """
        Analyze when items are typically cheapest

        Args:
            prices: Historical price data

        Returns:
            Analysis of best buying times
        """
        if not prices:
            return {'error': 'No price data'}

        # Group by day of week
        day_prices = defaultdict(list)
        hour_prices = defaultdict(list)

        for dt, price in prices:
            day_of_week = dt.strftime('%A')
            hour = dt.hour

            day_prices[day_of_week].append(price)
            hour_prices[hour].append(price)

        # Calculate averages
        day_avgs = {
            day: statistics.mean(prices)
            for day, prices in day_prices.items()
            if prices
        }

        hour_avgs = {
            hour: statistics.mean(prices)
            for hour, prices in hour_prices.items()
            if prices
        }

        # Find best times
        best_day = min(day_avgs.items(), key=lambda x: x[1]) if day_avgs else ('Unknown', 0)
        worst_day = max(day_avgs.items(), key=lambda x: x[1]) if day_avgs else ('Unknown', 0)

        best_hour = min(hour_avgs.items(), key=lambda x: x[1]) if hour_avgs else (0, 0)
        worst_hour = max(hour_avgs.items(), key=lambda x: x[1]) if hour_avgs else (0, 0)

        return {
            'best_day': best_day[0],
            'best_day_avg_price': round(best_day[1], 2),
            'worst_day': worst_day[0],
            'worst_day_avg_price': round(worst_day[1], 2),
            'day_savings': round(worst_day[1] - best_day[1], 2),
            'best_hour': f"{best_hour[0]}:00",
            'best_hour_avg_price': round(best_hour[1], 2),
            'worst_hour': f"{worst_hour[0]}:00",
            'worst_hour_avg_price': round(worst_hour[1], 2),
            'hour_savings': round(worst_hour[1] - best_hour[1], 2)
        }


class SourcePerformanceTracker:
    """
    Track which sources provide the best deals

    Analyzes:
    - Which sources have lowest prices
    - Which sources find rare items
    - Success rate per source
    - Response time and reliability
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def analyze_source_performance(
        self,
        items: List[Dict]
    ) -> List[Dict]:
        """
        Analyze performance of each source

        Args:
            items: List of items from database

        Returns:
            List of source performance dicts, sorted by score
        """
        source_stats = defaultdict(lambda: {
            'total_items': 0,
            'avg_price': [],
            'rare_items': 0,
            'total_rarity_score': 0
        })

        # Aggregate stats
        for item in items:
            source = item.get('source_name', 'Unknown')

            source_stats[source]['total_items'] += 1

            if item.get('price'):
                source_stats[source]['avg_price'].append(item['price'])

            rarity = item.get('rarity_score', 0)
            if rarity >= 70:
                source_stats[source]['rare_items'] += 1

            source_stats[source]['total_rarity_score'] += rarity

        # Calculate metrics
        results = []
        for source, stats in source_stats.items():
            avg_price = statistics.mean(stats['avg_price']) if stats['avg_price'] else 0
            avg_rarity = stats['total_rarity_score'] / stats['total_items'] if stats['total_items'] > 0 else 0

            # Performance score (higher = better)
            # Factors: rare items found, avg rarity score, total items
            performance_score = (
                stats['rare_items'] * 10 +  # 10 points per rare item
                avg_rarity * 2 +  # 2x average rarity
                stats['total_items'] * 0.1  # Small bonus for volume
            )

            results.append({
                'source': source,
                'total_items': stats['total_items'],
                'rare_items_found': stats['rare_items'],
                'rare_item_rate': round((stats['rare_items'] / stats['total_items']) * 100, 1) if stats['total_items'] > 0 else 0,
                'avg_price': round(avg_price, 2),
                'avg_rarity_score': round(avg_rarity, 1),
                'performance_score': round(performance_score, 1)
            })

        # Sort by performance score
        results.sort(key=lambda x: x['performance_score'], reverse=True)

        return results


class MarketOpportunityScorer:
    """
    Score market opportunities for items

    Combines multiple factors to identify best buying opportunities:
    - Price trend
    - Current price vs average
    - Seller reputation
    - Source reliability
    - Rarity score
    """

    def __init__(self):
        self.price_tracker = PriceHistoryTracker()
        self.logger = logging.getLogger(self.__class__.__name__)

    def score_opportunity(
        self,
        item: Dict,
        price_history: List[Tuple[datetime, float]] = None,
        seller_trust_score: float = 50.0
    ) -> Dict[str, any]:
        """
        Calculate opportunity score for an item

        Args:
            item: Item dict
            price_history: Optional historical prices
            seller_trust_score: Seller reputation (0-100)

        Returns:
            Dict with opportunity analysis
        """
        score = 0.0
        factors = []

        current_price = item.get('price', 0)
        rarity_score = item.get('rarity_score', 0)

        # Factor 1: Rarity (0-40 points)
        rarity_points = min(40, rarity_score * 0.4)
        score += rarity_points
        if rarity_points > 20:
            factors.append(f"High rarity: {rarity_score}/100 (+{rarity_points:.0f})")

        # Factor 2: Price trend (0-30 points)
        if price_history and len(price_history) >= 2:
            trend = self.price_tracker.calculate_trend(price_history)

            if trend['direction'] == 'falling':
                trend_points = 30
                factors.append(f"Falling prices: {trend['change_percent']:.1f}% ↓ (+30)")
            elif trend['direction'] == 'stable':
                # Check if below average
                if current_price < trend['avg_price'] * 0.9:
                    trend_points = 20
                    factors.append(f"Below average: ${current_price:.0f} vs ${trend['avg_price']:.0f} (+20)")
                else:
                    trend_points = 10
            else:  # rising
                trend_points = 0
                factors.append("Rising prices (-0)")

            score += trend_points

        # Factor 3: Seller trust (0-20 points)
        trust_points = (seller_trust_score / 100) * 20
        score += trust_points
        if seller_trust_score >= 80:
            factors.append(f"Trusted seller: {seller_trust_score:.0f}/100 (+{trust_points:.0f})")

        # Factor 4: Condition (0-10 points)
        condition = item.get('condition', 'used')
        condition_points = {
            'new': 10,
            'like_new': 9,
            'refurbished': 7,
            'used': 5,
            'for_parts': 2
        }.get(condition, 5)
        score += condition_points

        # Normalize to 0-100
        score = min(100, score)

        # Determine recommendation
        if score >= 80:
            recommendation = "🔥 EXCELLENT OPPORTUNITY - Buy immediately!"
        elif score >= 60:
            recommendation = "✅ GOOD OPPORTUNITY - Strong buy candidate"
        elif score >= 40:
            recommendation = "💰 FAIR OPPORTUNITY - Consider buying"
        else:
            recommendation = "⏳ WAIT - Better opportunities likely"

        return {
            'opportunity_score': round(score, 1),
            'recommendation': recommendation,
            'factors': factors,
            'breakdown': {
                'rarity_points': round(rarity_points, 1),
                'price_trend_points': round(trend_points if price_history else 0, 1),
                'seller_trust_points': round(trust_points, 1),
                'condition_points': condition_points
            }
        }
