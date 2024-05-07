import json
import pandas as pd 
import logging
import re

from datetime import datetime as dt
from colorthief import ColorThief
from datetime import datetime as dt
from math import ceil
from bs4 import BeautifulSoup
from proxy_client import *
from utils import *

from dataclasses import dataclass


logger = init_logger(
    f"logs/{dt.now().strftime("%Y-%m-%d")}.log", 
    "%(asctime)s %(levelname)s %(message)s",
    logging.ERROR
)

@dataclass
class Product:
    name: str
    url: str
    images: str
    brand: str
    category: str
    price: float
    description: str
    sku: str
    spu: str
    in_stock: int
    origin_color: str
    color: str
    size: str


PER_PAGE = 36
PREFIX = "T4F-"

class Parser:
    BASE = "https://top4football.de"

    def __init__(self, path: str, category: str, proxy_client: ProxyClient) -> None:
        self.path = path
        self.category = category
        self.proxy_client = proxy_client
        
        self.size_re = r"\b(\d+(?:\s?[^\s]))\b"

    @staticmethod
    def n_pages(per_page: int, n_products: int) -> int:
        return ceil(n_products / per_page)
    
    @debug("Ошибка в получении количества товаров", True)
    def get_n_pages(self) -> int:
        return self.n_pages(
            PER_PAGE,
            int(BeautifulSoup(
                self.proxy_client.retry("GET", self.BASE + self.path + f"?priceFrom=10&priceTo=300").text,
                "html.parser"
            ).find("div", { "data-products-count": True }).get("data-products-count"))
        )

    @debug("Ошибка в парсинге URL товаров. Страница: {page}", True)
    def get_urls(self, page: int) -> list[str]:
        url = self.BASE + self.path + f"/page-{page}?priceFrom=10&priceTo=300"
        return list(
            self.BASE + x.get("href")
            for x in BeautifulSoup(
                self.proxy_client.retry("GET", url).text, 
                "html.parser"
            ).find("div", { "id": "product-list" }).find_all("a")
        )
    
    @debug("Ошибка в парсинге товара: {url}: {debug_exc}")
    def get_variations(self, url: str) -> list[Product]:
        v = []
        page = BeautifulSoup(self.proxy_client.retry("GET", url).text, "html.parser")
        if data := json.loads(
            page.find("script", { "type": "application/ld+json" }).text
        ):
            spu = data[0].get("productID")
            name = data[0].get("name")
            images = data[0].get("image")
            brand = data[0].get("brand").get("name")
            if not (description := data[0].get("description").replace("\n", "").strip()):
                description = ""

            if COLORS.get(
                (color := next((i.get("color") for i in data if i.get("color") is not None), None))
            ):
                origin_color = color
                color = COLORS.get(color)
            else:
                origin_color = ""
                color = dom_color_name(
                    *ColorThief(self.proxy_client.retry("GET", images[0], stream=True).raw).get_color(10)
                )

            stock_data = {}
            for i in page.find("div", { "id": "choose-size-list-eu" }).find_all("a"):
                stock_data_raw = i.find_all("div")
                if unicode_size := re.findall(self.size_re, stock_data_raw[1].text):
                    stock_data[str(
                        unicode_to_float(unicode_size[0].strip())
                    )] = stock_data_raw[2].text.strip()

            if stock_data:
                for i in data:
                    size = i.get("size").split(" | ")[0].replace(" EU", "").replace(",", ".")
                    if (stock_string := stock_data.get(size)) and stock_string != "Größe anfragen":
                        match stock_string:
                            case "Auf Lager":
                                in_stock = 10
                            case "":
                                in_stock = 1
                            case _:
                                in_stock = int(re.sub(r"\D", "", stock_string))

                        sku = i.get("sku")
                        product_url = i.get("offers").get("url")
                        price = i.get("offers").get("price")

                        v.append(Product(
                            name,
                            product_url,
                            images,
                            brand,
                            self.category,
                            price,
                            description,
                            sku,
                            spu,
                            in_stock,
                            origin_color,
                            color,
                            size
                        ))

        return v

def create_df(products: list[Product], stocks: bool = False) -> pd.DataFrame:
    if stocks:
        data = {
            "url": [],
            "brand": [],
            "shop_sku": [],
            "newmen_sku": [],
            "in_stock": [],
            "price": []
        }
    else:
        data = {
            "url": [],
            "artikul": [],
            "shop_sku": [],
            "newmen_sku": [],
            "bundle_id": [],
            "product_name": [],
            "producer_size": [],
            "price": [],
            "price_before_discount": [],
            "base_type": [],
            "commercial_type": [],
            "brand": [],
            "origin_color": [],
            "color_rgb": [],
            "color": [],
            "manufacturer": [],
            "main_photo": [],
            "additional_photos": [],
            "number": [],
            "vat": [],
            "ozon_id": [],
            "gtin": [],
            "weight_in_pack": [],
            "pack_width": [],
            "pack_length": [],
            "pack_height": [],
            "images_360": [],
            "note": [],
            "keywords": [],
            "in_stock": [],
            "card_num": [],
            "error": [],
            "warning": [],
            "num_packs": [],
            "origin_name": [],
            "category": [],
            "content_unit": [],
            "net_quantity_content": [],
            "instruction": [],
            "info_sheet": [],
            "product_description": [],
            "non_food_ingredients_description": [],
            "application_description": [],
            "company_address_description": [],
            "care_label_description": [],
            "country_of_origin_description": [],
            "warning_label_description": [],
            "sustainability_description": [],
            "required_fields_description": [],
            "additional_information_description": [],
            "hazard_warnings_description": [],
            "leaflet_description": []
        }

    for i in products:
        if stocks:
            data["url"].append(i.url)
            data["brand"].append(i.brand)
            data["shop_sku"].append(i.sku)
            data["newmen_sku"].append(PREFIX + i.sku)
            data["in_stock"].append(i.in_stock)
            data["price"].append(i.price)
        else:
            name_prefix = "Laufschuhe " if i.category == "беговая обувь" else "Fußballschuhe "

            data["url"].append(i.url)
            data["artikul"].append(i.sku)
            data["shop_sku"].append(i.sku)
            data["newmen_sku"].append(PREFIX + i.sku)
            data["bundle_id"].append(i.spu)
            data["product_name"].append(i.name.replace(name_prefix, ""))
            data["producer_size"].append(i.size)
            data["price"].append(i.price)
            data["price_before_discount"].append("")
            data["base_type"].append("")
            data["commercial_type"].append("")
            data["brand"].append(i.brand)
            data["origin_color"].append(i.origin_color)
            data["color_rgb"].append("")
            data["color"].append(i.color)
            data["manufacturer"].append("")
            data["main_photo"].append(i.images[0])
            data["additional_photos"].append(",".join(i.images[1:]))
            data["number"].append("")
            data["vat"].append("")
            data["ozon_id"].append("")
            data["gtin"].append("")
            data["weight_in_pack"].append("")
            data["pack_width"].append("")
            data["pack_length"].append("")
            data["pack_height"].append("")
            data["images_360"].append("")
            data["note"].append("")
            data["keywords"].append("")
            data["in_stock"].append(i.in_stock)
            data["card_num"].append("")
            data["error"].append("")
            data["warning"].append("")
            data["num_packs"].append("")
            data["origin_name"].append(i.name)
            data["category"].append(i.category)
            data["content_unit"].append("")
            data["net_quantity_content"].append("")
            data["instruction"].append("")
            data["info_sheet"].append("")
            data["product_description"].append(i.description)
            data["non_food_ingredients_description"].append("")
            data["application_description"].append("")
            data["company_address_description"].append("")
            data["care_label_description"].append("")
            data["country_of_origin_description"].append("")
            data["warning_label_description"].append("")
            data["sustainability_description"].append("")
            data["required_fields_description"].append("")
            data["additional_information_description"].append("")
            data["hazard_warnings_description"].append("")
            data["leaflet_description"].append("")

    return pd.DataFrame(data)

