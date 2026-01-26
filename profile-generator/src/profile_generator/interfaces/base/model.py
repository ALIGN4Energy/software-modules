# Copyright Contributors to the ALIGN4Energy Project.
# SPDX-License-Identifier: Apache-2.0

# The EnergyDiff model is made available via Nan Lin and Pedro P. Vergara
# from the Delft University of Technology. Nan Lin and Pedro P. Vergara are
# funded via the ALIGN4Energy Project (with project number NWA.1389.20.251) of
# the research programme NWA ORC 2020 which is (partly) financed by the Dutch
# Research Council (NWO), The Netherland.

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
        
