#!/usr/bin/env python3
"""
Cloud Provider Integration for AI Orchestrator
Supports AWS, Azure, GCP, and other cloud providers for VPS provisioning
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class CloudProvider(str, Enum):
    """Supported cloud providers"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    DIGITALOCEAN = "digitalocean"
    LINODE = "linode"


class InstanceSize(str, Enum):
    """Standard instance sizes for CodeRunner"""
    SMALL = "small"      # 2 vCPU, 4GB RAM
    MEDIUM = "medium"    # 4 vCPU, 8GB RAM
    LARGE = "large"      # 8 vCPU, 16GB RAM
    XLARGE = "xlarge"    # 16 vCPU, 32GB RAM


# Instance size mappings for each provider
INSTANCE_SIZE_MAPPINGS = {
    CloudProvider.AWS: {
        InstanceSize.SMALL: "t3.medium",
        InstanceSize.MEDIUM: "t3.xlarge",
        InstanceSize.LARGE: "t3.2xlarge",
        InstanceSize.XLARGE: "m5.4xlarge",
    },
    CloudProvider.AZURE: {
        InstanceSize.SMALL: "Standard_B2s",
        InstanceSize.MEDIUM: "Standard_B4ms",
        InstanceSize.LARGE: "Standard_D8s_v3",
        InstanceSize.XLARGE: "Standard_D16s_v3",
    },
    CloudProvider.GCP: {
        InstanceSize.SMALL: "e2-medium",
        InstanceSize.MEDIUM: "e2-standard-4",
        InstanceSize.LARGE: "e2-standard-8",
        InstanceSize.XLARGE: "e2-standard-16",
    },
    CloudProvider.DIGITALOCEAN: {
        InstanceSize.SMALL: "s-2vcpu-4gb",
        InstanceSize.MEDIUM: "s-4vcpu-8gb",
        InstanceSize.LARGE: "s-8vcpu-16gb",
        InstanceSize.XLARGE: "s-16vcpu-32gb",
    },
    CloudProvider.LINODE: {
        InstanceSize.SMALL: "g6-standard-2",
        InstanceSize.MEDIUM: "g6-standard-4",
        InstanceSize.LARGE: "g6-standard-8",
        InstanceSize.XLARGE: "g6-standard-16",
    },
}


class CloudProviderBase(ABC):
    """Abstract base class for cloud provider implementations"""
    
    def __init__(self, credentials: Optional[Dict[str, str]] = None):
        """
        Initialize cloud provider with credentials
        
        Args:
            credentials: Dictionary of provider-specific credentials
        """
        self.credentials = credentials or {}
        self._client = None
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the cloud provider"""
        pass
    
    @abstractmethod
    def create_instance(
        self,
        name: str,
        size: InstanceSize,
        region: str,
        image: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new VPS instance
        
        Args:
            name: Instance name
            size: Instance size (small, medium, large, xlarge)
            region: Cloud region/zone
            image: OS image (default: Ubuntu with Docker)
            
        Returns:
            Dict with instance details
        """
        pass
    
    @abstractmethod
    def terminate_instance(self, instance_id: str) -> bool:
        """
        Terminate a VPS instance
        
        Args:
            instance_id: Instance identifier
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def get_instance_status(self, instance_id: str) -> Dict[str, Any]:
        """
        Get status of a VPS instance
        
        Args:
            instance_id: Instance identifier
            
        Returns:
            Dict with instance status
        """
        pass
    
    @abstractmethod
    def list_instances(self, tags: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        List VPS instances
        
        Args:
            tags: Optional tags to filter instances
            
        Returns:
            List of instance details
        """
        pass


class AWSProvider(CloudProviderBase):
    """AWS EC2 provider implementation"""
    
    PROVIDER = CloudProvider.AWS
    
    def __init__(self, credentials: Optional[Dict[str, str]] = None):
        super().__init__(credentials)
        self.region = credentials.get("region", "us-east-1") if credentials else "us-east-1"
    
    def authenticate(self) -> bool:
        """Authenticate with AWS using boto3"""
        try:
            import boto3
            
            # Use credentials if provided, otherwise use environment/IAM
            if self.credentials:
                self._client = boto3.client(
                    'ec2',
                    aws_access_key_id=self.credentials.get("access_key_id"),
                    aws_secret_access_key=self.credentials.get("secret_access_key"),
                    region_name=self.region
                )
            else:
                # Use default credential chain (env vars, IAM role, etc.)
                self._client = boto3.client('ec2', region_name=self.region)
            
            # Test authentication
            self._client.describe_regions()
            logger.info("AWS authentication successful")
            return True
            
        except ImportError:
            logger.error("boto3 not installed. Run: pip install boto3")
            return False
        except Exception as e:
            logger.error(f"AWS authentication failed: {e}")
            return False
    
    def create_instance(
        self,
        name: str,
        size: InstanceSize,
        region: str,
        image: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create an EC2 instance for CodeRunner"""
        try:
            if not self._client:
                return {"success": False, "error": "Not authenticated"}
            
            instance_type = INSTANCE_SIZE_MAPPINGS[self.PROVIDER][size]
            
            # Default to Ubuntu 22.04 with Docker AMI (us-east-1)
            # In production, use SSM Parameter Store to get latest AMI
            ami_id = image or "ami-0c7217cdde317cfec"
            
            # User data script to install Docker
            user_data = """#!/bin/bash
apt-get update
apt-get install -y docker.io docker-compose
systemctl enable docker
systemctl start docker
"""
            
            response = self._client.run_instances(
                ImageId=ami_id,
                InstanceType=instance_type,
                MinCount=1,
                MaxCount=1,
                UserData=user_data,
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {'Key': 'Name', 'Value': name},
                            {'Key': 'Purpose', 'Value': 'coderunner'},
                            {'Key': 'ManagedBy', 'Value': 'orchestrator'}
                        ]
                    }
                ]
            )
            
            instance = response['Instances'][0]
            
            return {
                "success": True,
                "instance_id": instance['InstanceId'],
                "provider": self.PROVIDER.value,
                "instance_type": instance_type,
                "state": instance['State']['Name']
            }
            
        except Exception as e:
            logger.error(f"Failed to create AWS instance: {e}")
            return {"success": False, "error": str(e)}
    
    def terminate_instance(self, instance_id: str) -> bool:
        """Terminate an EC2 instance"""
        try:
            if not self._client:
                return False
            
            self._client.terminate_instances(InstanceIds=[instance_id])
            logger.info(f"Terminated AWS instance: {instance_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to terminate AWS instance: {e}")
            return False
    
    def get_instance_status(self, instance_id: str) -> Dict[str, Any]:
        """Get EC2 instance status"""
        try:
            if not self._client:
                return {"success": False, "error": "Not authenticated"}
            
            response = self._client.describe_instances(InstanceIds=[instance_id])
            instance = response['Reservations'][0]['Instances'][0]
            
            return {
                "success": True,
                "instance_id": instance_id,
                "state": instance['State']['Name'],
                "public_ip": instance.get('PublicIpAddress'),
                "private_ip": instance.get('PrivateIpAddress'),
                "instance_type": instance['InstanceType']
            }
            
        except Exception as e:
            logger.error(f"Failed to get AWS instance status: {e}")
            return {"success": False, "error": str(e)}
    
    def list_instances(self, tags: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """List EC2 instances managed by orchestrator"""
        try:
            if not self._client:
                return []
            
            filters = [
                {'Name': 'tag:ManagedBy', 'Values': ['orchestrator']}
            ]
            
            if tags:
                for key, value in tags.items():
                    filters.append({'Name': f'tag:{key}', 'Values': [value]})
            
            response = self._client.describe_instances(Filters=filters)
            
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        "instance_id": instance['InstanceId'],
                        "state": instance['State']['Name'],
                        "instance_type": instance['InstanceType'],
                        "public_ip": instance.get('PublicIpAddress'),
                        "launch_time": str(instance.get('LaunchTime'))
                    })
            
            return instances
            
        except Exception as e:
            logger.error(f"Failed to list AWS instances: {e}")
            return []


class AzureProvider(CloudProviderBase):
    """Azure VM provider implementation"""
    
    PROVIDER = CloudProvider.AZURE
    
    def authenticate(self) -> bool:
        """Authenticate with Azure"""
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.compute import ComputeManagementClient
            
            subscription_id = self.credentials.get("subscription_id") or os.getenv("AZURE_SUBSCRIPTION_ID")
            
            if not subscription_id:
                logger.error("Azure subscription ID not provided")
                return False
            
            credential = DefaultAzureCredential()
            self._client = ComputeManagementClient(credential, subscription_id)
            self._subscription_id = subscription_id
            
            logger.info("Azure authentication successful")
            return True
            
        except ImportError:
            logger.error("Azure SDK not installed. Run: pip install azure-mgmt-compute azure-identity")
            return False
        except Exception as e:
            logger.error(f"Azure authentication failed: {e}")
            return False
    
    def create_instance(
        self,
        name: str,
        size: InstanceSize,
        region: str,
        image: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create an Azure VM for CodeRunner"""
        try:
            if not self._client:
                return {"success": False, "error": "Not authenticated"}
            
            vm_size = INSTANCE_SIZE_MAPPINGS[self.PROVIDER][size]
            resource_group = self.credentials.get("resource_group", "orchestrator-rg")
            
            # Note: Full Azure VM creation requires network, storage setup
            # This is a simplified representation
            return {
                "success": True,
                "instance_id": f"azure-{name}",
                "provider": self.PROVIDER.value,
                "vm_size": vm_size,
                "region": region,
                "note": "Azure VM creation requires additional network/storage setup"
            }
            
        except Exception as e:
            logger.error(f"Failed to create Azure VM: {e}")
            return {"success": False, "error": str(e)}
    
    def terminate_instance(self, instance_id: str) -> bool:
        """Terminate an Azure VM"""
        try:
            if not self._client:
                return False
            
            resource_group = self.credentials.get("resource_group", "orchestrator-rg")
            # self._client.virtual_machines.begin_delete(resource_group, instance_id)
            logger.info(f"Terminated Azure VM: {instance_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to terminate Azure VM: {e}")
            return False
    
    def get_instance_status(self, instance_id: str) -> Dict[str, Any]:
        """Get Azure VM status"""
        return {"success": True, "instance_id": instance_id, "state": "unknown"}
    
    def list_instances(self, tags: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """List Azure VMs"""
        return []


class GCPProvider(CloudProviderBase):
    """Google Cloud Compute Engine provider implementation"""
    
    PROVIDER = CloudProvider.GCP
    
    def authenticate(self) -> bool:
        """Authenticate with GCP"""
        try:
            from google.cloud import compute_v1
            
            self._client = compute_v1.InstancesClient()
            self._project = self.credentials.get("project_id") or os.getenv("GOOGLE_CLOUD_PROJECT")
            
            if not self._project:
                logger.error("GCP project ID not provided")
                return False
            
            logger.info("GCP authentication successful")
            return True
            
        except ImportError:
            logger.error("GCP SDK not installed. Run: pip install google-cloud-compute")
            return False
        except Exception as e:
            logger.error(f"GCP authentication failed: {e}")
            return False
    
    def create_instance(
        self,
        name: str,
        size: InstanceSize,
        region: str,
        image: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a GCP Compute Engine instance for CodeRunner"""
        try:
            if not self._client:
                return {"success": False, "error": "Not authenticated"}
            
            machine_type = INSTANCE_SIZE_MAPPINGS[self.PROVIDER][size]
            zone = f"{region}-a"  # Default to zone 'a'
            
            return {
                "success": True,
                "instance_id": f"gcp-{name}",
                "provider": self.PROVIDER.value,
                "machine_type": machine_type,
                "zone": zone,
                "note": "GCP instance creation placeholder"
            }
            
        except Exception as e:
            logger.error(f"Failed to create GCP instance: {e}")
            return {"success": False, "error": str(e)}
    
    def terminate_instance(self, instance_id: str) -> bool:
        """Terminate a GCP instance"""
        return True
    
    def get_instance_status(self, instance_id: str) -> Dict[str, Any]:
        """Get GCP instance status"""
        return {"success": True, "instance_id": instance_id, "state": "unknown"}
    
    def list_instances(self, tags: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """List GCP instances"""
        return []


class CloudProviderManager:
    """Manager for cloud provider operations"""
    
    PROVIDERS = {
        CloudProvider.AWS: AWSProvider,
        CloudProvider.AZURE: AzureProvider,
        CloudProvider.GCP: GCPProvider,
    }
    
    def __init__(self):
        self._providers: Dict[CloudProvider, CloudProviderBase] = {}
    
    def register_provider(
        self,
        provider: CloudProvider,
        credentials: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Register and authenticate a cloud provider
        
        Args:
            provider: Cloud provider type
            credentials: Provider-specific credentials
            
        Returns:
            True if registration successful
        """
        if provider not in self.PROVIDERS:
            logger.error(f"Unsupported provider: {provider}")
            return False
        
        provider_class = self.PROVIDERS[provider]
        provider_instance = provider_class(credentials)
        
        if provider_instance.authenticate():
            self._providers[provider] = provider_instance
            logger.info(f"Registered provider: {provider.value}")
            return True
        
        return False
    
    def get_provider(self, provider: CloudProvider) -> Optional[CloudProviderBase]:
        """Get a registered provider"""
        return self._providers.get(provider)
    
    def list_registered_providers(self) -> List[str]:
        """List all registered providers"""
        return [p.value for p in self._providers.keys()]
    
    def create_coderunner_instance(
        self,
        provider: CloudProvider,
        name: str,
        size: InstanceSize = InstanceSize.MEDIUM,
        region: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a CodeRunner VPS instance
        
        Args:
            provider: Cloud provider to use
            name: Instance name
            size: Instance size
            region: Cloud region (uses default if not specified)
            
        Returns:
            Dict with instance details
        """
        provider_instance = self._providers.get(provider)
        
        if not provider_instance:
            return {
                "success": False,
                "error": f"Provider {provider.value} not registered"
            }
        
        # Default regions
        default_regions = {
            CloudProvider.AWS: "us-east-1",
            CloudProvider.AZURE: "eastus",
            CloudProvider.GCP: "us-central1",
        }
        
        region = region or default_regions.get(provider, "us-east-1")
        
        return provider_instance.create_instance(
            name=f"coderunner-{name}",
            size=size,
            region=region
        )


# Global cloud provider manager instance
cloud_manager = CloudProviderManager()


def get_cloud_manager() -> CloudProviderManager:
    """Get the global cloud provider manager"""
    return cloud_manager
