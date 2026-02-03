#!/usr/bin/env python3
"""
gNMI Collector - Network Telemetry Collection Tool

This collector uses pygnmi to subscribe to gNMI telemetry data from network devices.
Supports multiple platforms (cEOS, SONiC) with configurable paths for interface,
LLDP, and ARP data collection.
"""

import asyncio
import yaml
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from pygnmi.client import gNMIclient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GNMICollector:
    """Collector for gNMI telemetry data from network devices."""
    
    def __init__(self, config_dir: str = "configs"):
        """
        Initialize the gNMI collector.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.devices = []
        self.platform_paths = {}
        self.subscription_config = {}
        
    def load_config(self):
        """Load device and path configurations from YAML files."""
        # Load device configuration
        devices_file = self.config_dir / "devices.yaml"
        if not devices_file.exists():
            raise FileNotFoundError(f"Device config not found: {devices_file}")
            
        with open(devices_file, 'r') as f:
            config = yaml.safe_load(f)
            self.devices = config.get('devices', [])
            self.subscription_config = config.get('subscription', {})
            
        logger.info(f"Loaded {len(self.devices)} device(s) from configuration")
        
        # Load platform-specific path configurations
        for device in self.devices:
            platform = device.get('platform')
            if platform and platform not in self.platform_paths:
                paths_file = self.config_dir / f"paths_{platform}.yaml"
                if paths_file.exists():
                    with open(paths_file, 'r') as f:
                        paths_config = yaml.safe_load(f)
                        self.platform_paths[platform] = paths_config.get('paths', {})
                    logger.info(f"Loaded paths for platform: {platform}")
                else:
                    logger.warning(f"Path config not found for platform {platform}: {paths_file}")
    
    def get_subscription_paths(self, platform: str) -> List[str]:
        """
        Get all subscription paths for a platform.
        
        Args:
            platform: Platform name (e.g., 'ceos', 'sonic')
            
        Returns:
            List of gNMI paths to subscribe to
        """
        paths = []
        platform_config = self.platform_paths.get(platform, {})
        
        # Combine all paths from interface, lldp, and arp
        for category in ['interface', 'lldp', 'arp']:
            category_paths = platform_config.get(category, [])
            paths.extend(category_paths)
            
        return paths
    
    async def handle_telemetry_update(self, device_name: str, entry: Dict[str, Any]):
        """
        Handle incoming telemetry update from device.
        
        Args:
            device_name: Name of the device
            entry: Telemetry data entry
        """
        timestamp = datetime.now().isoformat()
        
        # Log the telemetry data
        logger.info(f"[{device_name}] Telemetry Update at {timestamp}")
        logger.info(f"[{device_name}] Path: {entry.get('path', 'N/A')}")
        logger.info(f"[{device_name}] Data: {json.dumps(entry.get('val', {}), indent=2)}")
        
        # Here you can add your custom processing logic:
        # - Store to database
        # - Send to time-series database (InfluxDB, Prometheus, etc.)
        # - Process and analyze the data
        # - Trigger alerts based on thresholds
        
    async def subscribe_device(self, device: Dict[str, Any]):
        """
        Subscribe to gNMI telemetry for a single device.
        
        Args:
            device: Device configuration dictionary
        """
        device_name = device.get('name')
        platform = device.get('platform')
        
        logger.info(f"Starting subscription for device: {device_name}")
        
        # Get paths for this device's platform
        paths = self.get_subscription_paths(platform)
        if not paths:
            logger.warning(f"No paths configured for device {device_name} (platform: {platform})")
            return
            
        logger.info(f"Subscribing to {len(paths)} path(s) on {device_name}")
        
        # Prepare subscription list
        subscribe_list = []
        for path in paths:
            subscribe_list.append({
                'path': path,
                'mode': self.subscription_config.get('mode', 'STREAM'),
                'sample_interval': self.subscription_config.get('sample_interval', 10) * 1000000000  # Convert to nanoseconds
            })
        
        try:
            # Create gNMI client
            client = gNMIclient(
                target=(device.get('host'), device.get('port')),
                username=device.get('username'),
                password=device.get('password'),
                insecure=device.get('insecure', True),
                skip_verify=device.get('skip_verify', True)
            )
            
            # Connect to device
            logger.info(f"Connecting to {device_name} at {device.get('host')}:{device.get('port')}")
            client.connect()
            
            # Subscribe to telemetry
            logger.info(f"Subscribing to telemetry on {device_name}")
            
            telemetry_iterator = client.subscribe(subscribe=subscribe_list)
            
            # Process incoming telemetry data
            for telemetry_entry in telemetry_iterator:
                await self.handle_telemetry_update(device_name, telemetry_entry)
                
        except KeyboardInterrupt:
            logger.info(f"Subscription interrupted for device: {device_name}")
            raise
        except Exception as e:
            logger.error(f"Error in subscription for device {device_name}: {e}")
            raise
        finally:
            try:
                client.close()
                logger.info(f"Closed connection to {device_name}")
            except:
                pass
    
    async def run(self):
        """Run the collector for all configured devices."""
        logger.info("Starting gNMI Collector")
        
        # Load configuration
        self.load_config()
        
        if not self.devices:
            logger.error("No devices configured. Please check configs/devices.yaml")
            return
        
        # Create subscription tasks for all devices
        tasks = []
        for device in self.devices:
            task = asyncio.create_task(self.subscribe_device(device))
            tasks.append(task)
        
        # Wait for all tasks (they run indefinitely until interrupted)
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Collector stopped by user")
        except Exception as e:
            logger.error(f"Collector error: {e}")
            raise


async def main():
    """Main entry point for the collector."""
    collector = GNMICollector(config_dir="configs")
    await collector.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Collector shutdown")
