from pathlib import Path

import torch

from profile_generator.interfaces.demo_model.config import (
    DemoModelConfig,
    DemoSampleCondition,
    DemoSampleConfig,
    Month,
)
from profile_generator.interfaces.demo_model.model import DemoModel


def _model_path() -> str:
    return str(
        (Path(__file__).resolve().parent.parent / "models" / "demo_model_state_dict.pt")
    )


def test_create_condition_tensor_normalizes_inputs():
    demo_model = DemoModel(DemoModelConfig(model_path=_model_path()))
    condition = DemoSampleCondition(
        month=Month.SEPTEMBER,
        annual_consumption=5500.0,
    )

    tensors = DemoModel.create_condition_tensor(
        condition=condition,
        batch_size=4,
        device=demo_model.device,
    )

    expected_month = torch.full((4, 1), Month.SEPTEMBER.value / 11.0)
    expected_annual = torch.full((4, 1), 5500.0 / 10000.0)

    assert set(tensors.keys()) == {"month", "annual_consumption"}
    assert tensors["month"].shape == (4, 1)
    assert tensors["annual_consumption"].shape == (4, 1)
    torch.testing.assert_close(tensors["month"].cpu(), expected_month)
    torch.testing.assert_close(tensors["annual_consumption"].cpu(), expected_annual)


def test_demo_model_sample_matches_forward():
    demo_model = DemoModel(DemoModelConfig(model_path=_model_path()))
    sample_config = DemoSampleConfig(batch_size=3)
    sample_condition = DemoSampleCondition(
        month=Month.JUNE,
        annual_consumption=7200.0,
    )

    condition_tensor = DemoModel.create_condition_tensor(
        condition=sample_condition,
        batch_size=sample_config.batch_size,
        device=demo_model.device,
    )

    with torch.no_grad():
        expected = demo_model.model(condition_tensor)
        samples = demo_model.sample(sample_config, sample_condition)

    assert samples.shape == (sample_config.batch_size, 96)
    torch.testing.assert_close(samples.cpu(), expected.cpu())
