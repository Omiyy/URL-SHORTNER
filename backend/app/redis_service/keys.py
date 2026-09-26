CLICK_BUFFER_KEY = "url_click_buffer"
INFLIGHT_CLICK_PREFIX = "url_click_buffer_inflight"
CACHE_PREFIX = "url_cache"
DELETED_PREFIX = "url_deleted"


def cache_key(short_code: str) -> str:
    return f"{CACHE_PREFIX}:{short_code}"


def deleted_key(short_code: str) -> str:
    return f"{DELETED_PREFIX}:{short_code}"
