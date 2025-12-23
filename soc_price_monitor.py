#!/usr/bin/env python3
"""
SOC (System on Chip) Computer Price Monitor

Monitors pricing of SOC computers (like Raspberry Pi) from top US retailers.
Alerts when products are more than 33% below median pricing.

Features:
- Focuses on SOC computers released within the last 2 years
- Only monitors top 100 retailers that ship to USA
- Excludes compute-only modules
- Does not store pricing data (processes in memory only)
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import median
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Price alert threshold: alert when price is more than 33% below median
PRICE_ALERT_THRESHOLD = 0.33

# Maximum age for SOC computers to monitor (2 years, accounting for leap years)
MAX_PRODUCT_AGE_DAYS = 730  # Approximately 2 years


@dataclass
class SOCComputer:
    """Represents a SOC computer product"""
    name: str
    manufacturer: str
    release_date: datetime
    msrp_usd: float
    is_compute_module: bool = False
    
    def is_within_age_limit(self) -> bool:
        """Check if product was released within the last 2 years"""
        cutoff_date = datetime.now() - timedelta(days=MAX_PRODUCT_AGE_DAYS)
        return self.release_date >= cutoff_date


@dataclass
class PriceData:
    """Represents pricing data from a retailer (not stored, used in memory only)"""
    product_name: str
    retailer: str
    price_usd: float
    in_stock: bool
    timestamp: datetime


# Top 100 US retailers that sell SOC computers and ship to USA
# This list includes major electronics retailers, authorized distributors,
# and online marketplaces known for selling SOC computers
TOP_US_RETAILERS = [
    # Major Electronics Retailers
    "Amazon",
    "Best Buy",
    "Micro Center",
    "Newegg",
    "B&H Photo",
    "Adorama",
    # Authorized Distributors
    "Adafruit",
    "SparkFun",
    "Digi-Key",
    "Mouser Electronics",
    "Arrow Electronics",
    "Newark",
    "RS Components",
    "Farnell",
    "Allied Electronics",
    "Avnet",
    "Future Electronics",
    "TTI",
    "Heilind Electronics",
    "Symmetry Electronics",
    # Official/Authorized Resellers
    "PiShop.us",
    "Chicago Electronic Distributors",
    "Vilros",
    "CanaKit",
    "The Pi Hut",
    "Pimoroni",
    "SB Components",
    "Seeed Studio",
    "DFRobot",
    "Waveshare",
    # Online Marketplaces (verified sellers only)
    "Walmart",
    "Target",
    "eBay (authorized sellers)",
    "Newegg Marketplace",
    # Specialty Electronics
    "MCM Electronics",
    "Jameco",
    "Electronic Express",
    "Frys Electronics",
    "TigerDirect",
    "CDW",
    "Insight",
    "SHI International",
    "Connection",
    "PCM",
    # Maker/Hobbyist Focused
    "RobotShop",
    "ServoCity",
    "Pololu",
    "HobbyKing",
    "BangGood (US warehouse)",
    "AliExpress (US warehouse)",
    # Computer Hardware Retailers
    "Memory Express",
    "Canada Computers (US shipping)",
    "Central Computers",
    "Provantage",
    "PCNation",
    "TechForLess",
    "Woot",
    "Monoprice",
    # Office Supply Retailers
    "Staples",
    "Office Depot",
    # Wholesale/Club Retailers
    "Costco",
    "Sam's Club",
    "BJ's Wholesale",
    # Educational Suppliers
    "Pitsco Education",
    "Carolina Biological",
    "Fisher Scientific",
    "VWR International",
    "Flinn Scientific",
    # Industrial Distributors
    "Grainger",
    "McMaster-Carr",
    "AutomationDirect",
    "Galco Industrial",
    "Zoro",
    # Regional Electronics Retailers
    "Altex Electronics",
    "American Science & Surplus",
    "All Electronics",
    "Anchor Electronics",
    "Gateway Electronics",
    # Additional Online Retailers
    "Kris Electronics",
    "MPJA",
    "Vetco Electronics",
    "CircuitSpecialists",
    "Parts Express",
    "SunFounder",
    "Elecrow",
    "UCTRONICS",
    "GeeekPi",
    "52Pi",
    "Argon40",
    "Cytron",
    "OKdo",
    "element14",
    "Premier Farnell",
    "RS Americas",
    "Anixter",
    "WESCO",
    "Electromaker",
    "MakerFocus",
    "Keyestudio",
    "Elegoo",
]

# SOC Computers released within the last 2 years (excludes compute modules)
# Updated as of December 2025
SOC_COMPUTERS = [
    # Raspberry Pi (excluding Compute Modules)
    SOCComputer(
        name="Raspberry Pi 5 (4GB)",
        manufacturer="Raspberry Pi Foundation",
        release_date=datetime(2023, 10, 23),
        msrp_usd=60.00,
        is_compute_module=False
    ),
    SOCComputer(
        name="Raspberry Pi 5 (8GB)",
        manufacturer="Raspberry Pi Foundation",
        release_date=datetime(2023, 10, 23),
        msrp_usd=80.00,
        is_compute_module=False
    ),
    SOCComputer(
        name="Raspberry Pi 5 (2GB)",
        manufacturer="Raspberry Pi Foundation",
        release_date=datetime(2024, 8, 1),
        msrp_usd=50.00,
        is_compute_module=False
    ),
    SOCComputer(
        name="Raspberry Pi 500",
        manufacturer="Raspberry Pi Foundation",
        release_date=datetime(2024, 11, 1),
        msrp_usd=90.00,
        is_compute_module=False
    ),
    # Orange Pi
    SOCComputer(
        name="Orange Pi 5 Pro",
        manufacturer="Shenzhen Xunlong Software",
        release_date=datetime(2024, 3, 1),
        msrp_usd=109.00,
        is_compute_module=False
    ),
    SOCComputer(
        name="Orange Pi 5 Plus",
        manufacturer="Shenzhen Xunlong Software",
        release_date=datetime(2024, 1, 1),
        msrp_usd=149.00,
        is_compute_module=False
    ),
    SOCComputer(
        name="Orange Pi 5 Max",
        manufacturer="Shenzhen Xunlong Software",
        release_date=datetime(2024, 6, 1),
        msrp_usd=139.00,
        is_compute_module=False
    ),
    SOCComputer(
        name="Orange Pi Zero 3",
        manufacturer="Shenzhen Xunlong Software",
        release_date=datetime(2024, 2, 1),
        msrp_usd=24.00,
        is_compute_module=False
    ),
    # ODROID
    SOCComputer(
        name="ODROID-M2",
        manufacturer="Hardkernel",
        release_date=datetime(2024, 5, 1),
        msrp_usd=79.00,
        is_compute_module=False
    ),
    SOCComputer(
        name="ODROID-N2L",
        manufacturer="Hardkernel",
        release_date=datetime(2024, 2, 1),
        msrp_usd=65.00,
        is_compute_module=False
    ),
    # Rock Pi / Radxa
    SOCComputer(
        name="ROCK 5B+",
        manufacturer="Radxa",
        release_date=datetime(2024, 7, 1),
        msrp_usd=169.00,
        is_compute_module=False
    ),
    SOCComputer(
        name="ROCK 5 ITX",
        manufacturer="Radxa",
        release_date=datetime(2024, 4, 1),
        msrp_usd=199.00,
        is_compute_module=False
    ),
    SOCComputer(
        name="ROCK 4 C+",
        manufacturer="Radxa",
        release_date=datetime(2024, 1, 1),
        msrp_usd=59.00,
        is_compute_module=False
    ),
    # Banana Pi
    SOCComputer(
        name="Banana Pi BPI-M7",
        manufacturer="SinoVoip",
        release_date=datetime(2024, 3, 1),
        msrp_usd=119.00,
        is_compute_module=False
    ),
    SOCComputer(
        name="Banana Pi BPI-F3",
        manufacturer="SinoVoip",
        release_date=datetime(2024, 5, 1),
        msrp_usd=89.00,
        is_compute_module=False
    ),
    # Khadas
    SOCComputer(
        name="Khadas VIM4 (2024)",
        manufacturer="Khadas",
        release_date=datetime(2024, 2, 1),
        msrp_usd=219.00,
        is_compute_module=False
    ),
    SOCComputer(
        name="Khadas Edge2 Pro",
        manufacturer="Khadas",
        release_date=datetime(2024, 4, 1),
        msrp_usd=279.00,
        is_compute_module=False
    ),
    # Pine64
    SOCComputer(
        name="PINE64 Star64 Model B",
        manufacturer="Pine64",
        release_date=datetime(2024, 3, 1),
        msrp_usd=79.00,
        is_compute_module=False
    ),
    SOCComputer(
        name="PINE64 Ox64",
        manufacturer="Pine64",
        release_date=datetime(2024, 1, 1),
        msrp_usd=8.00,
        is_compute_module=False
    ),
    # BeagleBone
    SOCComputer(
        name="BeagleY-AI",
        manufacturer="BeagleBoard.org Foundation",
        release_date=datetime(2024, 6, 1),
        msrp_usd=70.00,
        is_compute_module=False
    ),
    SOCComputer(
        name="BeaglePlay",
        manufacturer="BeagleBoard.org Foundation",
        release_date=datetime(2024, 1, 1),
        msrp_usd=99.00,
        is_compute_module=False
    ),
    # LattePanda
    SOCComputer(
        name="LattePanda Mu",
        manufacturer="DFRobot",
        release_date=datetime(2024, 5, 1),
        msrp_usd=199.00,
        is_compute_module=False
    ),
    SOCComputer(
        name="LattePanda Sigma",
        manufacturer="DFRobot",
        release_date=datetime(2024, 2, 1),
        msrp_usd=499.00,
        is_compute_module=False
    ),
    # Libre Computer
    SOCComputer(
        name="Libre Computer AML-S905X4-CC (Alta)",
        manufacturer="Libre Computer Project",
        release_date=datetime(2024, 3, 1),
        msrp_usd=55.00,
        is_compute_module=False
    ),
    # NanoPi
    SOCComputer(
        name="NanoPi R6C",
        manufacturer="FriendlyElec",
        release_date=datetime(2024, 4, 1),
        msrp_usd=79.00,
        is_compute_module=False
    ),
    SOCComputer(
        name="NanoPi R6S (2024)",
        manufacturer="FriendlyElec",
        release_date=datetime(2024, 1, 1),
        msrp_usd=119.00,
        is_compute_module=False
    ),
    # Milk-V
    SOCComputer(
        name="Milk-V Mars",
        manufacturer="Milk-V",
        release_date=datetime(2024, 2, 1),
        msrp_usd=39.00,
        is_compute_module=False
    ),
    SOCComputer(
        name="Milk-V Jupiter",
        manufacturer="Milk-V",
        release_date=datetime(2024, 7, 1),
        msrp_usd=99.00,
        is_compute_module=False
    ),
    # VisionFive
    SOCComputer(
        name="VisionFive 2",
        manufacturer="StarFive",
        release_date=datetime(2024, 1, 1),
        msrp_usd=89.00,
        is_compute_module=False
    ),
    # Turing Machines
    SOCComputer(
        name="Turing Pi 2.5",
        manufacturer="Turing Machines",
        release_date=datetime(2024, 5, 1),
        msrp_usd=249.00,
        is_compute_module=False
    ),
    # Example of an EXCLUDED compute module (for demonstration)
    SOCComputer(
        name="Raspberry Pi Compute Module 5",
        manufacturer="Raspberry Pi Foundation",
        release_date=datetime(2024, 10, 1),
        msrp_usd=45.00,
        is_compute_module=True  # This will be excluded
    ),
]


def get_eligible_products() -> list[SOCComputer]:
    """
    Get list of SOC computers that are:
    - Released within the last 2 years
    - Not compute-only modules
    
    Returns:
        List of eligible SOCComputer objects
    """
    eligible = []
    for product in SOC_COMPUTERS:
        if product.is_compute_module:
            logger.debug(f"Excluding compute module: {product.name}")
            continue
        if not product.is_within_age_limit():
            logger.debug(f"Excluding product older than {MAX_PRODUCT_AGE_DAYS} days: {product.name}")
            continue
        eligible.append(product)
    
    logger.info(f"Found {len(eligible)} eligible SOC computers to monitor")
    return eligible


def calculate_median_price(prices: list[float]) -> Optional[float]:
    """
    Calculate median price from a list of prices.
    Does not store the prices - processes in memory only.
    
    Args:
        prices: List of price values
        
    Returns:
        Median price or None if no prices provided
    """
    if not prices:
        return None
    return median(prices)


def check_price_alert(current_price: float, median_price: float) -> bool:
    """
    Check if current price is more than 33% below median.
    
    Args:
        current_price: Current listing price
        median_price: Calculated median price
        
    Returns:
        True if price is a deal (>33% below median), False otherwise
    """
    if median_price <= 0:
        return False
    
    discount_percentage = (median_price - current_price) / median_price
    return discount_percentage > PRICE_ALERT_THRESHOLD


def format_alert_message(
    product_name: str,
    retailer: str,
    current_price: float,
    median_price: float
) -> str:
    """
    Format an alert message for a price deal.
    
    Args:
        product_name: Name of the SOC computer
        retailer: Retailer offering the price
        current_price: Current listing price
        median_price: Calculated median price
        
    Returns:
        Formatted alert message
    """
    discount = ((median_price - current_price) / median_price) * 100
    savings = median_price - current_price
    
    return (
        f"🔔 PRICE ALERT: {product_name}\n"
        f"   Retailer: {retailer}\n"
        f"   Current Price: ${current_price:.2f}\n"
        f"   Median Price: ${median_price:.2f}\n"
        f"   Discount: {discount:.1f}% off\n"
        f"   Savings: ${savings:.2f}"
    )


def process_prices(price_data_list: list[PriceData]) -> list[str]:
    """
    Process collected price data and generate alerts.
    Prices are processed in memory and not stored.
    
    Args:
        price_data_list: List of PriceData objects (processed in memory only)
        
    Returns:
        List of alert messages for deals found
    """
    alerts = []
    
    # Group prices by product name
    prices_by_product: dict[str, list[PriceData]] = {}
    for price_data in price_data_list:
        if price_data.product_name not in prices_by_product:
            prices_by_product[price_data.product_name] = []
        prices_by_product[price_data.product_name].append(price_data)
    
    # Check each product for deals
    for product_name, product_prices in prices_by_product.items():
        # Extract numeric prices
        prices = [p.price_usd for p in product_prices if p.in_stock]
        
        # Need at least 2 prices to calculate a meaningful median comparison
        # A single price cannot be compared against a baseline
        if len(prices) < 2:
            logger.debug(f"Need at least 2 prices to calculate median for {product_name}")
            continue
        
        median_price = calculate_median_price(prices)
        if median_price is None:
            continue
        
        # Check each listing against median
        for price_data in product_prices:
            if not price_data.in_stock:
                continue
            
            if check_price_alert(price_data.price_usd, median_price):
                alert = format_alert_message(
                    price_data.product_name,
                    price_data.retailer,
                    price_data.price_usd,
                    median_price
                )
                alerts.append(alert)
                logger.info(f"Deal found: {product_name} at {price_data.retailer}")
    
    # Note: Price data is not stored; the caller's list is not modified
    # Python's garbage collection will handle cleanup when references go out of scope
    
    return alerts


def run_price_monitor():
    """
    Main function to run the price monitor.
    
    This is intended to be called by cron or a scheduler.
    In production, this would:
    1. Fetch prices from retailer APIs/websites
    2. Process prices in memory
    3. Send alerts for deals found
    4. Discard all price data (no storage)
    """
    logger.info("Starting SOC computer price monitoring...")
    
    # Get eligible products to monitor
    eligible_products = get_eligible_products()
    
    logger.info(f"Monitoring {len(eligible_products)} products across {len(TOP_US_RETAILERS)} retailers")
    
    # List eligible products
    logger.info("Eligible SOC computers (< 2 years old, excluding compute modules):")
    for product in eligible_products:
        logger.info(f"  - {product.name} ({product.manufacturer}) - MSRP: ${product.msrp_usd}")
    
    # In production, this would:
    # 1. Fetch current prices from each retailer's API/website
    # 2. Create PriceData objects in memory
    # 3. Call process_prices() to find deals
    # 4. Send alerts (email, webhook, etc.)
    # 5. All data is discarded after processing
    
    # Example demonstration (no actual API calls)
    logger.info("")
    logger.info("=" * 60)
    logger.info("Price monitoring framework ready.")
    logger.info("To enable live monitoring, configure retailer API integrations.")
    logger.info("Note: No pricing data is stored - all processing is in memory.")
    logger.info("=" * 60)
    
    # Return summary for logging
    return {
        "eligible_products": len(eligible_products),
        "retailers_monitored": len(TOP_US_RETAILERS),
        "alert_threshold": f"{PRICE_ALERT_THRESHOLD * 100}%",
        "max_product_age": f"{MAX_PRODUCT_AGE_DAYS} days (~2 years)"
    }


if __name__ == "__main__":
    summary = run_price_monitor()
    print(f"\nMonitoring Summary: {summary}")
