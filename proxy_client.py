import requests
import random
from enum import Enum
from fake_useragent import UserAgent

class ProxyProtocol(Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"

class ProxyClient:
    def __init__(self, proxy_list: list[str], protocol: ProxyProtocol) -> None:
        self.proxy_list = proxy_list
        self.protocol = protocol

        # Пока не используется, т.к. периодически возвращает плохие user-agent'ы. Вместо этого статичный u.a. для каждого запроса.
        self.ua = UserAgent()

    def as_dict(self, url: str) -> dict[str, str]:
        return { "http": f"{self.protocol.value}://{url}", "https": f"{self.protocol.value}://{url}" }

    def http(
        self, 
        method: str, 
        url: str,
        **kwargs
    ) -> tuple[requests.Response, str] | None:
        while True:
            working_proxies = list(self.proxy_list)

            while working_proxies:
                random.shuffle(working_proxies)
                proxy = working_proxies.pop()

                kwargs["headers"] = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36" }

                try:
                    req = requests.request(method, url, proxies=self.as_dict(proxy), timeout=60, **kwargs)
                    """
                    top4football.de возвращает 403 даже при успешных запросах поэтому игнорируем
                    (без прокси тоже проверял)
                    """
                    if req.status_code != 403: req.raise_for_status()

                    return req
                except:
                     continue
