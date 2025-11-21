"""
DOM Structure Monitoring for Auto-Maintenance

Detects when website layouts change, preventing scraper breakage.

Uses structural diffing to:
1. Detect selector drift (element paths changed)
2. Alert for manual review
3. Store baseline DOM structures
4. Calculate structural similarity scores
"""

import logging
from typing import Dict, List, Optional, Tuple
from lxml import html, etree
from datetime import datetime
import hashlib
import json
from pathlib import Path


class DOMStructureMonitor:
    """
    Monitor DOM structure changes to detect scraper breakage

    Compares current page structure against known-good baseline
    to identify layout changes that would break selectors.
    """

    def __init__(self, baseline_db_path: str = "data/dom_baselines.json"):
        """
        Initialize DOM monitor

        Args:
            baseline_db_path: Path to baseline database
        """
        self.db_path = Path(baseline_db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.baselines: Dict[str, Dict] = {}
        self.logger = logging.getLogger(self.__class__.__name__)

        self.load()

    def load(self):
        """Load baseline database"""
        if not self.db_path.exists():
            self.logger.info("No existing DOM baseline database found")
            return

        try:
            with open(self.db_path, 'r') as f:
                self.baselines = json.load(f)

            self.logger.info(f"Loaded {len(self.baselines)} DOM baselines")

        except Exception as e:
            self.logger.error(f"Failed to load DOM baselines: {e}")

    def save(self):
        """Save baseline database"""
        try:
            with open(self.db_path, 'w') as f:
                json.dump(self.baselines, f, indent=2)

            self.logger.debug(f"Saved DOM baselines to {self.db_path}")

        except Exception as e:
            self.logger.error(f"Failed to save DOM baselines: {e}")

    def parse_html(self, html_content: str) -> Optional[etree._Element]:
        """
        Parse HTML into DOM tree

        Args:
            html_content: HTML string

        Returns:
            lxml Element tree or None
        """
        try:
            tree = html.fromstring(html_content)
            return tree

        except Exception as e:
            self.logger.error(f"Failed to parse HTML: {e}")
            return None

    def extract_structure(self, tree: etree._Element, max_depth: int = 10) -> Dict:
        """
        Extract structural features from DOM tree

        Args:
            tree: lxml Element tree
            max_depth: Maximum depth to traverse

        Returns:
            Dict with structural features
        """
        structure = {
            'tag_counts': {},
            'class_counts': {},
            'id_list': [],
            'depth': 0,
            'total_elements': 0
        }

        def traverse(element, depth=0):
            if depth > max_depth:
                return

            structure['total_elements'] += 1
            structure['depth'] = max(structure['depth'], depth)

            # Count tags
            tag = element.tag
            structure['tag_counts'][tag] = structure['tag_counts'].get(tag, 0) + 1

            # Count classes
            classes = element.get('class', '')
            for cls in classes.split():
                if cls:
                    structure['class_counts'][cls] = structure['class_counts'].get(cls, 0) + 1

            # Collect IDs
            elem_id = element.get('id')
            if elem_id:
                structure['id_list'].append(elem_id)

            # Recurse
            for child in element:
                traverse(child, depth + 1)

        traverse(tree)

        return structure

    def compute_structure_hash(self, structure: Dict) -> str:
        """
        Compute hash of structure for quick comparison

        Args:
            structure: Structure dict

        Returns:
            SHA256 hash hex string
        """
        # Create normalized string representation
        normalized = json.dumps(structure, sort_keys=True)

        return hashlib.sha256(normalized.encode()).hexdigest()

    def calculate_similarity(self, struct1: Dict, struct2: Dict) -> float:
        """
        Calculate structural similarity between two DOM structures

        Args:
            struct1: First structure
            struct2: Second structure

        Returns:
            Similarity score (0-100, higher = more similar)
        """
        score = 0.0

        # Compare tag counts (40 points)
        tags1 = set(struct1['tag_counts'].keys())
        tags2 = set(struct2['tag_counts'].keys())

        if tags1 and tags2:
            tag_similarity = len(tags1 & tags2) / len(tags1 | tags2)
            score += tag_similarity * 40

        # Compare class counts (30 points)
        classes1 = set(struct1['class_counts'].keys())
        classes2 = set(struct2['class_counts'].keys())

        if classes1 and classes2:
            class_similarity = len(classes1 & classes2) / len(classes1 | classes2)
            score += class_similarity * 30

        # Compare IDs (20 points)
        ids1 = set(struct1['id_list'])
        ids2 = set(struct2['id_list'])

        if ids1 and ids2:
            id_similarity = len(ids1 & ids2) / len(ids1 | ids2)
            score += id_similarity * 20

        # Compare depth (10 points)
        depth1 = struct1.get('depth', 0)
        depth2 = struct2.get('depth', 0)
        if depth1 > 0 and depth2 > 0:
            depth_diff = abs(depth1 - depth2) / max(depth1, depth2)
            depth_similarity = 1.0 - depth_diff
            score += depth_similarity * 10

        return round(score, 2)

    def store_baseline(
        self,
        source_name: str,
        page_type: str,
        html_content: str,
        notes: str = ""
    ) -> bool:
        """
        Store baseline DOM structure for a source

        Args:
            source_name: Source identifier (e.g., "ebay")
            page_type: Page type (e.g., "search_results", "item_detail")
            html_content: HTML of known-good page
            notes: Optional notes

        Returns:
            True if successful
        """
        tree = self.parse_html(html_content)
        if tree is None:
            return False

        structure = self.extract_structure(tree)
        structure_hash = self.compute_structure_hash(structure)

        baseline_id = f"{source_name}_{page_type}"

        self.baselines[baseline_id] = {
            'source_name': source_name,
            'page_type': page_type,
            'structure': structure,
            'structure_hash': structure_hash,
            'created_at': datetime.now().isoformat(),
            'notes': notes
        }

        self.save()

        self.logger.info(f"Stored baseline for {baseline_id}")
        return True

    def check_structure(
        self,
        source_name: str,
        page_type: str,
        html_content: str,
        min_similarity: float = 70.0
    ) -> Tuple[bool, float, str]:
        """
        Check if current structure matches baseline

        Args:
            source_name: Source identifier
            page_type: Page type
            html_content: Current HTML
            min_similarity: Minimum similarity to consider valid

        Returns:
            (is_valid, similarity_score, message) tuple
        """
        baseline_id = f"{source_name}_{page_type}"

        if baseline_id not in self.baselines:
            return True, 100.0, "No baseline (assuming valid)"

        # Parse current HTML
        tree = self.parse_html(html_content)
        if tree is None:
            return False, 0.0, "Failed to parse HTML"

        # Extract current structure
        current_structure = self.extract_structure(tree)

        # Compare with baseline
        baseline_structure = self.baselines[baseline_id]['structure']
        similarity = self.calculate_similarity(baseline_structure, current_structure)

        if similarity >= min_similarity:
            return True, similarity, f"Structure valid (similarity: {similarity}%)"
        else:
            return False, similarity, f"⚠️ STRUCTURE CHANGED! (similarity: {similarity}% < {min_similarity}%)"

    def detect_selector_drift(
        self,
        source_name: str,
        page_type: str,
        selector: str,
        html_content: str
    ) -> Tuple[bool, List[str]]:
        """
        Test if a CSS selector still works

        Args:
            source_name: Source identifier
            page_type: Page type
            selector: CSS selector to test
            html_content: Current HTML

        Returns:
            (selector_works, suggested_alternatives) tuple
        """
        tree = self.parse_html(html_content)
        if tree is None:
            return False, []

        try:
            # Test selector
            elements = tree.cssselect(selector)

            if elements:
                return True, []  # Selector works

            # Selector failed - try to find alternatives
            # This is a simplified version; production would use more sophisticated matching
            alternatives = []

            # Try relaxing the selector
            parts = selector.split()
            if len(parts) > 1:
                # Try just the last part
                relaxed = parts[-1]
                if tree.cssselect(relaxed):
                    alternatives.append(relaxed)

            return False, alternatives

        except Exception as e:
            self.logger.error(f"Error testing selector '{selector}': {e}")
            return False, []

    def get_maintenance_report(self) -> List[Dict]:
        """
        Generate maintenance report for all sources

        Returns:
            List of issues requiring attention
        """
        issues = []

        for baseline_id, baseline in self.baselines.items():
            # Check age
            created_at = datetime.fromisoformat(baseline['created_at'])
            age_days = (datetime.now() - created_at).days

            if age_days > 90:
                issues.append({
                    'baseline_id': baseline_id,
                    'severity': 'low',
                    'issue': f"Baseline is {age_days} days old - consider refreshing",
                    'recommendation': "Run baseline update"
                })

        return issues
