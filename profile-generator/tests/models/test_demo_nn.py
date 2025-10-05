import torch

from profile_generator.models.demo_nn import DemoNN


def test_demo_nn_initialization():
    model = DemoNN()

    assert isinstance(model.month_mod, torch.nn.Linear)
    assert isinstance(model.annual_c_mod, torch.nn.Linear)
    assert model.magic_vector.shape == (1, 96)
    torch.testing.assert_close(
        model.annual_c_mod.weight,
        torch.ones_like(model.annual_c_mod.weight),
    )
    torch.testing.assert_close(
        model.magic_vector[0, 0],
        torch.tensor(2.5, dtype=model.magic_vector.dtype),
    )


def test_demo_nn_forward_expected_behavior():
    model = DemoNN()
    with torch.no_grad():
        model.month_mod.weight.fill_(2.0)
        model.month_mod.bias.fill_(0.5)
        model.annual_c_mod.weight.fill_(1.0)
        model.annual_c_mod.bias.zero_()
        model.magic_vector.copy_(
            torch.arange(96, dtype=torch.float32).unsqueeze(0)
        )

    condition = {
        "month": torch.tensor([[0.0], [1.0]], dtype=torch.float32),
        "annual_consumption": torch.tensor([[0.2], [0.8]], dtype=torch.float32),
    }

    output = model.forward(condition)
    expected = torch.vstack(
        (
            torch.arange(96, dtype=torch.float32) * 0.7,
            torch.arange(96, dtype=torch.float32) * 3.3,
        )
    )

    assert output.shape == (2, 96)
    torch.testing.assert_close(output, expected)


def test_demo_nn_sample_adds_noise_and_clamps():
    model = DemoNN()
    with torch.no_grad():
        model.month_mod.weight.fill_(1.5)
        model.month_mod.bias.zero_()
        model.annual_c_mod.weight.fill_(0.5)
        model.annual_c_mod.bias.fill_(0.1)
        model.magic_vector.copy_(
            torch.arange(96, dtype=torch.float32).unsqueeze(0)
        )

    condition = {
        "month": torch.tensor([[0.6]], dtype=torch.float32),
        "annual_consumption": torch.tensor([[0.4]], dtype=torch.float32),
    }

    base = model.forward(condition)

    torch.manual_seed(123)
    expected_noise = torch.randn_like(model.magic_vector) * 0.5
    expected = (base + expected_noise).clamp(min=0.0)

    torch.manual_seed(123)
    sample = model.sample(condition)

    assert sample.shape == (1, 96)
    assert torch.all(sample >= 0)
    torch.testing.assert_close(sample, expected)
