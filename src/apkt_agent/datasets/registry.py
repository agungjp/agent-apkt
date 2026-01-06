"""Dataset registry and management."""

from typing import Dict, Type, Optional

from ..logging_ import get_logger
from .base import BaseDataset


class DatasetRegistry:
    """Registry for all available datasets."""
    
    _datasets: Dict[str, Type[BaseDataset]] = {}
    
    @classmethod
    def register(cls, name: str, dataset_class: Type[BaseDataset]) -> None:
        """Register a dataset.
        
        Args:
            name: Dataset name
            dataset_class: Dataset class
        """
        logger = get_logger()
        logger.info(f"Registering dataset: {name}")
        cls._datasets[name] = dataset_class
    
    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseDataset]]:
        """Get dataset class by name.
        
        Args:
            name: Dataset name
            
        Returns:
            Dataset class or None if not found
        """
        return cls._datasets.get(name)
    
    @classmethod
    def list(cls) -> Dict[str, Type[BaseDataset]]:
        """List all registered datasets.
        
        Returns:
            Dictionary of dataset name -> class
        """
        return cls._datasets.copy()
    
    @classmethod
    def create(cls, name: str, config) -> BaseDataset:
        """Create dataset instance.
        
        Args:
            name: Dataset name
            config: Configuration object
            
        Returns:
            Dataset instance
            
        Raises:
            ValueError: If dataset not found
        """
        dataset_class = cls.get(name)
        if not dataset_class:
            raise ValueError(f"Dataset not found: {name}")
        return dataset_class(config)
    
    @classmethod
    def get_handler(cls, name: str, config) -> "BaseDataset":
        """Get or create a dataset handler instance.
        
        Alias for create() for clearer intent.
        
        Args:
            name: Dataset name
            config: Configuration object
            
        Returns:
            Dataset handler instance
        """
        return cls.create(name, config)


def register_all_datasets():
    """Register all available datasets."""
    from .se004.kumulatif import SE004KumulatifDataset
    from .se004.rolling import SE004RollingDataset
    from .se004.gangguan import SE004GangguanDataset
    
    DatasetRegistry.register("se004_kumulatif", SE004KumulatifDataset)
    DatasetRegistry.register("se004_rolling", SE004RollingDataset)
    DatasetRegistry.register("se004_gangguan", SE004GangguanDataset)


# Auto-register on module import
register_all_datasets()
