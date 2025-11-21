"""
Unit Tests for TIER 2 Features

Tests:
- Image verification (perceptual hashing)
- Market trends analysis
- Smart alerts system
- Scheduler functionality
- DOM monitoring
"""

import asyncio
from datetime import datetime, timedelta
from PIL import Image
import io
import tempfile
import os


# Test Image Verification
def test_image_verifier_hash_computation():
    """Test perceptual hash computation"""
    from utils.image_verification import ImageVerifier

    verifier = ImageVerifier(hash_size=8)

    # Create test image (100x100 red square)
    img = Image.new('RGB', (100, 100), color='red')

    # Compute hashes with different algorithms
    hash_avg = verifier.compute_hash(img, algorithm="average")
    hash_perceptual = verifier.compute_hash(img, algorithm="perceptual")
    hash_diff = verifier.compute_hash(img, algorithm="difference")

    assert hash_avg is not None, "Average hash failed"
    assert hash_perceptual is not None, "Perceptual hash failed"
    assert hash_diff is not None, "Difference hash failed"
    assert len(hash_avg) == 16, "Hash should be 16 hex chars for size=8"

    print("✅ Image hash computation test passed")
    print(f"   Average hash: {hash_avg}")
    print(f"   Perceptual hash: {hash_perceptual}")


def test_image_hash_similarity():
    """Test that similar images produce similar hashes"""
    from utils.image_verification import ImageVerifier

    verifier = ImageVerifier(hash_size=8)

    # Create original image
    img1 = Image.new('RGB', (100, 100), color='blue')
    hash1 = verifier.compute_hash(img1, algorithm="perceptual")

    # Create slightly modified image (same color, different size)
    img2 = Image.new('RGB', (120, 120), color='blue')
    hash2 = verifier.compute_hash(img2, algorithm="perceptual")

    # Create very different image
    img3 = Image.new('RGB', (100, 100), color='red')
    hash3 = verifier.compute_hash(img3, algorithm="perceptual")

    # Compare
    distance_similar = verifier.compare_hashes(hash1, hash2)
    distance_different = verifier.compare_hashes(hash1, hash3)

    assert distance_similar < distance_different, "Similar images should have smaller distance"
    assert distance_similar <= 10, "Similar images should be within threshold"

    print("✅ Image similarity test passed")
    print(f"   Similar images distance: {distance_similar}")
    print(f"   Different images distance: {distance_different}")


def test_product_image_database():
    """Test product image database"""
    from utils.image_verification import ProductImageDatabase
    import tempfile

    # Use temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_db = f.name

    try:
        db = ProductImageDatabase(db_path=temp_db)

        # Create test image
        img = Image.new('RGB', (100, 100), color='green')
        temp_img = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img.save(temp_img.name)

        # Add product (using file:// URL for local testing)
        test_url = f"file://{temp_img.name}"

        # For testing, we'll manually add the hash
        hash_val = db.verifier.compute_hash(img, algorithm="perceptual")
        db.images['test_fpga_001'] = {
            'hash': hash_val,
            'product_name': 'Test FPGA Board',
            'image_url': test_url,
            'tags': ['fpga', 'xilinx'],
            'algorithm': 'perceptual'
        }
        db.save()

        # Verify it was saved
        assert 'test_fpga_001' in db.images
        assert db.images['test_fpga_001']['product_name'] == 'Test FPGA Board'

        print("✅ Product image database test passed")
        print(f"   Products in database: {len(db.images)}")

        # Cleanup
        os.remove(temp_img.name)

    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


# Test Market Trends
def test_price_trend_calculation():
    """Test price trend analysis"""
    from utils.market_trends import PriceHistoryTracker

    tracker = PriceHistoryTracker()

    # Create falling price trend
    falling_prices = []
    base_date = datetime.now() - timedelta(days=30)
    for i in range(30):
        price = 1000 - (i * 10)  # Declining from $1000 to $700
        falling_prices.append((base_date + timedelta(days=i), price))

    trend = tracker.calculate_trend(falling_prices, window_days=30)

    assert trend['direction'] == 'falling', "Should detect falling trend"
    assert trend['change_percent'] < -5, "Should show significant decrease"
    assert 'BUY' in trend['recommendation'].upper(), "Should recommend buying"

    print("✅ Price trend calculation test passed")
    print(f"   Direction: {trend['direction']}")
    print(f"   Change: {trend['change_percent']:.1f}%")
    print(f"   Recommendation: {trend['recommendation']}")


def test_best_time_to_buy():
    """Test best time to buy analysis"""
    from utils.market_trends import PriceHistoryTracker

    tracker = PriceHistoryTracker()

    # Create price data with pattern (cheaper on Mondays)
    prices = []
    base_date = datetime(2024, 1, 1)  # Start on a Monday

    for i in range(60):
        date = base_date + timedelta(days=i)
        # Cheaper on Mondays (day 0)
        if date.weekday() == 0:
            price = 800
        else:
            price = 900
        prices.append((date, price))

    analysis = tracker.find_best_time_to_buy(prices)

    assert analysis['best_day'] == 'Monday', "Should identify Monday as best day"
    assert analysis['best_day_avg_price'] < analysis['worst_day_avg_price']
    assert analysis['day_savings'] > 0, "Should show positive savings"

    print("✅ Best time to buy test passed")
    print(f"   Best day: {analysis['best_day']} (${analysis['best_day_avg_price']:.2f})")
    print(f"   Worst day: {analysis['worst_day']} (${analysis['worst_day_avg_price']:.2f})")
    print(f"   Potential savings: ${analysis['day_savings']:.2f}")


def test_market_opportunity_scorer():
    """Test market opportunity scoring"""
    from utils.market_trends import MarketOpportunityScorer

    scorer = MarketOpportunityScorer()

    # Test excellent opportunity
    excellent_item = {
        'title': 'Rare FPGA Board',
        'price': 500,
        'rarity_score': 85,
        'condition': 'new'
    }

    # Create falling price history
    price_history = []
    for i in range(30):
        price_history.append((datetime.now() - timedelta(days=30-i), 700 - i * 5))

    result = scorer.score_opportunity(
        excellent_item,
        price_history=price_history,
        seller_trust_score=90
    )

    assert result['opportunity_score'] >= 60, "Should have high opportunity score"
    assert len(result['factors']) > 0, "Should list contributing factors"
    assert 'OPPORTUNITY' in result['recommendation'].upper()

    print("✅ Market opportunity scorer test passed")
    print(f"   Opportunity score: {result['opportunity_score']:.1f}/100")
    print(f"   Recommendation: {result['recommendation']}")
    print(f"   Key factors: {result['factors'][:2]}")


def test_source_performance_tracker():
    """Test source performance analysis"""
    from utils.market_trends import SourcePerformanceTracker

    tracker = SourcePerformanceTracker()

    # Create mock items from different sources
    items = []

    # Source A: Many rare items
    for i in range(10):
        items.append({
            'source_name': 'SourceA',
            'price': 500 + i * 10,
            'rarity_score': 80
        })

    # Source B: Many items, low rarity
    for i in range(50):
        items.append({
            'source_name': 'SourceB',
            'price': 300 + i * 5,
            'rarity_score': 30
        })

    results = tracker.analyze_source_performance(items)

    assert len(results) == 2, "Should have 2 sources"
    assert results[0]['source'] == 'SourceA', "SourceA should rank first (higher rarity)"
    assert results[0]['performance_score'] > results[1]['performance_score']

    print("✅ Source performance tracker test passed")
    print(f"   Best source: {results[0]['source']} (score: {results[0]['performance_score']:.1f})")
    print(f"   Rare items found: {results[0]['rare_items_found']}")


# Test Smart Alerts
def test_alert_rule_matching():
    """Test alert rule matching logic"""
    from utils.smart_alerts import SmartAlertManager, AlertRule

    manager = SmartAlertManager()

    # Create alert rule
    rule = AlertRule(
        rule_id="test_rule_1",
        name="Cheap FPGAs",
        keywords=["fpga", "xilinx"],
        max_price=500,
        min_rarity_score=70,
        discord=True
    )

    manager.add_rule(rule)

    # Test matching item
    matching_item = {
        'title': 'Xilinx FPGA Board',
        'price': 450,
        'rarity_score': 80,
        'url': 'https://example.com/item1'
    }

    matches = manager.check_item(matching_item)
    assert len(matches) == 1, "Should match the rule"
    assert matches[0].rule_id == "test_rule_1"

    # Test non-matching item (too expensive)
    expensive_item = {
        'title': 'Xilinx FPGA Board',
        'price': 900,
        'rarity_score': 80,
        'url': 'https://example.com/item2'
    }

    matches = manager.check_item(expensive_item)
    assert len(matches) == 0, "Should not match (too expensive)"

    print("✅ Alert rule matching test passed")
    print(f"   Rule: {rule.name}")
    print(f"   Matching item found: Yes")
    print(f"   Non-matching filtered: Yes")


def test_alert_rate_limiting():
    """Test alert rate limiting"""
    from utils.smart_alerts import SmartAlertManager, AlertRule

    manager = SmartAlertManager()

    rule = AlertRule(
        rule_id="rate_limit_test",
        name="Rate Limited Rule",
        max_alerts_per_hour=3  # Only 3 alerts per hour
    )

    manager.add_rule(rule)

    # Simulate 5 recent alerts
    for i in range(5):
        manager.alert_history.append({
            'rule_id': 'rate_limit_test',
            'item_url': f'https://example.com/item{i}',
            'timestamp': datetime.now() - timedelta(minutes=10)
        })

    # Check if rate limited
    is_limited = manager._check_rate_limit('rate_limit_test')
    assert is_limited, "Should be rate limited after 5 alerts"

    print("✅ Alert rate limiting test passed")
    print(f"   Max alerts/hour: 3")
    print(f"   Recent alerts: 5")
    print(f"   Rate limited: Yes")


def test_price_drop_detector():
    """Test price drop detection"""
    from utils.smart_alerts import PriceDropDetector

    detector = PriceDropDetector(min_drop_percent=15.0)

    # Create items
    items = [
        {'id': 'item1', 'title': 'FPGA Board', 'price': 400},
        {'id': 'item2', 'title': 'GPU Module', 'price': 300}
    ]

    # Historical prices (higher than current)
    historical_prices = {
        'item1': [
            (datetime.now() - timedelta(days=7), 600),
            (datetime.now() - timedelta(days=3), 580),
            (datetime.now() - timedelta(days=1), 550)
        ],
        'item2': [
            (datetime.now() - timedelta(days=5), 320),
            (datetime.now() - timedelta(days=1), 310)
        ]
    }

    drops = detector.detect_drops(items, historical_prices)

    assert len(drops) == 1, "Should detect 1 significant drop"
    assert drops[0][0]['id'] == 'item1', "item1 should have significant drop"
    assert drops[0][1] >= 15.0, "Drop should be >= 15%"

    print("✅ Price drop detector test passed")
    print(f"   Items checked: {len(items)}")
    print(f"   Significant drops: {len(drops)}")
    print(f"   Drop percentage: {drops[0][1]:.1f}%")


# Test Scheduler
def test_scheduler_daily_job():
    """Test daily job scheduling"""
    from utils.scheduler import ScraperScheduler

    scheduler = ScraperScheduler()

    # Add daily job
    async def test_job():
        return "Job executed"

    scheduler.add_daily_job(
        test_job,
        hour=3,
        minute=30,
        job_id="test_daily"
    )

    jobs = scheduler.list_jobs()
    assert len(jobs) >= 1, "Should have at least 1 job"

    # Find our job
    our_job = next((j for j in jobs if j['id'] == 'test_daily'), None)
    assert our_job is not None, "Should find our job"
    assert our_job['next_run'] is not None, "Should have next run time"

    print("✅ Scheduler daily job test passed")
    print(f"   Job ID: {our_job['id']}")
    print(f"   Next run: {our_job['next_run']}")

    # Cleanup
    scheduler.shutdown()


def test_scheduler_interval_job():
    """Test interval job scheduling"""
    from utils.scheduler import ScraperScheduler

    scheduler = ScraperScheduler()

    async def test_job():
        return "Job executed"

    scheduler.add_interval_job(
        test_job,
        hours=2,
        job_id="test_interval"
    )

    jobs = scheduler.list_jobs()
    our_job = next((j for j in jobs if j['id'] == 'test_interval'), None)

    assert our_job is not None, "Should find interval job"
    assert 'interval' in str(our_job['trigger']).lower(), "Should be interval trigger"

    print("✅ Scheduler interval job test passed")
    print(f"   Job ID: {our_job['id']}")
    print(f"   Trigger: {our_job['trigger']}")

    scheduler.shutdown()


def test_scheduler_job_stats():
    """Test job statistics tracking"""
    from utils.scheduler import ScraperScheduler

    scheduler = ScraperScheduler()

    # Record some job results
    scheduler.record_job_result(
        job_id="test_scraper",
        items_found=15,
        duration_seconds=45.2,
        success=True
    )

    scheduler.record_job_result(
        job_id="test_scraper",
        items_found=8,
        duration_seconds=32.1,
        success=True
    )

    scheduler.record_job_result(
        job_id="test_scraper",
        items_found=0,
        duration_seconds=10.5,
        success=False,
        error="Connection timeout"
    )

    stats = scheduler.get_job_stats("test_scraper")

    assert stats['total_runs'] == 3
    assert stats['successful_runs'] == 2
    assert stats['success_rate'] < 100
    assert stats['total_items_found'] == 23

    print("✅ Scheduler job stats test passed")
    print(f"   Total runs: {stats['total_runs']}")
    print(f"   Success rate: {stats['success_rate']:.1f}%")
    print(f"   Avg items/run: {stats['avg_items_per_run']}")

    scheduler.shutdown()


# Test DOM Monitoring
def test_dom_structure_extraction():
    """Test DOM structure extraction"""
    from utils.dom_monitor import DOMStructureMonitor
    from lxml import etree

    monitor = DOMStructureMonitor()

    # Create test HTML
    html = """
    <html>
        <body>
            <div class="container">
                <div class="item" id="item1">
                    <h2 class="title">Product 1</h2>
                    <span class="price">$500</span>
                </div>
                <div class="item" id="item2">
                    <h2 class="title">Product 2</h2>
                    <span class="price">$750</span>
                </div>
            </div>
        </body>
    </html>
    """

    tree = etree.HTML(html)
    structure = monitor.extract_structure(tree)

    assert structure['total_elements'] > 0
    assert 'div' in structure['tag_counts']
    assert 'item' in structure['class_counts']
    assert 'item1' in structure['id_list'] or 'item2' in structure['id_list']

    print("✅ DOM structure extraction test passed")
    print(f"   Total elements: {structure['total_elements']}")
    print(f"   Unique tags: {len(structure['tag_counts'])}")
    print(f"   Unique classes: {len(structure['class_counts'])}")


def test_dom_similarity_calculation():
    """Test DOM similarity scoring"""
    from utils.dom_monitor import DOMStructureMonitor
    from lxml import etree

    monitor = DOMStructureMonitor()

    # Original HTML
    html1 = """
    <html>
        <body>
            <div class="product-list">
                <div class="product">Product 1</div>
                <div class="product">Product 2</div>
            </div>
        </body>
    </html>
    """

    # Similar HTML (same structure, different content)
    html2 = """
    <html>
        <body>
            <div class="product-list">
                <div class="product">Product A</div>
                <div class="product">Product B</div>
            </div>
        </body>
    </html>
    """

    # Different HTML
    html3 = """
    <html>
        <body>
            <table>
                <tr><td>Product 1</td></tr>
                <tr><td>Product 2</td></tr>
            </table>
        </body>
    </html>
    """

    tree1 = etree.HTML(html1)
    tree2 = etree.HTML(html2)
    tree3 = etree.HTML(html3)

    struct1 = monitor.extract_structure(tree1)
    struct2 = monitor.extract_structure(tree2)
    struct3 = monitor.extract_structure(tree3)

    similarity_same = monitor.calculate_similarity(struct1, struct2)
    similarity_different = monitor.calculate_similarity(struct1, struct3)

    assert similarity_same > similarity_different, "Similar structures should have higher score"
    assert similarity_same >= 80, "Nearly identical structures should score high"

    print("✅ DOM similarity calculation test passed")
    print(f"   Similar structures: {similarity_same:.1f}/100")
    print(f"   Different structures: {similarity_different:.1f}/100")


def test_dom_change_detection():
    """Test DOM change detection"""
    from utils.dom_monitor import DOMStructureMonitor
    from lxml import etree

    monitor = DOMStructureMonitor()

    # Original structure
    html_old = """
    <div class="listings">
        <div class="item">Item 1</div>
    </div>
    """

    # Changed structure (added new class)
    html_new = """
    <div class="listings-container">
        <div class="listing-item">Item 1</div>
    </div>
    """

    tree_old = etree.HTML(html_old)
    tree_new = etree.HTML(html_new)

    has_changed, similarity, report = monitor.detect_changes(
        old_html=etree.tostring(tree_old, encoding='unicode'),
        new_html=etree.tostring(tree_new, encoding='unicode'),
        threshold=90
    )

    assert has_changed, "Should detect structural changes"
    assert similarity < 90, "Similarity should be below threshold"
    assert len(report['changes']) > 0, "Should report specific changes"

    print("✅ DOM change detection test passed")
    print(f"   Change detected: {has_changed}")
    print(f"   Similarity: {similarity:.1f}/100")
    print(f"   Changes: {len(report['changes'])} found")


def run_all_tier2_tests():
    """Run all TIER 2 tests"""
    print("\n" + "="*60)
    print("TIER 2 UNIT TESTS")
    print("="*60 + "\n")

    tests = [
        ("Image Hash Computation", test_image_verifier_hash_computation),
        ("Image Hash Similarity", test_image_hash_similarity),
        ("Product Image Database", test_product_image_database),
        ("Price Trend Calculation", test_price_trend_calculation),
        ("Best Time to Buy", test_best_time_to_buy),
        ("Market Opportunity Scorer", test_market_opportunity_scorer),
        ("Source Performance Tracker", test_source_performance_tracker),
        ("Alert Rule Matching", test_alert_rule_matching),
        ("Alert Rate Limiting", test_alert_rate_limiting),
        ("Price Drop Detector", test_price_drop_detector),
        ("Scheduler Daily Job", test_scheduler_daily_job),
        ("Scheduler Interval Job", test_scheduler_interval_job),
        ("Scheduler Job Stats", test_scheduler_job_stats),
        ("DOM Structure Extraction", test_dom_structure_extraction),
        ("DOM Similarity Calculation", test_dom_similarity_calculation),
        ("DOM Change Detection", test_dom_change_detection),
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
    passed, failed = run_all_tier2_tests()
    exit(0 if failed == 0 else 1)
