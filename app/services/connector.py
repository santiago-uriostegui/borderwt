import xml.etree.ElementTree as ET
from urllib.error import URLError
from urllib.request import urlopen

from defusedxml.ElementTree import fromstring
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class BorderWaitTimeFetchError(Exception):
    """Raised when the CBP border wait time feed cannot be fetched or parsed."""


@retry(
    retry=retry_if_exception_type((URLError, ET.ParseError)),
    stop=stop_after_attempt(get_settings().bwt_fetch_max_attempts),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
def fetch_border_wait_times_xml() -> ET.Element:
    settings = get_settings()
    logger.info("Fetching border wait time feed from %s", settings.bwt_url)

    try:
        with urlopen(
            settings.bwt_url, timeout=settings.bwt_fetch_timeout_seconds
        ) as response:
            body = response.read().decode("utf-8")
        return fromstring(body)
    except (URLError, ET.ParseError):
        logger.warning(
            "Attempt to fetch/parse border wait time feed failed", exc_info=True
        )
        raise
    except Exception as exc:
        raise BorderWaitTimeFetchError(
            f"Unexpected error fetching border wait time feed: {exc}"
        ) from exc
