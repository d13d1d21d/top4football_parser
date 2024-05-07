import requests
import random

from logger import LogType
from utils import debug, logger
from dataclasses import dataclass


@dataclass
class ProxyData:
    protocol: str
    proxy: str

class ProxyClient:
    def __init__(
        self, 
        proxies: list[ProxyData],
        *, 
        retries: int, 
        timeout: int = 60
    ) -> None:
        self.proxies = proxies
        self.retries = retries
        self.timeout = timeout

    @staticmethod
    def proxy_request(method: str, url: str, proxy: ProxyData, **kwargs) -> requests.Response:
        return requests.request(
            method,
            url,
            proxies={ "http": f"{proxy.protocol}://{proxy.proxy}", "https": f"{proxy.protocol}://{proxy.proxy}" },
            **kwargs
        )
    
    @debug("{method} {url} - все попытки получить успешный ответ от сервера исчерпаны")
    def retry(
        self,
        method,
        url: str,
        **kwargs
    ) -> requests.Response | None:
        for _ in range(self.retries):
            all_proxies = list(self.proxies)

            while all_proxies:
                random.shuffle(all_proxies)
                proxy = all_proxies.pop()

                try:
                    headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0" }

                    req = self.proxy_request(method, url, proxy, headers=headers, timeout=self.timeout, **kwargs)

                    logger.log(LogType.INFO, f"{method} {url} - {req.status_code}. Proxy: {proxy.proxy}")
                    if req.status_code != 403: req.raise_for_status()

                    return req
                except requests.RequestException: continue
        
        raise requests.RequestException(f"All {self.retries} retries exhausted. Request failed")


            
def map_proxies(protocol: str, proxies: list[str]) -> list[ProxyData]:
    return [
        ProxyData(protocol, i) 
        for i in proxies
    ]