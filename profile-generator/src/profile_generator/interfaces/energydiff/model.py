import torch
from flow_matching.solver import ODESolver

from ...models.cnflow import FlowModelPL
from ..base.model import ModelInterface
from .config import (
    EnergyDiffModelConfig,
    EnergyDiffSampleCondition,
    EnergyDiffSampleConfig,
)


class EnergyDiffModel(ModelInterface):
    """Interface of `EnergyDiffModel` that is used for generation
    
    """

    def __init__(self, model_config: EnergyDiffModelConfig):
        self.model_config = model_config
        self.device = torch.device(self.model_config.device)
        self.model = self._load_model()

    def _load_model(self):
        pl_model = FlowModelPL.load_from_checkpoint(
            self.model_config.model_path,
            map_location=self.device,
        )
        nn_model = pl_model.ema.ema_model
        return nn_model

    @staticmethod
    def create_batched_condition_tensor(
        condition: EnergyDiffSampleCondition,
        batch_size: int,
        device: torch.device|str,
    ) -> dict[str, torch.Tensor]:
        """create batched condition for generation

        returns:
            dict[str, torch.Tensor]: Condition tensor of shape (batch_size, 2)
        """
        _month = torch.ones((batch_size, 1)) * condition.month.value
        _annual_c = torch.ones((batch_size, 1)) * condition.annual_consumption
        return {
            "month": _month.to(device),
            "annual_consumption": _annual_c.to(device),
        }

    @staticmethod
    def _prepare_x_0(
        batch_size: int,
        device: torch.device|str,
    ) -> torch.Tensor:
        """Prepare initial noise tensor x_0 for sampling

        returns:
            torch.Tensor: Initial noise tensor of shape (batch_size, 96, 1)
        """
        return torch.randn((batch_size, 96, 1), device=device)

    def sample(
        self,
        sample_config: EnergyDiffSampleConfig,
        sample_condition: EnergyDiffSampleCondition,
    ):
        """Sample from the model
        Args:
            sample_config (EnergyDiffSampleConfig): Configuration for sampling.
            sample_condition (EnergyDiffSampleCondition): Conditions for sampling.
        Returns:
            torch.Tensor: Sampled tensor of shape (sample_config.batch_size, 96)
        """
        batched_condition = self.create_batched_condition_tensor(
            sample_condition,
            batch_size=sample_config.batch_size,
            device=self.device
        )  # dict[str, torch.Tensor]
        x_0 = self._prepare_x_0(
            batch_size=sample_config.batch_size,
            device=self.device,
        )
        solver = ODESolver(velocity_model=self.model)
        with torch.no_grad():
            samples = solver.sample(
                x_init=x_0,
                method="euler",
                step_size=1./sample_config.num_steps,
                y=batched_condition,
            )

        return samples
