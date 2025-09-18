"""Configuration API et serveurs"""

API_CONFIG = {
    "port": 3000,
    "host": "localhost",
    "cors_enabled": True,
    "timeout": 30000
}

SCRAPING_CONFIG = {
    "timeout": 45000,
    "retry_attempts": 3,
    "delay_between_requests": 2000,
    "max_concurrent": 1
}
