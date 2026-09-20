from __future__ import annotations
import requests

class ESPNRequestor():
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

    @classmethod
    def get(cls: ESPNRequestor, url: str) -> requests.Response:
        return requests.get(url, headers={"User-Agent": cls.user_agent})