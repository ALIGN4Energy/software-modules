import torch
from torch import nn


class DemoNN(nn.Module):
    """Demo neural network model that generates data."""
    def __init__(self):
        super().__init__()
        self.month_mod = nn.Linear(1, 1)
        self.annual_c_mod = nn.Linear(1, 1)
        self.magic_vector = nn.Parameter(torch.empty(1, 96))
        self._initialize_weights()

    @torch.no_grad()
    def _initialize_weights(self):
        nn.init.ones_(self.annual_c_mod.weight)
        self.magic_vector.copy_(
        1.5 + torch.cos(torch.linspace(0, 2 * 3.1415926, steps=96)).unsqueeze(0)
        )

    def forward(self, x: dict[str, torch.Tensor]) -> torch.Tensor:
        month = self.month_mod(x["month"])
        annual_c = self.annual_c_mod(x["annual_consumption"])
        batch_size = month.shape[0]
        return (month + annual_c) * self.magic_vector.repeat(batch_size, 1)  # (B, 96)

    @torch.no_grad()
    def sample(self, condition: dict[str, torch.Tensor]) -> torch.Tensor:
        """Sample from the model given the condition.
        
        Args:
            condition (dict[str, torch.Tensor]): Condition dictionary with keys:
                - "month": Tensor of shape (B, 1) with month values normalized to [0, 1].
                - "annual_consumption": Tensor of shape (B, 1) with annual consumption normalized to [0, 1].
        
        Returns:
            torch.Tensor: Sampled tensor of shape (B, 96).
        """
        noise = torch.randn_like(self.magic_vector) * 0.5
        return (self.forward(condition) + noise).clamp(min=0.0)