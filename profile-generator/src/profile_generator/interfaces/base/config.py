from pydantic import BaseModel


class ModelConfigABC(BaseModel):
    """
    Base configuration class for all model configurations.
    """
    pass


class SampleConfigABC(BaseModel):
    """
    Base configuration class for all sampling configurations.
    """
    pass

