"""
Machine Learning Anomaly Detection for Rare Item Identification

Uses unsupervised ML to automatically flag:
1. Underpriced items (price anomalies)
2. Unusual sellers (reputation anomalies)
3. Sudden inventory spikes
4. Too-good-to-be-true deals

Based on Isolation Forest and One-Class SVM algorithms.
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler


class PriceAnomalyDetector:
    """
    Detect price anomalies using Isolation Forest

    Flags items that are significantly underpriced compared to
    historical market data.
    """

    def __init__(
        self,
        contamination: float = 0.1,  # Expected % of anomalies
        random_state: int = 42
    ):
        """
        Initialize anomaly detector

        Args:
            contamination: Expected proportion of anomalies (0.1 = 10%)
            random_state: Random seed for reproducibility
        """
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.logger = logging.getLogger(self.__class__.__name__)

    def fit(self, prices: List[float], additional_features: Optional[np.ndarray] = None):
        """
        Train the model on historical price data

        Args:
            prices: List of historical prices
            additional_features: Optional additional features (condition, age, etc.)
        """
        if len(prices) < 10:
            self.logger.warning(
                f"Insufficient data for training ({len(prices)} samples). "
                "Need at least 10 samples."
            )
            return

        # Prepare features
        X = np.array(prices).reshape(-1, 1)

        if additional_features is not None:
            X = np.hstack([X, additional_features])

        # Normalize
        X_scaled = self.scaler.fit_transform(X)

        # Train
        self.model.fit(X_scaled)
        self.is_fitted = True

        self.logger.info(
            f"Trained anomaly detector on {len(prices)} samples"
        )

    def predict(
        self,
        price: float,
        additional_features: Optional[np.ndarray] = None
    ) -> Tuple[bool, float]:
        """
        Predict if a price is anomalous (suspiciously low)

        Args:
            price: Price to check
            additional_features: Optional additional features

        Returns:
            (is_anomaly, anomaly_score) tuple
            - is_anomaly: True if anomalous
            - anomaly_score: -1 to 1 (lower = more anomalous)
        """
        if not self.is_fitted:
            self.logger.warning("Model not fitted. Call fit() first.")
            return False, 0.0

        # Prepare features
        X = np.array([[price]])

        if additional_features is not None:
            X = np.hstack([X, additional_features])

        # Scale
        X_scaled = self.scaler.transform(X)

        # Predict
        prediction = self.model.predict(X_scaled)[0]
        score = self.model.score_samples(X_scaled)[0]

        is_anomaly = (prediction == -1)  # -1 = anomaly in Isolation Forest

        return is_anomaly, float(score)


class MarketAnomalyDetector:
    """
    Advanced anomaly detection with multiple features

    Analyzes:
    - Price vs historical average
    - Seller reputation
    - Listing time (unusual hours)
    - Description quality
    """

    def __init__(self):
        self.price_detector = PriceAnomalyDetector()
        self.global_detector = OneClassSVM(nu=0.1, kernel="rbf", gamma='auto')
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_features(self, item: Dict) -> np.ndarray:
        """
        Extract features from an item for anomaly detection

        Args:
            item: Dict with keys: price, seller_rating, created_at, description

        Returns:
            Feature vector as numpy array
        """
        features = []

        # Price
        features.append(item.get('price', 0))

        # Seller reputation (0-100)
        features.append(item.get('seller_rating', 50))

        # Time features (suspicious if listed at odd hours)
        created_at = item.get('created_at')
        if created_at:
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)

            hour = created_at.hour
            # Encode hour cyclically
            features.append(np.sin(2 * np.pi * hour / 24))
            features.append(np.cos(2 * np.pi * hour / 24))
        else:
            features.extend([0, 0])

        # Description quality (longer = more legitimate)
        desc_length = len(item.get('description', ''))
        features.append(min(desc_length, 1000))  # Cap at 1000 chars

        # Condition score
        condition_map = {
            'new': 100,
            'like_new': 90,
            'refurbished': 80,
            'used': 60,
            'for_parts': 20
        }
        condition = item.get('condition', 'used')
        features.append(condition_map.get(condition, 50))

        return np.array(features).reshape(1, -1)

    def fit(self, items: List[Dict]):
        """
        Train on historical item data

        Args:
            items: List of item dicts
        """
        if len(items) < 20:
            self.logger.warning(
                f"Insufficient training data ({len(items)} items). "
                "Need at least 20 items."
            )
            return

        # Extract features for all items
        X = np.vstack([self.extract_features(item) for item in items])

        # Normalize
        X_scaled = self.scaler.fit_transform(X)

        # Train global detector
        self.global_detector.fit(X_scaled)

        # Train price-only detector
        prices = [item['price'] for item in items if 'price' in item and item['price']]
        if prices:
            self.price_detector.fit(prices)

        self.is_fitted = True
        self.logger.info(f"Trained market anomaly detector on {len(items)} items")

    def detect(self, item: Dict) -> Dict[str, any]:
        """
        Detect if item is anomalous

        Args:
            item: Item dict to analyze

        Returns:
            Dict with detection results:
            {
                'is_anomaly': bool,
                'confidence': float (0-1),
                'anomaly_score': float,
                'price_anomaly': bool,
                'reasons': List[str]
            }
        """
        if not self.is_fitted:
            return {
                'is_anomaly': False,
                'confidence': 0.0,
                'anomaly_score': 0.0,
                'price_anomaly': False,
                'reasons': ['Model not trained']
            }

        reasons = []

        # Extract features
        X = self.extract_features(item)
        X_scaled = self.scaler.transform(X)

        # Global anomaly detection
        global_pred = self.global_detector.predict(X_scaled)[0]
        global_score = self.global_detector.score_samples(X_scaled)[0]

        is_global_anomaly = (global_pred == -1)

        # Price-specific anomaly
        price = item.get('price')
        price_anomaly = False
        price_score = 0.0

        if price and self.price_detector.is_fitted:
            price_anomaly, price_score = self.price_detector.predict(price)

            if price_anomaly:
                reasons.append(f"Price ${price:.2f} is significantly below market average")

        # Check seller reputation
        seller_rating = item.get('seller_rating', 50)
        if seller_rating < 70:
            reasons.append(f"Low seller rating: {seller_rating}%")

        # Check listing time
        created_at = item.get('created_at')
        if created_at:
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)

            hour = created_at.hour
            # Suspicious if listed between 2-5 AM
            if 2 <= hour <= 5:
                reasons.append(f"Listed at unusual hour: {hour}:00")

        # Overall decision
        is_anomaly = is_global_anomaly or price_anomaly

        # Confidence score (0-1, higher = more confident it's anomalous)
        confidence = 0.0
        if is_anomaly:
            # Convert scores to confidence
            # Isolation Forest scores are typically between -0.5 and 0.5
            # More negative = more anomalous
            confidence = min(1.0, abs(min(global_score, price_score)))

        result = {
            'is_anomaly': is_anomaly,
            'confidence': confidence,
            'anomaly_score': float(global_score),
            'price_anomaly': price_anomaly,
            'price_score': float(price_score),
            'reasons': reasons
        }

        if is_anomaly:
            self.logger.info(
                f"ANOMALY DETECTED: {item.get('title', 'Unknown')} - "
                f"Confidence: {confidence:.2%} - Reasons: {', '.join(reasons)}"
            )

        return result


def calculate_price_deviation(
    current_price: float,
    historical_prices: List[float]
) -> Dict[str, float]:
    """
    Calculate how much a price deviates from historical average

    Args:
        current_price: Current item price
        historical_prices: List of historical prices for similar items

    Returns:
        Dict with deviation metrics:
        {
            'mean': float,
            'std': float,
            'deviation_percent': float,  # % below mean
            'z_score': float,  # Standard deviations from mean
            'percentile': float  # Percentile rank (0-100)
        }
    """
    if not historical_prices or len(historical_prices) < 2:
        return {
            'mean': current_price,
            'std': 0.0,
            'deviation_percent': 0.0,
            'z_score': 0.0,
            'percentile': 50.0
        }

    mean = np.mean(historical_prices)
    std = np.std(historical_prices)

    # Deviation percentage
    deviation_percent = ((mean - current_price) / mean) * 100 if mean > 0 else 0

    # Z-score (how many standard deviations from mean)
    z_score = (current_price - mean) / std if std > 0 else 0

    # Percentile rank
    percentile = (np.sum(np.array(historical_prices) < current_price) / len(historical_prices)) * 100

    return {
        'mean': float(mean),
        'std': float(std),
        'deviation_percent': float(deviation_percent),
        'z_score': float(z_score),
        'percentile': float(percentile)
    }
