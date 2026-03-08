from __future__ import annotations

from dataclasses import dataclass
from random import Random

PRODUCTS: dict[str, dict[str, float | str]] = {
    "soda": {
        "size": "small",
        "base_daily_demand": 7.0,
        "ideal_price": 1.50,
        "wholesale_price": 0.58,
        "weather_bias": "hot",
    },
    "water": {
        "size": "small",
        "base_daily_demand": 6.0,
        "ideal_price": 1.25,
        "wholesale_price": 0.42,
        "weather_bias": "hot",
    },
    "candy": {
        "size": "small",
        "base_daily_demand": 4.0,
        "ideal_price": 1.25,
        "wholesale_price": 0.35,
        "weather_bias": "neutral",
    },
    "chips": {
        "size": "large",
        "base_daily_demand": 5.0,
        "ideal_price": 2.00,
        "wholesale_price": 0.72,
        "weather_bias": "neutral",
    },
    "sandwich": {
        "size": "large",
        "base_daily_demand": 2.0,
        "ideal_price": 4.50,
        "wholesale_price": 2.20,
        "weather_bias": "cold",
    },
}

SEASON_MULTIPLIERS = {
    "winter": 0.9,
    "spring": 1.0,
    "summer": 1.15,
    "autumn": 1.0,
}

DAY_OF_WEEK_MULTIPLIERS = {
    "monday": 0.95,
    "tuesday": 1.0,
    "wednesday": 1.0,
    "thursday": 1.0,
    "friday": 1.1,
    "saturday": 1.2,
    "sunday": 0.85,
}

WEATHER_MULTIPLIERS = {
    "sunny": 1.15,
    "cloudy": 1.0,
    "rainy": 0.85,
    "foggy": 0.9,
    "heatwave": 1.25,
}

WEATHER_SEQUENCE = ["sunny", "cloudy", "rainy", "sunny", "foggy", "cloudy", "sunny"]
DAY_NAMES = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


@dataclass(slots=True)
class DailySalesResult:
    units_sold: dict[str, int]
    revenue: float
    debug: dict[str, float]


def season_for_day(day_index: int) -> str:
    day_of_year = ((day_index - 1) % 365) + 1
    if day_of_year <= 79:
        return "winter"
    if day_of_year <= 171:
        return "spring"
    if day_of_year <= 265:
        return "summer"
    if day_of_year <= 354:
        return "autumn"
    return "winter"


def day_of_week_for_day(day_index: int) -> str:
    return DAY_NAMES[(day_index - 1) % len(DAY_NAMES)]


def weather_for_day(day_index: int) -> str:
    return WEATHER_SEQUENCE[(day_index - 1) % len(WEATHER_SEQUENCE)]


def _weather_bias_multiplier(product: str, weather: str) -> float:
    bias = str(PRODUCTS.get(product, {}).get("weather_bias", "neutral"))
    if bias == "hot" and weather in {"sunny", "heatwave"}:
        return 1.1
    if bias == "cold" and weather in {"rainy", "foggy"}:
        return 1.08
    return 1.0


def compute_daily_sales(
    products: list[str],
    prices: dict[str, float],
    weather: str,
    season: str,
    day_of_week: str,
    inventory: dict[str, int] | None = None,
    seed: int | None = None,
) -> DailySalesResult:
    rng = Random(seed)
    choice_multiplier = 1.0 + min(max(len(products) - 1, 0), 5) * 0.05
    weather_multiplier = WEATHER_MULTIPLIERS.get(weather, 1.0)
    season_multiplier = SEASON_MULTIPLIERS.get(season, 1.0)
    dow_multiplier = DAY_OF_WEEK_MULTIPLIERS.get(day_of_week, 1.0)
    inventory = inventory or {}

    units_sold: dict[str, int] = {}
    revenue = 0.0
    for product in products:
        catalog = PRODUCTS.get(product, {})
        base_demand = float(catalog.get("base_daily_demand", 1.0))
        ideal_price = float(
            catalog.get("ideal_price", max(prices.get(product, 1.0), 0.01))
        )
        price = float(prices.get(product, ideal_price))
        price_multiplier = max(
            0.15, 1.0 - ((price - ideal_price) / max(ideal_price, 0.01)) * 0.45
        )
        noise_multiplier = 0.9 + (rng.random() * 0.2)
        expected_units = (
            base_demand
            * choice_multiplier
            * weather_multiplier
            * season_multiplier
            * dow_multiplier
            * price_multiplier
            * _weather_bias_multiplier(product, weather)
            * noise_multiplier
        )
        sold = max(0, int(round(expected_units)))
        if product in inventory:
            sold = min(sold, inventory[product])
        units_sold[product] = sold
        revenue += sold * price

    debug = {
        "choice_multiplier": round(choice_multiplier, 3),
        "weather_multiplier": round(weather_multiplier, 3),
        "season_multiplier": round(season_multiplier, 3),
        "day_of_week_multiplier": round(dow_multiplier, 3),
    }
    return DailySalesResult(
        units_sold=units_sold, revenue=round(revenue, 2), debug=debug
    )
