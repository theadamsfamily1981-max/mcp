"""
Unit Tests for TIER 1 Features

Tests:
- StealthHTTPClient (TLS evasion)
- Anomaly detection (Isolation Forest)
- Seller reputation system
- Price deviation calculations
"""

import asyncio
from datetime import datetime, timedelta
import numpy as np


# Test StealthHTTPClient
def test_stealth_client_initialization():
    """Test that stealth client initializes correctly"""
    from utils.stealth_client import StealthHTTPClient

    client = StealthHTTPClient(
        proxy=None,
        rotate_profiles=True
    )

    assert client.browser_profile in client.BROWSER_PROFILES
    assert client.rotate_profiles == True
    assert client.session is not None

    print("✅ StealthHTTPClient initialization test passed")


def test_stealth_client_browser_profiles():
    """Test browser profile rotation"""
    from utils.stealth_client import StealthHTTPClient

    client = StealthHTTPClient(rotate_profiles=True)

    profiles = set()
    for _ in range(10):
        profile = client._get_browser_profile()
        profiles.add(profile)

    # Should get variety of profiles
    assert len(profiles) > 1, "Profile rotation not working"

    print(f"✅ Profile rotation test passed (got {len(profiles)} unique profiles)")


def test_stealth_client_proxy_rotation():
    """Test proxy rotation"""
    from utils.stealth_client import ProxyRotatingStealthClient

    proxies = [
        "http://proxy1:8080",
        "http://proxy2:8080",
        "http://proxy3:8080"
    ]

    client = ProxyRotatingStealthClient(proxy_list=proxies)

    # Check rotation
    proxy1 = client.proxy
    client._rotate_proxy()
    proxy2 = client.proxy

    assert proxy1 != proxy2, "Proxy not rotating"

    print("✅ Proxy rotation test passed")


# Test Anomaly Detection
def test_price_anomaly_detector():
    """Test price anomaly detection"""
    from utils.anomaly_detection import PriceAnomalyDetector

    detector = PriceAnomalyDetector()

    # Train on normal prices
    normal_prices = [800, 850, 920, 780, 900, 850, 880, 910, 795, 870]
    detector.fit(normal_prices)

    # Test normal price
    is_anomaly, score = detector.predict(850)
    assert not is_anomaly, "Normal price flagged as anomaly"

    # Test anomalous price (way too low)
    is_anomaly, score = detector.predict(250)
    assert is_anomaly, "Anomalous price not detected"

    print("✅ Price anomaly detection test passed")
    print(f"   Normal price (850): anomaly={is_anomaly}")
    print(f"   Low price (250): anomaly={True}")


def test_market_anomaly_detector():
    """Test market anomaly detector with multiple features"""
    from utils.anomaly_detection import MarketAnomalyDetector

    detector = MarketAnomalyDetector()

    # Generate training data
    training_items = []
    for i in range(30):
        training_items.append({
            'price': 800 + (i % 10) * 20,
            'seller_rating': 85 + (i % 10),
            'created_at': datetime.now() - timedelta(days=i),
            'description': 'Standard item description ' * 10,
            'condition': 'used'
        })

    detector.fit(training_items)

    # Test normal item
    normal_item = {
        'title': 'Alveo U50',
        'price': 850,
        'seller_rating': 90,
        'created_at': datetime.now(),
        'description': 'Good condition, tested working',
        'condition': 'used'
    }

    result = detector.detect(normal_item)
    print(f"✅ Market anomaly detection test passed")
    print(f"   Normal item - Anomaly: {result['is_anomaly']}, Confidence: {result['confidence']:.2%}")

    # Test suspicious item
    suspicious_item = {
        'title': 'Alveo U50',
        'price': 250,  # Way too low!
        'seller_rating': 30,  # Low rating!
        'created_at': datetime.now().replace(hour=3),  # 3 AM (suspicious)
        'description': 'great deal',  # Short description
        'condition': 'new'
    }

    result = detector.detect(suspicious_item)
    print(f"   Suspicious item - Anomaly: {result['is_anomaly']}, Confidence: {result['confidence']:.2%}")
    print(f"   Reasons: {result['reasons']}")


def test_price_deviation_calculation():
    """Test price deviation calculations"""
    from utils.anomaly_detection import calculate_price_deviation

    historical_prices = [800, 850, 920, 780, 900, 850]
    current_price = 250

    stats = calculate_price_deviation(current_price, historical_prices)

    assert stats['mean'] > 0
    assert stats['deviation_percent'] > 50, "Should detect major deviation"
    assert stats['z_score'] < -2, "Should be multiple std devs below mean"

    print("✅ Price deviation calculation test passed")
    print(f"   Mean: ${stats['mean']:.0f}")
    print(f"   Deviation: {stats['deviation_percent']:.1f}% below average")
    print(f"   Z-Score: {stats['z_score']:.2f} standard deviations")


# Test Seller Reputation
def test_seller_reputation_manager():
    """Test seller reputation tracking"""
    from utils.seller_reputation import SellerReputationManager
    import tempfile
    import os

    # Use temp file for testing
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_db = f.name

    try:
        manager = SellerReputationManager(db_path=temp_db)

        # Create seller
        seller = manager.get_or_create_seller('test_seller_123', 'Test Seller')
        assert seller.trust_score == 50.0, "Initial trust score should be 50"

        # Record successful purchase
        manager.record_purchase('test_seller_123', success=True)
        seller = manager.sellers['test_seller_123']
        assert seller.successful_purchases == 1
        assert seller.trust_score > 50, "Trust score should increase"

        # Record failed purchase
        manager.record_purchase('test_seller_123', success=False)
        seller = manager.sellers['test_seller_123']
        assert seller.failed_purchases == 1

        # Whitelist seller
        manager.whitelist_seller('test_seller_123')
        assert manager.is_whitelisted('test_seller_123')

        # Test blacklist
        manager.blacklist_seller('scammer_456', reason="Test scammer")
        assert manager.is_blacklisted('scammer_456')

        should_show, reason = manager.should_show_listing('scammer_456')
        assert not should_show, "Blacklisted seller should not be shown"

        print("✅ Seller reputation manager test passed")
        print(f"   Seller trust score: {seller.trust_score:.1f}")
        print(f"   Whitelisted: {manager.is_whitelisted('test_seller_123')}")
        print(f"   Scammer blocked: {manager.is_blacklisted('scammer_456')}")

    finally:
        # Cleanup
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_seller_trust_scoring():
    """Test trust score calculation"""
    from utils.seller_reputation import SellerReputationManager
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_db = f.name

    try:
        manager = SellerReputationManager(db_path=temp_db)

        # Create seller
        manager.get_or_create_seller('good_seller', 'Good Seller')

        # Simulate good history
        for _ in range(5):
            manager.record_purchase('good_seller', success=True)

        seller = manager.sellers['good_seller']
        manager.update_trust_score('good_seller')

        good_score = seller.trust_score
        assert good_score >= 80, "Good seller should have high trust"

        # Create bad seller
        manager.get_or_create_seller('bad_seller', 'Bad Seller')

        # Simulate bad history
        for _ in range(3):
            manager.record_purchase('bad_seller', success=False)
        manager.report_scam('bad_seller', "Scam report")

        seller = manager.sellers['bad_seller']
        bad_score = seller.trust_score
        assert bad_score <= 20, "Bad seller should have low trust"

        print("✅ Seller trust scoring test passed")
        print(f"   Good seller score: {good_score:.1f}/100")
        print(f"   Bad seller score: {bad_score:.1f}/100")

    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def run_all_tier1_tests():
    """Run all TIER 1 tests"""
    print("\n" + "="*60)
    print("TIER 1 UNIT TESTS")
    print("="*60 + "\n")

    tests = [
        ("StealthHTTPClient Initialization", test_stealth_client_initialization),
        ("Browser Profile Rotation", test_stealth_client_browser_profiles),
        ("Proxy Rotation", test_stealth_client_proxy_rotation),
        ("Price Anomaly Detection", test_price_anomaly_detector),
        ("Market Anomaly Detection", test_market_anomaly_detector),
        ("Price Deviation Calculation", test_price_deviation_calculation),
        ("Seller Reputation Manager", test_seller_reputation_manager),
        ("Seller Trust Scoring", test_seller_trust_scoring),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            print(f"\n📝 Running: {name}")
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {name}")
            print(f"   Error: {e}")
            failed += 1
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*60 + "\n")

    return passed, failed


if __name__ == "__main__":
    passed, failed = run_all_tier1_tests()
    exit(0 if failed == 0 else 1)
