#!/usr/bin/env python3
"""
Anti-detection helpers for Noxtools scraper (Alpha)
- User-Agent pools and randomized selection
- Realistic browser headers including Sec-Fetch-*
- Delay utilities with jitter (human-like pacing)
- Simple token-bucket rate limiter (per minute with burst)

No database writes; pure in-memory utilities for Alpha testing.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Dict, Optional

# —— User-Agent and header pools (aligned with existing SEM config) ——
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
]

ACCEPT_LANGUAGES = [
    'en-US,en;q=0.9,fr;q=0.8',
    'en-US,en;q=0.9',
    'fr-FR,fr;q=0.9,en;q=0.8',
    'en-GB,en;q=0.9,en-US;q=0.8',
]

# —— Config dataclass ——
@dataclass
class StealthConfig:
    header_rotation_interval_s: int = 3600
    base_delay_ms: int = 1000
    max_delay_ms: int = 2500
    jitter_ms: int = 200
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10
    backoff_base_s: float = 1.0
    backoff_multiplier: float = 2.0
    backoff_max_s: float = 10.0


def choose_user_agent() -> str:
    """Return a randomized realistic User-Agent string."""
    return random.choice(USER_AGENTS)


def choose_accept_language() -> str:
    """Return a randomized Accept-Language header value."""
    return random.choice(ACCEPT_LANGUAGES)


def build_stealth_headers(context: str = 'navigate', user_agent: Optional[str] = None) -> Dict[str, str]:
    """Build realistic browser headers.

    context: 'navigate' | 'fetch' | 'api'
    """
    ua = user_agent or choose_user_agent()
    accept_language = choose_accept_language()

    # Base headers common to modern browsers
    headers: Dict[str, str] = {
        'User-Agent': ua,
        'Accept-Language': accept_language,
        'Accept-Encoding': 'gzip, deflate, br',
        'Upgrade-Insecure-Requests': '1',
        'DNT': '1',  # Do Not Track (optional, realistic in some profiles)
    }

    # Accept varies by context
    if context == 'navigate':
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
        headers['Sec-Fetch-Site'] = 'none'
        headers['Sec-Fetch-Mode'] = 'navigate'
        headers['Sec-Fetch-User'] = '?1'  # Only for direct user navigation
        headers['Sec-Fetch-Dest'] = 'document'
    elif context == 'fetch':
        headers['Accept'] = '*/*'
        headers['Sec-Fetch-Site'] = 'same-origin'
        headers['Sec-Fetch-Mode'] = 'cors'
        headers['Sec-Fetch-Dest'] = 'empty'
    else:  # 'api' or other programmatic calls
        headers['Accept'] = 'application/json, text/plain, */*'
        headers['Sec-Fetch-Site'] = 'same-origin'
        headers['Sec-Fetch-Mode'] = 'cors'
        headers['Sec-Fetch-Dest'] = 'empty'

    return headers


def compute_delay_seconds(base_ms: int, jitter_ms: int, max_ms: Optional[int] = None) -> float:
    """Compute a human-like randomized delay in seconds."""
    # Ensure jitter doesn't exceed base delay to avoid negative values
    effective_jitter = min(jitter_ms, base_ms // 2) if base_ms > 0 else 0
    jitter = random.uniform(-effective_jitter, effective_jitter)
    value_ms = max(0.0, base_ms + jitter)
    if max_ms is not None:
        value_ms = min(value_ms, max_ms)
    return value_ms / 1000.0


class TokenBucket:
    """Simple token-bucket rate limiter.

    - capacity: max tokens (burst)
    - refill_rate_per_min: tokens added per minute
    """

    def __init__(self, capacity: int, refill_rate_per_min: int):
        self.capacity = max(1, capacity)
        self.tokens = float(capacity)
        self.refill_rate_per_min = max(1, refill_rate_per_min)
        self.last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        # tokens per second
        rate_per_s = self.refill_rate_per_min / 60.0
        added = elapsed * rate_per_s
        if added > 0:
            self.tokens = min(self.capacity, self.tokens + added)
        # Always update last_refill to prevent time drift
        self.last_refill = now

    def consume(self, tokens: float = 1.0) -> bool:
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def wait_for_token(self) -> None:
        """Block until at least one token is available."""
        while not self.consume(1.0):
            # sleep a small fraction to allow refill; avoid busy loop
            time.sleep(0.05)


def get_default_stealth_config() -> StealthConfig:
    """Return default stealth configuration aligned with existing SEM settings."""
    return StealthConfig()


def build_rate_limiter(cfg: Optional[StealthConfig] = None) -> TokenBucket:
    cfg = cfg or get_default_stealth_config()
    return TokenBucket(capacity=cfg.rate_limit_burst, refill_rate_per_min=cfg.rate_limit_per_minute)
