from enum import Enum
from typing import Self

from pydantic import BaseModel

from ..base.config import ModelConfigABC, SampleConfigABC

# Model
class DemoModelConfig(ModelConfigABC):
    device: str = "cpu"
    model_path: str


# Sample
class DemoSampleConfig(SampleConfigABC):
    batch_size: int = 100


# Month
class Month(int, Enum):
    JANUARY = 0
    FEBRUARY = 1
    MARCH = 2
    APRIL = 3
    MAY = 4
    JUNE = 5
    JULY = 6
    AUGUST = 7
    SEPTEMBER = 8
    OCTOBER = 9
    NOVEMBER = 10
    DECEMBER = 11

    @classmethod
    def _missing_(
        cls: type[Self],
        value: int | str,
    ) -> Self:
        """Instantiate the enum from a value.

        Args:
            value (int | str): The value to convert.

        """
        if isinstance(value, int):
            try:
                return cls(value)
            except ValueError as err:
                raise ValueError(
                    f"Invalid value for {cls.__name__}: {value}. "
                    f"Valid values are: {[e.value for e in cls]}"
                ) from err
        elif isinstance(value, str):
            try:
                return cls[value.upper()]
            except KeyError as err:
                raise ValueError(
                    f"Invalid value for {cls.__name__}: {value}. "
                    f"Valid values are: {[e.name for e in cls]}"
                ) from err

        raise TypeError(f"Cannot convert {type(value)} to {cls.__name__}")


class DemoSampleCondition(BaseModel):
    """Conditions that are used by the demo model for sampling.
    
    Attributes:
        month (Month): The month of the year.
        annual_consumption (float): The annual consumption in kWh.
        
    """
    month: Month
    annual_consumption: float  # in kWh
