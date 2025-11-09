"""
Service Monitor - Core monitoring engine
Handles service health checks, data persistence, and status tracking
"""

import asyncio
import aiohttp
import time
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class ServiceStatus(Enum):
    """Service health status"""
    GREEN = "green"  # Operational
    YELLOW = "yellow"  # Degraded (slow response)
    RED = "red"  # Down


@dataclass
class ServiceCheck:
    """Single service check result"""
    timestamp: float
    status: ServiceStatus
    response_time: float
    error: Optional[str] = None


@dataclass
class ServiceData:
    """Service monitoring data"""
    name: str
    url: str
    current_status: ServiceStatus
    last_check: float
    response_time: float
    consecutive_failures: int
    history: List[ServiceCheck]
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['current_status'] = self.current_status.value
        data['history'] = [
            {
                'timestamp': check.timestamp,
                'status': check.status.value,
                'response_time': check.response_time,
                'error': check.error
            }
            for check in self.history
        ]
        return data


class ServiceMonitor:
    """Main service monitoring engine"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.services: Dict[str, ServiceData] = {}
        self.data_file = Path("data/service_data.json")
        self.running = False
        self.callbacks = []  # Status change callbacks
        
        # Load existing data
        self._load_data()
        
        # Initialize services from config
        self._initialize_services()
    
    def _load_config(self) -> dict:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}\n"
                "Please copy config.example.yaml to config.yaml and customize it."
            )
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _initialize_services(self):
        """Initialize service tracking from config"""
        for service_config in self.config.get('services', []):
            name = service_config['name']
            if name not in self.services:
                self.services[name] = ServiceData(
                    name=name,
                    url=service_config['url'],
                    current_status=ServiceStatus.GREEN,
                    last_check=0,
                    response_time=0,
                    consecutive_failures=0,
                    history=[]
                )
    
    def _load_data(self):
        """Load historical data from disk"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    for name, service_data in data.items():
                        # Reconstruct ServiceData from JSON
                        history = [
                            ServiceCheck(
                                timestamp=check['timestamp'],
                                status=ServiceStatus(check['status']),
                                response_time=check['response_time'],
                                error=check.get('error')
                            )
                            for check in service_data['history']
                        ]
                        self.services[name] = ServiceData(
                            name=service_data['name'],
                            url=service_data['url'],
                            current_status=ServiceStatus(service_data['current_status']),
                            last_check=service_data['last_check'],
                            response_time=service_data['response_time'],
                            consecutive_failures=service_data['consecutive_failures'],
                            history=history
                        )
            except Exception as e:
                print(f"Error loading data: {e}")
    
    def _save_data(self):
        """Save data to disk"""
        self.data_file.parent.mkdir(exist_ok=True)
        
        data = {name: service.to_dict() for name, service in self.services.items()}
        
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _cleanup_old_data(self):
        """Remove data older than configured history duration"""
        history_seconds = self.config['monitoring']['history_duration'] * 3600
        cutoff_time = time.time() - history_seconds
        
        for service in self.services.values():
            service.history = [
                check for check in service.history
                if check.timestamp > cutoff_time
            ]
    
    async def check_service(self, service_config: dict) -> ServiceCheck:
        """Check a single service's health"""
        name = service_config['name']
        url = service_config['url']
        timeout = self.config['monitoring']['timeout']
        
        start_time = time.time()
        
        try:
            # Increase max_line_size and max_field_size for services with large headers (like Twitter/X)
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    url, 
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    allow_redirects=True,
                    max_redirects=10
                ) as response:
                    response_time = time.time() - start_time
                    
                    # Accept 200-399 as successful (includes redirects)
                    expected_status = service_config.get('expected_status', 200)
                    if response.status == expected_status or (200 <= response.status < 400):
                        yellow_threshold = self.config['thresholds']['yellow_response_time']
                        if response_time > yellow_threshold:
                            status = ServiceStatus.YELLOW
                        else:
                            status = ServiceStatus.GREEN
                        error = None
                    else:
                        status = ServiceStatus.RED
                        error = f"HTTP {response.status}"
                    
                    return ServiceCheck(
                        timestamp=time.time(),
                        status=status,
                        response_time=response_time,
                        error=error
                    )
        
        except asyncio.TimeoutError:
            return ServiceCheck(
                timestamp=time.time(),
                status=ServiceStatus.RED,
                response_time=timeout,
                error="Timeout"
            )
        except Exception as e:
            return ServiceCheck(
                timestamp=time.time(),
                status=ServiceStatus.RED,
                response_time=time.time() - start_time,
                error=str(e)[:100]  # Truncate error message
            )
    
    def _update_service_status(self, name: str, check: ServiceCheck):
        """Update service status based on check result"""
        service = self.services[name]
        old_status = service.current_status
        
        # Update history
        service.history.append(check)
        service.last_check = check.timestamp
        service.response_time = check.response_time
        
        # Update failure counter
        if check.status == ServiceStatus.RED:
            service.consecutive_failures += 1
        else:
            service.consecutive_failures = 0
        
        # Determine current status
        red_threshold = self.config['thresholds']['red_consecutive_failures']
        if service.consecutive_failures >= red_threshold:
            service.current_status = ServiceStatus.RED
        else:
            service.current_status = check.status
        
        # Notify callbacks if status changed
        if old_status != service.current_status:
            for callback in self.callbacks:
                callback(name, old_status, service.current_status)
    
    def register_callback(self, callback):
        """Register a callback for status changes"""
        self.callbacks.append(callback)
    
    async def monitor_loop(self):
        """Main monitoring loop"""
        self.running = True
        check_interval = self.config['monitoring']['check_interval']
        
        while self.running:
            # Check all services
            tasks = []
            service_configs = self.config.get('services', [])
            
            for service_config in service_configs:
                tasks.append(self.check_service(service_config))
            
            # Wait for all checks to complete
            results = await asyncio.gather(*tasks)
            
            # Update statuses
            for service_config, check in zip(service_configs, results):
                self._update_service_status(service_config['name'], check)
            
            # Cleanup old data and save
            self._cleanup_old_data()
            self._save_data()
            
            # Wait for next check
            await asyncio.sleep(check_interval)
    
    def start(self):
        """Start monitoring (blocking)"""
        asyncio.run(self.monitor_loop())
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
    
    def get_service_data(self, name: str) -> Optional[ServiceData]:
        """Get data for a specific service"""
        return self.services.get(name)
    
    def get_all_services(self) -> Dict[str, ServiceData]:
        """Get data for all services"""
        return self.services
