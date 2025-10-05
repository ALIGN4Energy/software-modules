from __future__ import annotations

from pathlib import Path

from profile_generator.interfaces.demo_model.config import (
    DemoModelConfig,
    DemoSampleCondition,
    DemoSampleConfig,
    Month,
)
from profile_generator.interfaces.demo_model.model import DemoModel


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    model_path = project_root / "tests" / "models" / "demo_model_state_dict.pt"

    demo_model = DemoModel(DemoModelConfig(model_path=str(model_path)))

    sample_config = DemoSampleConfig(batch_size=5)
    sample_condition = DemoSampleCondition(
        month=Month.MARCH,
        annual_consumption=6500.0,
    )

    generated = demo_model.sample(sample_config, sample_condition)

    print("Demo data generation complete.")
    print(f"Generated data shape: {tuple(generated.shape)}")
    print(f"Generated data dtype: {generated.dtype}")
    print(f"Generated data device: {generated.device}")


if __name__ == "__main__":
    main()
