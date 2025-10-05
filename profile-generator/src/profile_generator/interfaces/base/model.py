from abc import ABC, abstractmethod

from .config import ModelConfigABC, SampleConfigABC


class ModelInterface(ABC):
    """
    Base interface for all model implementations.
    """    
    @abstractmethod
    def __init__(self, model_config: ModelConfigABC):
        pass

    @abstractmethod
    def sample(
        self,
        sample_config: SampleConfigABC,
        **kwargs,
    ):
        pass
        
