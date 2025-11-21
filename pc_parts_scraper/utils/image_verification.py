"""
Perceptual Image Hashing for Visual Item Verification

Uses image hashing to:
1. Verify product images match expected items
2. Detect image manipulation/obfuscation by anti-bot systems
3. Find visually similar items
4. Detect duplicate listings with different images

Based on perceptual hashing algorithms that maintain correlation
between hash output and visual similarity.
"""

import logging
import requests
from typing import Optional, Tuple, Dict, List
from pathlib import Path
from PIL import Image
import imagehash
import io


class ImageVerifier:
    """
    Verify product images using perceptual hashing

    Perceptual hashes (unlike cryptographic hashes) maintain similarity
    even when images are resized, compressed, or slightly modified.
    """

    def __init__(self, hash_size: int = 8):
        """
        Initialize image verifier

        Args:
            hash_size: Hash size (8=64bit, 16=256bit)
                      Larger = more sensitive to differences
        """
        self.hash_size = hash_size
        self.logger = logging.getLogger(self.__class__.__name__)

    def download_image(self, url: str, timeout: int = 10) -> Optional[Image.Image]:
        """
        Download image from URL

        Args:
            url: Image URL
            timeout: Request timeout in seconds

        Returns:
            PIL Image object or None if failed
        """
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()

            img = Image.open(io.BytesIO(response.content))
            return img

        except Exception as e:
            self.logger.error(f"Failed to download image from {url}: {e}")
            return None

    def compute_hash(self, image: Image.Image, algorithm: str = "average") -> str:
        """
        Compute perceptual hash of image

        Args:
            image: PIL Image object
            algorithm: Hashing algorithm
                      - "average" (aHash): Fast, good for thumbnails
                      - "perceptual" (pHash): More robust, better for variations
                      - "difference" (dHash): Gradient-based, fast
                      - "wavelet" (wHash): Most accurate, slower

        Returns:
            Hash as hex string
        """
        try:
            if algorithm == "average":
                hash_obj = imagehash.average_hash(image, hash_size=self.hash_size)
            elif algorithm == "perceptual":
                hash_obj = imagehash.phash(image, hash_size=self.hash_size)
            elif algorithm == "difference":
                hash_obj = imagehash.dhash(image, hash_size=self.hash_size)
            elif algorithm == "wavelet":
                hash_obj = imagehash.whash(image, hash_size=self.hash_size)
            else:
                raise ValueError(f"Unknown algorithm: {algorithm}")

            return str(hash_obj)

        except Exception as e:
            self.logger.error(f"Failed to compute hash: {e}")
            return None

    def compute_hash_from_url(
        self,
        url: str,
        algorithm: str = "perceptual"
    ) -> Optional[str]:
        """
        Download image and compute hash

        Args:
            url: Image URL
            algorithm: Hashing algorithm

        Returns:
            Hash as hex string or None if failed
        """
        image = self.download_image(url)
        if image is None:
            return None

        return self.compute_hash(image, algorithm=algorithm)

    def compare_hashes(self, hash1: str, hash2: str) -> int:
        """
        Compare two perceptual hashes using Hamming distance

        Args:
            hash1: First hash (hex string)
            hash2: Second hash (hex string)

        Returns:
            Hamming distance (0 = identical, higher = more different)
            Typical thresholds:
            - 0-5: Very similar (likely same image)
            - 6-10: Similar (variations/crops)
            - 11-20: Somewhat similar
            - 21+: Different images
        """
        try:
            hash_obj1 = imagehash.hex_to_hash(hash1)
            hash_obj2 = imagehash.hex_to_hash(hash2)

            distance = hash_obj1 - hash_obj2  # Hamming distance
            return int(distance)

        except Exception as e:
            self.logger.error(f"Failed to compare hashes: {e}")
            return 999  # Max distance on error

    def verify_image(
        self,
        test_url: str,
        expected_hash: str,
        max_distance: int = 10,
        algorithm: str = "perceptual"
    ) -> Tuple[bool, int, str]:
        """
        Verify that an image matches expected hash

        Args:
            test_url: URL of image to verify
            expected_hash: Expected hash (hex string)
            max_distance: Maximum acceptable Hamming distance
            algorithm: Hashing algorithm to use

        Returns:
            (is_match, distance, reason) tuple
        """
        # Compute hash of test image
        test_hash = self.compute_hash_from_url(test_url, algorithm=algorithm)

        if test_hash is None:
            return False, 999, "Failed to download or hash image"

        # Compare
        distance = self.compare_hashes(test_hash, expected_hash)

        if distance <= max_distance:
            return True, distance, f"Match (distance: {distance})"
        else:
            return False, distance, f"No match (distance: {distance} > {max_distance})"

    def find_similar_images(
        self,
        target_hash: str,
        candidate_hashes: Dict[str, str],
        max_distance: int = 10
    ) -> List[Tuple[str, int]]:
        """
        Find images similar to target

        Args:
            target_hash: Hash to search for
            candidate_hashes: Dict of {item_id: hash}
            max_distance: Maximum distance to consider similar

        Returns:
            List of (item_id, distance) tuples, sorted by distance
        """
        similar = []

        for item_id, candidate_hash in candidate_hashes.items():
            distance = self.compare_hashes(target_hash, candidate_hash)

            if distance <= max_distance:
                similar.append((item_id, distance))

        # Sort by distance (most similar first)
        similar.sort(key=lambda x: x[1])

        return similar

    def detect_duplicate_listings(
        self,
        listings: List[Dict],
        max_distance: int = 5,
        algorithm: str = "perceptual"
    ) -> List[List[Dict]]:
        """
        Detect duplicate listings based on image similarity

        Args:
            listings: List of listing dicts with 'image_url' key
            max_distance: Maximum distance to consider duplicates
            algorithm: Hashing algorithm

        Returns:
            List of duplicate groups (each group is a list of listings)
        """
        # Compute hashes for all listings
        hashes = {}
        for i, listing in enumerate(listings):
            image_url = listing.get('image_url')
            if not image_url:
                continue

            hash_val = self.compute_hash_from_url(image_url, algorithm=algorithm)
            if hash_val:
                hashes[i] = hash_val

        # Find duplicates
        duplicates = []
        processed = set()

        for i, hash_i in hashes.items():
            if i in processed:
                continue

            group = [listings[i]]
            processed.add(i)

            # Find similar images
            for j, hash_j in hashes.items():
                if j <= i or j in processed:
                    continue

                distance = self.compare_hashes(hash_i, hash_j)
                if distance <= max_distance:
                    group.append(listings[j])
                    processed.add(j)

            if len(group) > 1:
                duplicates.append(group)

        self.logger.info(f"Found {len(duplicates)} duplicate groups")

        return duplicates


class ProductImageDatabase:
    """
    Database of known product images for verification

    Maintains a library of verified product images (e.g., stock photos
    of specific FPGA boards) for comparison against scraped listings.
    """

    def __init__(self, db_path: str = "data/image_hashes.json"):
        """
        Initialize image database

        Args:
            db_path: Path to JSON database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.images: Dict[str, Dict] = {}  # product_id -> {hash, metadata}
        self.verifier = ImageVerifier()
        self.logger = logging.getLogger(self.__class__.__name__)

        self.load()

    def load(self):
        """Load image database from disk"""
        if not self.db_path.exists():
            self.logger.info("No existing image database found")
            return

        try:
            import json
            with open(self.db_path, 'r') as f:
                self.images = json.load(f)

            self.logger.info(f"Loaded {len(self.images)} known product images")

        except Exception as e:
            self.logger.error(f"Failed to load image database: {e}")

    def save(self):
        """Save image database to disk"""
        try:
            import json
            with open(self.db_path, 'w') as f:
                json.dump(self.images, f, indent=2)

            self.logger.debug(f"Saved image database to {self.db_path}")

        except Exception as e:
            self.logger.error(f"Failed to save image database: {e}")

    def add_product(
        self,
        product_id: str,
        image_url: str,
        product_name: str,
        tags: List[str] = None,
        algorithm: str = "perceptual"
    ):
        """
        Add known product image to database

        Args:
            product_id: Unique product identifier (e.g., "trenz_te0803")
            image_url: URL of verified product image
            product_name: Human-readable name
            tags: Optional tags (e.g., ["fpga", "zynq", "som"])
            algorithm: Hashing algorithm
        """
        hash_val = self.verifier.compute_hash_from_url(image_url, algorithm=algorithm)

        if hash_val is None:
            self.logger.error(f"Failed to add product {product_id}: could not hash image")
            return

        self.images[product_id] = {
            'hash': hash_val,
            'product_name': product_name,
            'image_url': image_url,
            'tags': tags or [],
            'algorithm': algorithm
        }

        self.save()
        self.logger.info(f"Added product to database: {product_id}")

    def verify_listing(
        self,
        listing_image_url: str,
        product_id: str,
        max_distance: int = 10
    ) -> Tuple[bool, int, str]:
        """
        Verify that a listing image matches a known product

        Args:
            listing_image_url: Image from listing to verify
            product_id: Expected product ID
            max_distance: Maximum acceptable distance

        Returns:
            (is_match, distance, reason) tuple
        """
        if product_id not in self.images:
            return False, 999, f"Unknown product: {product_id}"

        product = self.images[product_id]
        expected_hash = product['hash']
        algorithm = product.get('algorithm', 'perceptual')

        return self.verifier.verify_image(
            listing_image_url,
            expected_hash,
            max_distance=max_distance,
            algorithm=algorithm
        )

    def find_matching_product(
        self,
        listing_image_url: str,
        max_distance: int = 10
    ) -> Optional[Tuple[str, int]]:
        """
        Identify which product a listing image matches

        Args:
            listing_image_url: Image to identify
            max_distance: Maximum distance to consider a match

        Returns:
            (product_id, distance) or None if no match
        """
        # Compute hash of listing image
        listing_hash = self.verifier.compute_hash_from_url(listing_image_url)
        if listing_hash is None:
            return None

        # Find closest match
        best_match = None
        best_distance = 999

        for product_id, product in self.images.items():
            distance = self.verifier.compare_hashes(listing_hash, product['hash'])

            if distance < best_distance and distance <= max_distance:
                best_distance = distance
                best_match = product_id

        if best_match:
            return (best_match, best_distance)

        return None
