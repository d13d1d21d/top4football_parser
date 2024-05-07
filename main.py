import concurrent.futures
import platform

from settings.settings import settings
from colorama import Fore, Style, just_fix_windows_console
from proxy_client import *
from utils import *
from webparser import *
from proxy_client import *



if platform.system() == "Windows":
    just_fix_windows_console()


SOURCES = {
    "/c/fussball-fussballschuhe": "футбольные бутсы",
    "/c/fussball-laufschuhe": "беговая обувь"
}

proxy_client = ProxyClient(
    map_proxies("http", open("proxy_list.txt").read().split("\n")),
    retries=5
)
parsers = (
    Parser(*list(SOURCES.items())[0], proxy_client),
    Parser(*list(SOURCES.items())[1], proxy_client)
)

urls = []
products = []

logger.log_new_run()

print(f"[{Fore.CYAN + Style.BRIGHT}⧖{Style.RESET_ALL}] Получение URLs...")
logger.log(LogType.INFO, f"\"Получено {len(urls)} URLs\"")

for parser in parsers:
    n_pages = parser.get_n_pages()
    p_urls = []

    with concurrent.futures.ThreadPoolExecutor(settings.threads) as executor:
        for url in executor.map(parser.get_urls, range(1, n_pages + 1)):
            if url: p_urls += url
    
    urls.append(p_urls)

print(f"[{Fore.GREEN + Style.BRIGHT}✓{Style.RESET_ALL}] Получено {len(urls[0] + urls[1])} URLs\n")
logger.log(LogType.INFO, f"\"Получено {len(urls[0] + urls[1])} URLs\"")

for parser, urls_pack in zip(parsers, urls):
    n = 0

    with concurrent.futures.ThreadPoolExecutor(settings.threads) as executor:
        for variations in executor.map(parser.get_variations, urls_pack):
            if variations:
                products += variations
                n += 1

                if n % 100 == 0: 
                    print(f"[{Fore.CYAN + Style.BRIGHT}i{Style.RESET_ALL}] {parser.category}: Обработано {Style.BRIGHT + str(n) + Style.RESET_ALL} URLs")
                    logger.log(LogType.INFO, f"{parser.category}: Обработано {n} URLs")

        print(f"[{Fore.GREEN + Style.BRIGHT}✓{Style.RESET_ALL}] Получено {len(products)} вариаций\n")

print(f"[{Fore.CYAN + Style.BRIGHT}⧖{Style.RESET_ALL}] Создание CSV...")
create_df(products).to_csv("output/top4football-products.csv", sep=settings.csv_sep, index=False, encoding="utf-8")
create_df(products, True).to_csv("output/top4football.csv", sep=settings.csv_sep, index=False, encoding="utf-8")
