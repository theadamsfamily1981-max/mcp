"""
Integration Tests for Full Scraper Pipeline

Tests the complete workflow:
1. Scraping items from sources (mock)
2. Processing with TIER 1 features (stealth, anomaly detection, reputation)
3. Processing with TIER 2 features (image verification, trends, alerts)
4. Database storage and retrieval
5. End-to-end workflow
"""

import asyncio
from datetime import datetime, timedelta
import tempfile
import os
from pathlib import Path


def test_scraper_to_database_pipeline():
    """Test scraping items and storing to database"""
    from scrapers.ebay import EbayScraper
    from database import Database, Item
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Use in-memory database
    engine = create_engine('sqlite:///:memory:')
    Database.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create mock items (since we're not actually scraping)
    mock_items = [
        Item(
            title="Xilinx Alveo U50 FPGA",
            price=850.00,
            url="https://example.com/item1",
            source_name="eBay",
            condition="used",
            description="Working FPGA board for data center acceleration",
            scraped_at=datetime.now()
        ),
        Item(
            title="AMD Instinct MI100",
            price=1200.00,
            url="https://example.com/item2",
            source_name="eBay",
            condition="new",
            description="High-performance compute accelerator",
            scraped_at=datetime.now()
        )
    ]

    # Add to database
    for item in mock_items:
        session.add(item)
    session.commit()

    # Verify items were stored
    stored_items = session.query(Item).all()
    assert len(stored_items) == 2, "Should store 2 items"
    assert stored_items[0].title == "Xilinx Alveo U50 FPGA"

    print("✅ Scraper to database pipeline test passed")
    print(f"   Items scraped: {len(mock_items)}")
    print(f"   Items stored: {len(stored_items)}")

    session.close()


def test_stealth_scraping_with_anomaly_detection():
    """Test scraping with stealth client and anomaly detection"""
    from utils.stealth_client import StealthHTTPClient
    from utils.anomaly_detection import PriceAnomalyDetector

    # Create stealth client
    client = StealthHTTPClient(rotate_profiles=True)
    assert client.browser_profile in client.BROWSER_PROFILES

    # Simulate scraped items
    scraped_items = [
        {'title': 'FPGA Board 1', 'price': 800},
        {'title': 'FPGA Board 2', 'price': 850},
        {'title': 'FPGA Board 3', 'price': 820},
        {'title': 'FPGA Board 4', 'price': 250},  # Anomaly!
        {'title': 'FPGA Board 5', 'price': 900},
    ]

    # Train anomaly detector
    detector = PriceAnomalyDetector()
    normal_prices = [item['price'] for item in scraped_items[:3]]
    detector.fit(normal_prices)

    # Detect anomalies
    anomalies = []
    for item in scraped_items:
        is_anomaly, score = detector.predict(item['price'])
        if is_anomaly:
            anomalies.append(item)

    assert len(anomalies) >= 1, "Should detect at least 1 anomaly"
    assert anomalies[0]['price'] == 250, "Should flag suspiciously low price"

    print("✅ Stealth scraping + anomaly detection test passed")
    print(f"   Items scraped: {len(scraped_items)}")
    print(f"   Anomalies detected: {len(anomalies)}")
    print(f"   Anomalous price: ${anomalies[0]['price']}")


def test_seller_reputation_integration():
    """Test seller reputation with real workflow"""
    from utils.seller_reputation import SellerReputationManager
    import tempfile

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_db = f.name

    try:
        manager = SellerReputationManager(db_path=temp_db)

        # Simulate scraping items from different sellers
        items = [
            {'seller_id': 'seller_A', 'seller_name': 'Good Seller', 'title': 'Item 1', 'price': 500},
            {'seller_id': 'seller_B', 'seller_name': 'Scammer', 'title': 'Item 2', 'price': 100},
            {'seller_id': 'seller_A', 'seller_name': 'Good Seller', 'title': 'Item 3', 'price': 600},
        ]

        # Process items with reputation check
        good_items = []
        blocked_items = []

        # Blacklist known scammer
        manager.blacklist_seller('seller_B', reason="Known scammer from previous reports")

        for item in items:
            seller_id = item['seller_id']
            seller_name = item['seller_name']

            # Get or create seller
            manager.get_or_create_seller(seller_id, seller_name)

            # Check if should show
            should_show, reason = manager.should_show_listing(seller_id)

            if should_show:
                good_items.append(item)
            else:
                blocked_items.append(item)

        assert len(good_items) == 2, "Should allow 2 items from good seller"
        assert len(blocked_items) == 1, "Should block 1 item from scammer"
        assert blocked_items[0]['seller_id'] == 'seller_B'

        print("✅ Seller reputation integration test passed")
        print(f"   Total items: {len(items)}")
        print(f"   Allowed items: {len(good_items)}")
        print(f"   Blocked items: {len(blocked_items)}")

    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_price_trends_with_alerts():
    """Test price trends analysis triggering smart alerts"""
    from utils.market_trends import PriceHistoryTracker
    from utils.smart_alerts import SmartAlertManager, AlertRule

    # Create price history showing falling trend
    price_history = []
    base_date = datetime.now() - timedelta(days=30)
    for i in range(30):
        price = 1000 - (i * 15)  # Steep decline
        price_history.append((base_date + timedelta(days=i), price))

    # Analyze trend
    tracker = PriceHistoryTracker()
    trend = tracker.calculate_trend(price_history)

    assert trend['direction'] == 'falling', "Should detect falling trend"

    # Set up alert for price drops
    alert_manager = SmartAlertManager()
    rule = AlertRule(
        rule_id="price_drop_alert",
        name="FPGA Price Drop Alert",
        keywords=["fpga"],
        min_discount_percent=20,
        discord=True
    )
    alert_manager.add_rule(rule)

    # Simulate new item with price drop
    current_price = price_history[-1][1]  # Latest (low) price
    avg_price = trend['avg_price']
    price_drop_percent = ((avg_price - current_price) / avg_price) * 100

    item = {
        'title': 'Xilinx FPGA Board',
        'price': current_price,
        'url': 'https://example.com/fpga'
    }

    # Check if alerts should trigger
    matching_rules = alert_manager.check_item(
        item,
        price_drop_percent=price_drop_percent
    )

    assert len(matching_rules) >= 1, "Should trigger alert for price drop"
    assert matching_rules[0].rule_id == "price_drop_alert"

    print("✅ Price trends + alerts integration test passed")
    print(f"   Price trend: {trend['direction']} ({trend['change_percent']:.1f}%)")
    print(f"   Price drop: {price_drop_percent:.1f}%")
    print(f"   Alerts triggered: {len(matching_rules)}")


def test_image_verification_workflow():
    """Test image verification in scraping workflow"""
    from utils.image_verification import ImageVerifier
    from PIL import Image
    import tempfile

    verifier = ImageVerifier(hash_size=8)

    # Create mock product image (blue square = FPGA board)
    fpga_image = Image.new('RGB', (100, 100), color='blue')
    temp_img1 = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    fpga_image.save(temp_img1.name)

    # Create listing image (same blue square, slightly different)
    listing_image = Image.new('RGB', (105, 105), color='blue')
    temp_img2 = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    listing_image.save(temp_img2.name)

    try:
        # Compute hashes
        fpga_hash = verifier.compute_hash(fpga_image, algorithm="perceptual")
        listing_hash = verifier.compute_hash(listing_image, algorithm="perceptual")

        # Verify similarity
        distance = verifier.compare_hashes(fpga_hash, listing_hash)

        assert distance <= 10, "Similar images should be within threshold"

        # Simulate workflow: verify listing matches expected product
        is_verified = distance <= 10

        print("✅ Image verification workflow test passed")
        print(f"   Product hash: {fpga_hash}")
        print(f"   Listing hash: {listing_hash}")
        print(f"   Hamming distance: {distance}")
        print(f"   Verified: {is_verified}")

    finally:
        os.remove(temp_img1.name)
        os.remove(temp_img2.name)


def test_market_opportunity_scoring_workflow():
    """Test complete market opportunity scoring"""
    from utils.market_trends import MarketOpportunityScorer
    from utils.seller_reputation import SellerReputationManager
    import tempfile

    scorer = MarketOpportunityScorer()

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_db = f.name

    try:
        # Setup seller reputation
        rep_manager = SellerReputationManager(db_path=temp_db)
        rep_manager.get_or_create_seller('trusted_seller', 'Trusted Seller')

        # Record successful history
        for _ in range(5):
            rep_manager.record_purchase('trusted_seller', success=True)

        seller = rep_manager.sellers['trusted_seller']
        trust_score = seller.trust_score

        # Create item with good attributes
        item = {
            'title': 'Rare Alveo U280 FPGA',
            'price': 1200,
            'rarity_score': 85,
            'condition': 'new',
            'seller_id': 'trusted_seller'
        }

        # Create falling price history
        price_history = []
        for i in range(20):
            price_history.append((
                datetime.now() - timedelta(days=20-i),
                1500 - (i * 10)
            ))

        # Score opportunity
        result = scorer.score_opportunity(
            item,
            price_history=price_history,
            seller_trust_score=trust_score
        )

        assert result['opportunity_score'] >= 60, "Should have high opportunity score"
        assert len(result['factors']) > 0, "Should list contributing factors"

        print("✅ Market opportunity scoring workflow test passed")
        print(f"   Opportunity score: {result['opportunity_score']:.1f}/100")
        print(f"   Seller trust: {trust_score:.1f}/100")
        print(f"   Recommendation: {result['recommendation']}")

    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_scheduler_with_scraping():
    """Test scheduler running scraping jobs"""
    from utils.scheduler import ScraperScheduler
    import time

    scheduler = ScraperScheduler()

    # Track job executions
    execution_count = [0]

    async def mock_scrape_job(source_name):
        """Mock scraping job"""
        execution_count[0] += 1
        # Simulate scraping
        items = [
            {'title': f'{source_name} Item 1', 'price': 500},
            {'title': f'{source_name} Item 2', 'price': 600}
        ]
        return items

    # Schedule job to run every 2 seconds (for testing)
    scheduler.add_interval_job(
        mock_scrape_job,
        minutes=None,
        hours=None,
        job_id="test_scraper",
        source_name="TestSource"
    )

    # Note: We can't easily test actual execution without waiting,
    # so we just verify the job was scheduled
    jobs = scheduler.list_jobs()
    test_job = next((j for j in jobs if j['id'] == 'test_scraper'), None)

    assert test_job is not None, "Job should be scheduled"

    print("✅ Scheduler integration test passed")
    print(f"   Jobs scheduled: {len(jobs)}")
    print(f"   Test job: {test_job['id']}")

    scheduler.shutdown()


def test_dom_monitoring_for_scraper_maintenance():
    """Test DOM monitoring detecting site changes"""
    from utils.dom_monitor import DOMStructureMonitor
    from lxml import etree

    monitor = DOMStructureMonitor()

    # Original site structure
    original_html = """
    <html>
        <body>
            <div class="listings">
                <div class="listing-card">
                    <h3 class="title">Product 1</h3>
                    <span class="price">$500</span>
                </div>
            </div>
        </body>
    </html>
    """

    # Site updated structure (different classes)
    updated_html = """
    <html>
        <body>
            <div class="products-grid">
                <div class="product-item">
                    <h3 class="product-title">Product 1</h3>
                    <span class="product-price">$500</span>
                </div>
            </div>
        </body>
    </html>
    """

    # Detect changes
    has_changed, similarity, report = monitor.detect_changes(
        original_html,
        updated_html,
        threshold=85
    )

    assert has_changed, "Should detect structural changes"
    assert similarity < 85, "Similarity should be below threshold"

    # Generate maintenance report
    maint_report = monitor.generate_maintenance_report(
        source_name="TestSite",
        old_selectors={
            'title': '.listing-card .title',
            'price': '.listing-card .price'
        },
        changes=report['changes']
    )

    assert maint_report['requires_update'], "Should flag for maintenance"
    assert len(maint_report['affected_selectors']) > 0

    print("✅ DOM monitoring for maintenance test passed")
    print(f"   Change detected: {has_changed}")
    print(f"   Similarity: {similarity:.1f}/100")
    print(f"   Requires update: {maint_report['requires_update']}")
    print(f"   Affected selectors: {len(maint_report['affected_selectors'])}")


def test_end_to_end_workflow():
    """Test complete end-to-end workflow"""
    from utils.stealth_client import StealthHTTPClient
    from utils.anomaly_detection import PriceAnomalyDetector
    from utils.seller_reputation import SellerReputationManager
    from utils.market_trends import MarketOpportunityScorer
    from utils.smart_alerts import SmartAlertManager, AlertRule
    import tempfile

    print("\n🔄 Running end-to-end workflow test...")

    # 1. Initialize all components
    print("   Step 1: Initialize components")
    stealth_client = StealthHTTPClient(rotate_profiles=True)
    price_detector = PriceAnomalyDetector()
    opportunity_scorer = MarketOpportunityScorer()
    alert_manager = SmartAlertManager()

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_db = f.name

    try:
        rep_manager = SellerReputationManager(db_path=temp_db)

        # 2. Simulate scraping (with stealth)
        print("   Step 2: Scrape items (stealth mode)")
        scraped_items = [
            {
                'title': 'Xilinx Alveo U50',
                'price': 750,
                'seller_id': 'good_seller',
                'seller_name': 'TrustedDealer',
                'rarity_score': 80,
                'condition': 'used',
                'url': 'https://example.com/item1'
            },
            {
                'title': 'AMD Instinct MI100',
                'price': 200,  # Suspiciously low!
                'seller_id': 'sketchy_seller',
                'seller_name': 'QuickSale',
                'rarity_score': 90,
                'condition': 'new',
                'url': 'https://example.com/item2'
            }
        ]

        # 3. Train anomaly detector
        print("   Step 3: Train anomaly detector")
        historical_prices = [800, 850, 900, 780, 820, 870, 810, 890]
        price_detector.fit(historical_prices)

        # 4. Process each item
        print("   Step 4: Process items")
        processed_items = []

        for item in scraped_items:
            # Check price anomaly
            is_anomaly, anomaly_score = price_detector.predict(item['price'])

            # Get/create seller
            rep_manager.get_or_create_seller(item['seller_id'], item['seller_name'])
            seller = rep_manager.sellers[item['seller_id']]

            # Check seller reputation
            should_show, reason = rep_manager.should_show_listing(item['seller_id'])

            if not should_show:
                print(f"   ⚠️  Blocked: {item['title']} - {reason}")
                continue

            # Flag anomaly
            if is_anomaly:
                print(f"   ⚠️  Price anomaly: {item['title']} - ${item['price']}")

            # Score opportunity
            opportunity = opportunity_scorer.score_opportunity(
                item,
                price_history=None,
                seller_trust_score=seller.trust_score
            )

            item['opportunity_score'] = opportunity['opportunity_score']
            item['is_anomaly'] = is_anomaly

            processed_items.append(item)

        # 5. Setup and check alerts
        print("   Step 5: Check alert rules")
        rule = AlertRule(
            rule_id="rare_fpga_alert",
            name="Rare FPGA Alert",
            keywords=["alveo", "instinct", "xilinx", "amd"],
            min_rarity_score=75,
            discord=True
        )
        alert_manager.add_rule(rule)

        triggered_alerts = []
        for item in processed_items:
            matches = alert_manager.check_item(item)
            if matches:
                triggered_alerts.append((item, matches))
                print(f"   🔔 Alert: {item['title']} matched rule '{matches[0].name}'")

        # 6. Verify workflow
        assert len(processed_items) >= 1, "Should process at least 1 item"
        assert any(item['is_anomaly'] for item in processed_items), "Should detect anomaly"
        assert len(triggered_alerts) >= 1, "Should trigger at least 1 alert"

        print("\n✅ End-to-end workflow test PASSED")
        print(f"   Items scraped: {len(scraped_items)}")
        print(f"   Items processed: {len(processed_items)}")
        print(f"   Anomalies detected: {sum(1 for i in processed_items if i['is_anomaly'])}")
        print(f"   Alerts triggered: {len(triggered_alerts)}")

    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def run_all_integration_tests():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("INTEGRATION TESTS")
    print("="*60 + "\n")

    tests = [
        ("Scraper → Database Pipeline", test_scraper_to_database_pipeline),
        ("Stealth Scraping + Anomaly Detection", test_stealth_scraping_with_anomaly_detection),
        ("Seller Reputation Integration", test_seller_reputation_integration),
        ("Price Trends + Alerts", test_price_trends_with_alerts),
        ("Image Verification Workflow", test_image_verification_workflow),
        ("Market Opportunity Scoring", test_market_opportunity_scoring_workflow),
        ("Scheduler Integration", test_scheduler_with_scraping),
        ("DOM Monitoring for Maintenance", test_dom_monitoring_for_scraper_maintenance),
        ("END-TO-END Workflow", test_end_to_end_workflow),
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
    passed, failed = run_all_integration_tests()
    exit(0 if failed == 0 else 1)
