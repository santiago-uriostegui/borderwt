import os
import xml.etree.ElementTree as ET
from urllib.request import urlopen

BWT_URL = os.getenv(
    "BWT_URL",
    "https://bwt.cbp.gov/xml/bwt.xml",
)


def fetch_border_wait_times_xml() -> ET.Element:
    with urlopen(BWT_URL, timeout=30) as response:
        body = response.read().decode("utf-8")

    return ET.fromstring(body)
