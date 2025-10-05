import torch

from ..base.model import ModelInterface
from .config import DemoSampleCondition, DemoModelConfig, DemoSampleConfig
from ...models.demo_nn import DemoNN


class DemoModel(ModelInterface):
    """Interface of `DemoModel` that is use for generation
    
    """

    def __init__(self, model_config: DemoModelConfig):
        self.model_config = model_config
        self.device = torch.device(self.model_config.device)
        self.model = self._load_model()

    def _load_model(self):
        model = DemoNN().to(self.device)
        state_dict = torch.load(self.model_config.model_path, map_location=self.device)
        model.load_state_dict(state_dict)
        model.eval()
        return model

    @staticmethod
    def create_condition_tensor(
        condition: DemoSampleCondition,
        batch_size: int,
        device: torch.device|str,
    ) -> dict[str, torch.Tensor]:
        """create batched condition for generation
        returns:
            torch.Tensor: Condition tensor of shape (batch_size, 2)
        """
        _month = torch.ones((batch_size, 1)) * condition.month.value / 11.0
        _annual_c = torch.ones((batch_size, 1)) * condition.annual_consumption / 10000.0
        return {
            "month": _month.to(device),
            "annual_consumption": _annual_c.to(device),
        }

    def sample(
        self,
        sample_config: DemoSampleConfig,
        sample_condition: DemoSampleCondition,
    ):
        """Sample from the model
        Args:
            sample_config (DemoSampleConfig): Configuration for sampling.
            sample_condition (DemoSampleCondition): Conditions for sampling.
        Returns:
            torch.Tensor: Sampled tensor of shape (sample_config.batch_size, 96)
        """
        condition_tensor = self.create_condition_tensor(
            sample_condition,
            batch_size=sample_config.batch_size,
            device=self.device
        )
        with torch.no_grad():
            samples = self.model(condition_tensor)
        return samples
