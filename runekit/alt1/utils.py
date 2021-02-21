import codecs

import requests

from runekit.alt1.schema import AppManifest


def fetch_bom_json(url: str):
    req = requests.get(url)
    req.raise_for_status()

    if req.content[:3] == codecs.BOM_UTF8:
        req.encoding = "utf-8-sig"

    return req.json()
