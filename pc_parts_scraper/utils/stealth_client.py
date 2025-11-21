"""
TLS Fingerprint Evasion Client
Uses curl_cffi to impersonate real browsers and bypass anti-bot detection

This client provides enterprise-grade stealth by:
1. Mimicking TLS/JA3 signatures of real browsers (Chrome, Firefox, Safari)
2. Supporting HTTP/2 fingerprint impersonation
3. Rotating browser signatures automatically
4. Integrating with proxy pools
"""

import random
import logging
from typing import Optional, Dict, Any
from curl_cffi import requests as curl_requests
from curl_cffi.requests import Session


class StealthHTTPClient:
    """
    Advanced HTTP client with TLS fingerprint evasion

    Uses curl_cffi to impersonate browser TLS signatures,
    making requests indistinguishable from real browser traffic.
    """

    # Browser impersonation profiles
    # These match real browser TLS/HTTP2 signatures
    BROWSER_PROFILES = [
        "chrome110",
        "chrome116",
        "chrome120",
        "chrome124",
        "edge101",
        "edge99",
        "safari15_5",
        "safari17_0",
    ]

    def __init__(
        self,
        proxy: Optional[str] = None,
        timeout: int = 30,
        browser_profile: Optional[str] = None,
        rotate_profiles: bool = True
    ):
        """
        Initialize stealth client

        Args:
            proxy: Proxy URL (http://host:port or socks5://host:port)
            timeout: Request timeout in seconds
            browser_profile: Specific browser to impersonate (or None for random)
            rotate_profiles: Whether to rotate browser profiles per session
        """
        self.proxy = proxy
        self.timeout = timeout
        self.rotate_profiles = rotate_profiles
        self.logger = logging.getLogger(self.__class__.__name__)

        # Select browser profile
        if browser_profile and browser_profile in self.BROWSER_PROFILES:
            self.browser_profile = browser_profile
        else:
            self.browser_profile = random.choice(self.BROWSER_PROFILES)

        self.logger.info(f"Initialized StealthClient with profile: {self.browser_profile}")

        # Create session with impersonation
        self.session = self._create_session()

    def _create_session(self) -> Session:
        """Create a curl_cffi session with browser impersonation"""
        session = Session()

        # Configure proxy if provided
        if self.proxy:
            session.proxies = {
                "http": self.proxy,
                "https": self.proxy
            }

        return session

    def _get_browser_profile(self) -> str:
        """Get browser profile for this request"""
        if self.rotate_profiles:
            # Rotate profile per request for maximum entropy
            return random.choice(self.BROWSER_PROFILES)
        return self.browser_profile

    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Any:
        """
        Perform GET request with TLS impersonation

        Args:
            url: Target URL
            headers: Additional headers
            **kwargs: Additional arguments for curl_cffi

        Returns:
            Response object
        """
        profile = self._get_browser_profile()

        try:
            response = self.session.get(
                url,
                headers=headers,
                timeout=self.timeout,
                impersonate=profile,  # KEY: Browser impersonation
                **kwargs
            )

            self.logger.debug(
                f"GET {url} -> {response.status_code} "
                f"(profile: {profile})"
            )

            return response

        except Exception as e:
            self.logger.error(f"Request failed for {url}: {e}")
            raise

    def post(
        self,
        url: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Any:
        """
        Perform POST request with TLS impersonation

        Args:
            url: Target URL
            data: Form data
            json: JSON data
            headers: Additional headers
            **kwargs: Additional arguments for curl_cffi

        Returns:
            Response object
        """
        profile = self._get_browser_profile()

        try:
            response = self.session.post(
                url,
                data=data,
                json=json,
                headers=headers,
                timeout=self.timeout,
                impersonate=profile,
                **kwargs
            )

            self.logger.debug(
                f"POST {url} -> {response.status_code} "
                f"(profile: {profile})"
            )

            return response

        except Exception as e:
            self.logger.error(f"POST request failed for {url}: {e}")
            raise

    def close(self):
        """Close the session"""
        if self.session:
            self.session.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class ProxyRotatingStealthClient(StealthHTTPClient):
    """
    Stealth client with automatic proxy rotation

    Maintains a pool of proxies and rotates them to distribute
    traffic and avoid rate limiting.
    """

    def __init__(
        self,
        proxy_list: list[str],
        timeout: int = 30,
        browser_profile: Optional[str] = None,
        rotate_profiles: bool = True
    ):
        """
        Initialize with proxy pool

        Args:
            proxy_list: List of proxy URLs
            timeout: Request timeout
            browser_profile: Browser to impersonate
            rotate_profiles: Rotate browser profiles
        """
        self.proxy_list = proxy_list
        self.proxy_index = 0

        # Initialize with first proxy
        super().__init__(
            proxy=self._get_next_proxy(),
            timeout=timeout,
            browser_profile=browser_profile,
            rotate_profiles=rotate_profiles
        )

    def _get_next_proxy(self) -> str:
        """Get next proxy from the pool (round-robin)"""
        if not self.proxy_list:
            return None

        proxy = self.proxy_list[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(self.proxy_list)
        return proxy

    def _rotate_proxy(self):
        """Rotate to next proxy and recreate session"""
        self.proxy = self._get_next_proxy()
        self.session.close()
        self.session = self._create_session()
        self.logger.info(f"Rotated to proxy: {self.proxy}")

    def get(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> Any:
        """GET with automatic proxy rotation on failure"""
        max_retries = min(3, len(self.proxy_list))

        for attempt in range(max_retries):
            try:
                return super().get(url, headers=headers, **kwargs)
            except Exception as e:
                self.logger.warning(
                    f"Request failed (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    self._rotate_proxy()
                else:
                    raise
