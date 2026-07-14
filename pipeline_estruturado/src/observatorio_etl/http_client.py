import time
from typing import Any

import requests


class HttpClient:
    def __init__(self, timeout: int = 60, retries: int = 3, backoff: float = 1.5):
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "observatorio-etl/0.1"})

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> Any:
        last_error = None
        for attempt in range(self.retries):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as error:
                last_error = error
                if attempt < self.retries - 1:
                    time.sleep(self.backoff * (attempt + 1))
        raise RuntimeError(f"Falha ao acessar {url}: {last_error}")
