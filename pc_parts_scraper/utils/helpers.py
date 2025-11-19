"""
Utility functions for PC Parts Scraper
"""

import re
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime
from fuzzywuzzy import fuzz
import yaml


def load_config(config_path: str = "config/settings.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def clean_price(price_str: str) -> Optional[float]:
    """Extract numeric price from string"""
    if not price_str:
        return None

    # Remove currency symbols and whitespace
    cleaned = re.sub(r'[^\d.,]', '', str(price_str))

    # Handle different formats
    if ',' in cleaned and '.' in cleaned:
        # Could be 1,234.56 or 1.234,56
        if cleaned.rfind(',') > cleaned.rfind('.'):
            cleaned = cleaned.replace('.', '').replace(',', '.')
        else:
            cleaned = cleaned.replace(',', '')
    elif ',' in cleaned:
        # Could be 1,234 or 1,23
        if len(cleaned.split(',')[-1]) == 3:
            cleaned = cleaned.replace(',', '')
        else:
            cleaned = cleaned.replace(',', '.')

    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_condition(condition_str: str) -> str:
    """Normalize condition strings to standard values"""
    if not condition_str:
        return "unknown"

    condition_lower = condition_str.lower()

    # Map to standard conditions
    if any(word in condition_lower for word in ['new', 'sealed', 'bnib', 'nib']):
        return 'new'
    elif any(word in condition_lower for word in ['refurb', 'renewed', 'certified']):
        return 'refurbished'
    elif any(word in condition_lower for word in ['open box', 'open-box', 'openbox']):
        return 'open_box'
    elif any(word in condition_lower for word in ['used', 'pre-owned', 'preowned']):
        return 'used'
    elif any(word in condition_lower for word in ['parts', 'repair', 'broken', 'as-is', 'as is']):
        return 'for_parts'
    else:
        return 'unknown'


def categorize_part(title: str, description: str = "") -> str:
    """Categorize a PC part based on title and description"""
    text = f"{title} {description}".lower()

    # CPU patterns
    cpu_patterns = [
        r'\bcpu\b', r'\bprocessor\b', r'\bintel\b.*\b(core|xeon|pentium|celeron)\b',
        r'\bamd\b.*\b(ryzen|athlon|epyc|opteron|phenom)\b', r'\bsocket\s*\d+',
        r'\blga\s*\d+', r'\bam[45]\b'
    ]
    for pattern in cpu_patterns:
        if re.search(pattern, text):
            return 'cpu'

    # GPU patterns
    gpu_patterns = [
        r'\bgpu\b', r'\bgraphics\s*card\b', r'\bvideo\s*card\b',
        r'\bgeforce\b', r'\bradeon\b', r'\brtx\b', r'\bgtx\b',
        r'\bvoodoo\b', r'\bquadro\b', r'\bfirepro\b', r'\btesla\b'
    ]
    for pattern in gpu_patterns:
        if re.search(pattern, text):
            return 'gpu'

    # Motherboard patterns
    mobo_patterns = [
        r'\bmotherboard\b', r'\bmobo\b', r'\bmainboard\b',
        r'\batx\b', r'\bmicro.?atx\b', r'\bmini.?itx\b'
    ]
    for pattern in mobo_patterns:
        if re.search(pattern, text):
            return 'motherboard'

    # RAM patterns
    ram_patterns = [
        r'\bram\b', r'\bmemory\b', r'\bddr[1-5]\b', r'\bsdram\b',
        r'\brdram\b', r'\bdimm\b', r'\bsimm\b', r'\bsodimm\b'
    ]
    for pattern in ram_patterns:
        if re.search(pattern, text):
            return 'ram'

    # Storage patterns
    storage_patterns = [
        r'\bssd\b', r'\bhdd\b', r'\bhard\s*drive\b', r'\bsolid\s*state\b',
        r'\bnvme\b', r'\bsata\b', r'\bscsi\b', r'\bide\b', r'\bpata\b'
    ]
    for pattern in storage_patterns:
        if re.search(pattern, text):
            return 'storage'

    # PSU patterns
    psu_patterns = [
        r'\bpsu\b', r'\bpower\s*supply\b', r'\b\d+\s*w(att)?\b'
    ]
    for pattern in psu_patterns:
        if re.search(pattern, text):
            return 'psu'

    # Cooling patterns
    cooling_patterns = [
        r'\bcooler\b', r'\bfan\b', r'\bheatsink\b', r'\baio\b',
        r'\bwater\s*cool', r'\bliquid\s*cool'
    ]
    for pattern in cooling_patterns:
        if re.search(pattern, text):
            return 'cooling'

    # Case patterns
    case_patterns = [
        r'\bcase\b', r'\bchassis\b', r'\btower\b', r'\benclosure\b'
    ]
    for pattern in case_patterns:
        if re.search(pattern, text):
            return 'case'

    # Sound card patterns
    sound_patterns = [
        r'\bsound\s*card\b', r'\baudio\s*card\b', r'\bsound\s*blaster\b'
    ]
    for pattern in sound_patterns:
        if re.search(pattern, text):
            return 'sound_card'

    # Network patterns
    network_patterns = [
        r'\bnetwork\s*card\b', r'\bnic\b', r'\bethernet\b', r'\bwifi\b'
    ]
    for pattern in network_patterns:
        if re.search(pattern, text):
            return 'network'

    return 'other'


def calculate_rarity_score(
    title: str,
    description: str,
    keywords: List[str],
    category: str,
    price: Optional[float] = None
) -> float:
    """
    Calculate a rarity score (0-100) for a PC part.
    Higher scores indicate rarer/more valuable items.
    """
    score = 0.0
    text = f"{title} {description}".lower()

    # Keyword matching (up to 50 points)
    keyword_matches = []
    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in text:
            keyword_matches.append(keyword)
            # More specific keywords get more points
            if len(keyword.split()) >= 2:
                score += 10
            else:
                score += 5

    score = min(score, 50)  # Cap keyword points at 50

    # Vintage indicators (up to 20 points)
    vintage_terms = [
        'vintage', 'retro', 'classic', 'legacy', 'rare', 'collectible',
        'nos', 'new old stock', 'sealed', 'bnib', 'engineering sample',
        'es chip', 'prototype', 'server pull', 'datacenter'
    ]
    for term in vintage_terms:
        if term in text:
            score += 5
    score = min(score, 70)  # Cap at 70 after vintage

    # Old technology indicators (up to 15 points)
    old_tech = [
        'agp', 'pci', 'isa', 'vesa', 'mca', 'eisa', 'ide', 'pata',
        'scsi', 'slot 1', 'slot a', 'socket 7', 'socket 370', 'socket 478'
    ]
    for tech in old_tech:
        if tech in text:
            score += 5
    score = min(score, 85)  # Cap at 85

    # Specific rare items (bonus points)
    ultra_rare = [
        '3dfx', 'voodoo 5', 'voodoo5', 'xeon phi', 'titan v', 'tesla v100',
        'radeon pro duo', 'r9 fury x', 'pentium pro', 'gravis ultrasound',
        'roland mt-32'
    ]
    for item in ultra_rare:
        if item in text:
            score += 15

    return min(score, 100)


def generate_item_hash(source_name: str, source_url: str) -> str:
    """Generate a unique hash for an item to detect duplicates"""
    unique_str = f"{source_name}:{source_url}"
    return hashlib.md5(unique_str.encode()).hexdigest()


def fuzzy_match_keywords(text: str, keywords: List[str], threshold: int = 80) -> List[str]:
    """Find keywords that fuzzy match in the text"""
    matched = []
    text_lower = text.lower()

    for keyword in keywords:
        # First try exact match
        if keyword.lower() in text_lower:
            matched.append(keyword)
            continue

        # Then try fuzzy match on word boundaries
        words = text_lower.split()
        for i in range(len(words)):
            # Try matching against single words and word pairs
            for j in range(i + 1, min(i + 4, len(words) + 1)):
                phrase = ' '.join(words[i:j])
                ratio = fuzz.ratio(keyword.lower(), phrase)
                if ratio >= threshold:
                    matched.append(keyword)
                    break
            else:
                continue
            break

    return list(set(matched))


def parse_auction_time(time_str: str) -> Optional[datetime]:
    """Parse various auction end time formats"""
    if not time_str:
        return None

    # Common patterns
    patterns = [
        r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',  # ISO format
        r'(\w+ \d+, \d{4} \d{1,2}:\d{2} [AP]M)',    # "Jan 1, 2024 3:00 PM"
        r'(\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2})',   # "1/1/2024 15:00"
    ]

    for pattern in patterns:
        match = re.search(pattern, time_str)
        if match:
            try:
                # Try parsing with different formats
                for fmt in [
                    '%Y-%m-%dT%H:%M:%S',
                    '%b %d, %Y %I:%M %p',
                    '%m/%d/%Y %H:%M'
                ]:
                    try:
                        return datetime.strptime(match.group(1), fmt)
                    except ValueError:
                        continue
            except Exception:
                continue

    return None


def format_price(price: float, currency: str = 'USD') -> str:
    """Format price for display"""
    if currency == 'USD':
        return f"${price:,.2f}"
    elif currency == 'EUR':
        return f"€{price:,.2f}"
    elif currency == 'GBP':
        return f"£{price:,.2f}"
    else:
        return f"{price:,.2f} {currency}"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
