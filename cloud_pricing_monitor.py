#!/usr/bin/env python3
"""
Cloud GPU/CPU Pricing Monitor

Monitors pricing of GPU and CPU instances at top cloud computing providers.
Checks prices at configured intervals and can auto-launch instances when
prices fall below user-defined thresholds.

Note: This module uses simulated pricing data for demonstration purposes.
In production, replace the simulated fetchers with actual API calls to
cloud providers using their respective SDKs (boto3 for AWS, google-cloud
for GCP, azure-sdk for Azure, etc.).
"""

import asyncio
import logging
import random
from datetime import datetime
from typing import Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class InstanceType(Enum):
    """Types of cloud instances"""
    GPU = "gpu"
    CPU = "cpu"


class CloudProvider(Enum):
    """Supported cloud providers"""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    DIGITAL_OCEAN = "digital_ocean"
    LINODE = "linode"
    VULTR = "vultr"
    OVH = "ovh"
    HETZNER = "hetzner"
    ORACLE = "oracle"
    IBM = "ibm"


@dataclass
class InstancePrice:
    """Represents pricing for a cloud instance"""
    provider: CloudProvider
    instance_type: InstanceType
    instance_name: str
    price_per_hour: float
    currency: str = "USD"
    region: str = "us-east-1"
    specs: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PriceThreshold:
    """User-defined price threshold for auto-launch"""
    instance_type: InstanceType
    max_price: float
    preferred_providers: list = field(default_factory=list)
    auto_launch: bool = False
    min_specs: dict = field(default_factory=dict)


@dataclass
class MonitorStatus:
    """Status of the pricing monitor"""
    is_running: bool = False
    last_check: Optional[datetime] = None
    check_interval_seconds: int = 30
    total_checks: int = 0
    launches_triggered: int = 0


class CloudPricingMonitor:
    """
    Monitors cloud pricing and can trigger instance launches based on thresholds.
    
    This implementation uses simulated pricing data for demonstration.
    In production, implement actual API calls to each cloud provider.
    """
    
    def __init__(self, check_interval: int = 30):
        """
        Initialize the pricing monitor.
        
        Args:
            check_interval: Seconds between price checks (default: 30)
        """
        self.check_interval = check_interval
        self.status = MonitorStatus(check_interval_seconds=check_interval)
        self.current_prices: list[InstancePrice] = []
        self.thresholds: dict[InstanceType, PriceThreshold] = {}
        self._monitor_task: Optional[asyncio.Task] = None
        self._callbacks: list[Callable] = []
        
        # Base prices for simulation (will fluctuate)
        self._base_prices = self._initialize_base_prices()
    
    def _initialize_base_prices(self) -> dict:
        """Initialize base prices for simulation"""
        return {
            CloudProvider.AWS: {
                InstanceType.GPU: {"name": "p3.2xlarge", "base": 3.06, "specs": {"gpu": "Tesla V100", "vcpu": 8, "ram_gb": 61}},
                InstanceType.CPU: {"name": "c5.4xlarge", "base": 0.68, "specs": {"vcpu": 16, "ram_gb": 32}},
            },
            CloudProvider.GCP: {
                InstanceType.GPU: {"name": "n1-standard-8-nvidia-tesla-v100", "base": 2.95, "specs": {"gpu": "Tesla V100", "vcpu": 8, "ram_gb": 30}},
                InstanceType.CPU: {"name": "c2-standard-16", "base": 0.75, "specs": {"vcpu": 16, "ram_gb": 64}},
            },
            CloudProvider.AZURE: {
                InstanceType.GPU: {"name": "NC6s_v3", "base": 3.06, "specs": {"gpu": "Tesla V100", "vcpu": 6, "ram_gb": 112}},
                InstanceType.CPU: {"name": "F16s_v2", "base": 0.68, "specs": {"vcpu": 16, "ram_gb": 32}},
            },
            CloudProvider.DIGITAL_OCEAN: {
                InstanceType.GPU: {"name": "gpu-h100x1-80gb", "base": 2.85, "specs": {"gpu": "H100", "vcpu": 20, "ram_gb": 240}},
                InstanceType.CPU: {"name": "c-16", "base": 0.48, "specs": {"vcpu": 16, "ram_gb": 32}},
            },
            CloudProvider.LINODE: {
                InstanceType.GPU: {"name": "gpu-rtx6000-1", "base": 1.50, "specs": {"gpu": "RTX 6000", "vcpu": 8, "ram_gb": 64}},
                InstanceType.CPU: {"name": "dedicated-16", "base": 0.36, "specs": {"vcpu": 16, "ram_gb": 32}},
            },
            CloudProvider.VULTR: {
                InstanceType.GPU: {"name": "vgpu-a100-1", "base": 2.60, "specs": {"gpu": "A100", "vcpu": 12, "ram_gb": 120}},
                InstanceType.CPU: {"name": "vhp-16c-32gb", "base": 0.29, "specs": {"vcpu": 16, "ram_gb": 32}},
            },
            CloudProvider.OVH: {
                InstanceType.GPU: {"name": "gpu-t1-45", "base": 2.20, "specs": {"gpu": "Tesla T4", "vcpu": 45, "ram_gb": 180}},
                InstanceType.CPU: {"name": "c2-30", "base": 0.25, "specs": {"vcpu": 8, "ram_gb": 30}},
            },
            CloudProvider.HETZNER: {
                InstanceType.GPU: {"name": "gpu-server", "base": 1.80, "specs": {"gpu": "RTX A4000", "vcpu": 12, "ram_gb": 64}},
                InstanceType.CPU: {"name": "ccx33", "base": 0.18, "specs": {"vcpu": 8, "ram_gb": 32}},
            },
            CloudProvider.ORACLE: {
                InstanceType.GPU: {"name": "GPU.A10.1", "base": 2.00, "specs": {"gpu": "A10", "vcpu": 15, "ram_gb": 240}},
                InstanceType.CPU: {"name": "VM.Standard.E4.Flex", "base": 0.03, "specs": {"vcpu": 1, "ram_gb": 16}},
            },
            CloudProvider.IBM: {
                InstanceType.GPU: {"name": "gx2-32x256x2v100", "base": 3.20, "specs": {"gpu": "Tesla V100 x2", "vcpu": 32, "ram_gb": 256}},
                InstanceType.CPU: {"name": "bx2-16x64", "base": 0.77, "specs": {"vcpu": 16, "ram_gb": 64}},
            },
        }
    
    def _simulate_price(self, base_price: float) -> float:
        """
        Simulate price fluctuation for demonstration.
        
        In production, replace with actual API calls.
        Simulates ±15% price variation to mimic spot/preemptible pricing.
        """
        variation = random.uniform(-0.15, 0.15)
        return round(base_price * (1 + variation), 4)
    
    async def fetch_all_prices(self) -> list[InstancePrice]:
        """
        Fetch current prices from all providers.
        
        Note: This uses simulated data. In production, implement actual
        API calls to each provider.
        """
        prices = []
        timestamp = datetime.utcnow()
        
        for provider in CloudProvider:
            for instance_type in InstanceType:
                try:
                    price_info = self._base_prices[provider][instance_type]
                    simulated_price = self._simulate_price(price_info["base"])
                    
                    prices.append(InstancePrice(
                        provider=provider,
                        instance_type=instance_type,
                        instance_name=price_info["name"],
                        price_per_hour=simulated_price,
                        specs=price_info["specs"],
                        timestamp=timestamp
                    ))
                except KeyError:
                    logger.warning(f"No price data for {provider.value} {instance_type.value}")
        
        self.current_prices = prices
        return prices
    
    def get_prices_by_type(self, instance_type: InstanceType) -> list[InstancePrice]:
        """Get current prices filtered by instance type"""
        return [p for p in self.current_prices if p.instance_type == instance_type]
    
    def get_cheapest(self, instance_type: InstanceType) -> Optional[InstancePrice]:
        """Get the cheapest instance of a given type"""
        prices = self.get_prices_by_type(instance_type)
        if not prices:
            return None
        return min(prices, key=lambda p: p.price_per_hour)
    
    def set_threshold(self, threshold: PriceThreshold) -> None:
        """Set a price threshold for auto-launch"""
        self.thresholds[threshold.instance_type] = threshold
        logger.info(f"Set threshold for {threshold.instance_type.value}: ${threshold.max_price}/hr")
    
    def remove_threshold(self, instance_type: InstanceType) -> None:
        """Remove a price threshold"""
        if instance_type in self.thresholds:
            del self.thresholds[instance_type]
            logger.info(f"Removed threshold for {instance_type.value}")
    
    def check_thresholds(self) -> list[InstancePrice]:
        """Check if any prices are below thresholds"""
        matches = []
        
        for instance_type, threshold in self.thresholds.items():
            prices = self.get_prices_by_type(instance_type)
            
            for price in prices:
                # Check if price is below threshold
                if price.price_per_hour <= threshold.max_price:
                    # Check provider preference if specified
                    if threshold.preferred_providers:
                        if price.provider not in threshold.preferred_providers:
                            continue
                    matches.append(price)
        
        return matches
    
    async def launch_instance(self, price: InstancePrice) -> dict[str, Any]:
        """
        Launch a cloud instance.
        
        Note: This is a simulation. In production, implement actual
        instance launch using provider SDKs.
        
        Args:
            price: The InstancePrice object for the instance to launch
            
        Returns:
            Dict with launch status and details
        """
        logger.info(f"Launching instance: {price.provider.value} {price.instance_name}")
        
        # Simulate launch delay
        await asyncio.sleep(0.5)
        
        # In production, use provider SDKs:
        # - AWS: boto3.client('ec2').run_instances()
        # - GCP: google.cloud.compute_v1.InstancesClient().insert()
        # - Azure: azure.mgmt.compute.ComputeManagementClient().virtual_machines.begin_create_or_update()
        # etc.
        
        result = {
            "success": True,
            "provider": price.provider.value,
            "instance_name": price.instance_name,
            "instance_type": price.instance_type.value,
            "price_per_hour": price.price_per_hour,
            "region": price.region,
            "instance_id": f"sim-{price.provider.value}-{random.randint(10000, 99999)}",
            "message": "Instance launch simulated successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.status.launches_triggered += 1
        
        # Notify callbacks
        for callback in self._callbacks:
            try:
                await callback("launch", result)
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        return result
    
    def add_callback(self, callback: Callable) -> None:
        """Add a callback for monitor events"""
        self._callbacks.append(callback)
    
    async def _monitor_loop(self) -> None:
        """Internal monitoring loop"""
        while self.status.is_running:
            try:
                # Fetch latest prices
                await self.fetch_all_prices()
                self.status.last_check = datetime.utcnow()
                self.status.total_checks += 1
                
                # Check thresholds
                matches = self.check_thresholds()
                
                # Notify callbacks about price update
                for callback in self._callbacks:
                    try:
                        await callback("prices_updated", {
                            "prices": [self._price_to_dict(p) for p in self.current_prices],
                            "matches": [self._price_to_dict(p) for p in matches]
                        })
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
                
                # Auto-launch if enabled and matches found
                for price in matches:
                    threshold = self.thresholds.get(price.instance_type)
                    if threshold and threshold.auto_launch:
                        logger.info(f"Auto-launching {price.provider.value} {price.instance_name} at ${price.price_per_hour}/hr")
                        await self.launch_instance(price)
                        # Disable auto-launch after first launch to prevent multiple launches
                        threshold.auto_launch = False
                
                logger.debug(f"Price check #{self.status.total_checks} completed")
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    def _price_to_dict(self, price: InstancePrice) -> dict:
        """Convert InstancePrice to dictionary"""
        return {
            "provider": price.provider.value,
            "instance_type": price.instance_type.value,
            "instance_name": price.instance_name,
            "price_per_hour": price.price_per_hour,
            "currency": price.currency,
            "region": price.region,
            "specs": price.specs,
            "timestamp": price.timestamp.isoformat()
        }
    
    async def start(self) -> None:
        """Start the pricing monitor"""
        if self.status.is_running:
            logger.warning("Monitor is already running")
            return
        
        self.status.is_running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Pricing monitor started (interval: {self.check_interval}s)")
    
    async def stop(self) -> None:
        """Stop the pricing monitor"""
        self.status.is_running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
        logger.info("Pricing monitor stopped")
    
    def get_status(self) -> dict:
        """Get current monitor status"""
        return {
            "is_running": self.status.is_running,
            "last_check": self.status.last_check.isoformat() if self.status.last_check else None,
            "check_interval_seconds": self.status.check_interval_seconds,
            "total_checks": self.status.total_checks,
            "launches_triggered": self.status.launches_triggered,
            "active_thresholds": {
                k.value: {
                    "max_price": v.max_price,
                    "auto_launch": v.auto_launch,
                    "preferred_providers": [p.value for p in v.preferred_providers] if v.preferred_providers else []
                }
                for k, v in self.thresholds.items()
            }
        }
    
    def get_all_prices_dict(self) -> list[dict]:
        """Get all current prices as dictionaries"""
        return [self._price_to_dict(p) for p in self.current_prices]


# Global monitor instance
pricing_monitor: Optional[CloudPricingMonitor] = None


def get_monitor() -> CloudPricingMonitor:
    """Get or create the global pricing monitor instance"""
    global pricing_monitor
    if pricing_monitor is None:
        pricing_monitor = CloudPricingMonitor()
    return pricing_monitor
