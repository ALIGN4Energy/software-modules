# Energy Consumption Profile Generator (EnergyDiff)

A flow-matching based neural network model for generating synthetic daily energy consumption profiles for Dutch households. The EnergyDiff model generates 96 data points per day (15-minute intervals) conditioned on month and annual consumption.

## Overview

**What it does:** Generates realistic daily energy consumption profiles for households using a diffusion-based flow matching model
**Input:** Month (1-12), annual consumption (kWh), and trained model checkpoint
**Output:** 96 time-series data points representing energy usage in 15-minute intervals
**Use case:** Synthetic data generation for energy system modeling, testing, and simulation

### Key Features

- **EnergyDiff model:** Flow-matching diffusion model for high-quality profile generation
- **Conditional generation:** Profiles vary by season (month) and overall consumption level
- **Temporal resolution:** 96 intervals per day (15 minutes each)
- **Extensible architecture:** Abstract base classes for easy model integration
- **Type-safe:** Full Pydantic validation for configurations
- **Docker support:** Easy deployment with containerization

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [Python API Examples](#python-api-examples)
- [Architecture](#architecture)
- [Development](#development)
- [Testing](#testing)
- [Docker Usage](#docker-usage)

## Installation

### Prerequisites

- Python ≥ 3.13
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

### Pre-trained Model

A pre-trained EnergyDiff model is available at `models/energydiff-2025-12-22.ckpt` (not tracked in git due to size ~118MB). Contact the maintainers for access to the model checkpoint.

### Option 1: Using uv (Recommended)

```bash
# Clone the repository
cd profile-generator

# Install with uv
uv pip install -e .

# Or install from lock file
uv sync
```

### Option 2: Using pip

```bash
pip install -e .
```

### Option 3: Using Docker (Recommended for Production)

```bash
# Build the Docker image
docker build -t profile-generator .

# Get help
docker run --rm profile-generator help
```

### Dependencies

The project requires:
- `torch` ≥ 2.8.0 - PyTorch for neural network implementation
- `pytorch-lightning` ≥ 2.6.0 - Model training and checkpointing
- `flow-matching` ≥ 1.0.10 - Flow matching implementation
- `ema-pytorch` ≥ 0.7.9 - Exponential moving average
- `einops` ≥ 0.8.1 - Tensor operations
- `jaxtyping` ≥ 0.3.4 - Type annotations
- `pydantic` ≥ 2.12.2 - Configuration validation
- `numpy` ≥ 2.3.3 - Numerical operations
- `matplotlib` ≥ 3.10.7 - Visualization (optional)
- `pytest` ≥ 8.4.2 - Testing framework

## Quick Start

### Using the CLI (Recommended)

Generate annual energy consumption profiles:

```bash
# Generate profile for a household with 6500 kWh annual consumption
python scripts/generate_profile_cli.py \
  --model_path models/energydiff-2025-12-22.ckpt \
  --annual_consumption 6500 \
  --output output/profile.json

# Generate profile for household with heat pump
python scripts/generate_profile_cli.py \
  --model_path models/energydiff-2025-12-22.ckpt \
  --annual_consumption 7500 \
  --has_heatpump true \
  --output output/heatpump_profile.json

# Generate profile with multiple technologies
python scripts/generate_profile_cli.py \
  --model_path models/energydiff-2025-12-22.ckpt \
  --annual_consumption 9000 \
  --has_heatpump true \
  --has_solar true \
  --has_ev true \
  --num_steps 200 \
  --output output/fully_electrified.json
```

**Output:** JSON file containing daily profiles (96 × 15-minute intervals) for all 12 months.

### Using the Python API

```python
from profile_generator.interfaces.energydiff.config import (
    EnergyDiffModelConfig,
    EnergyDiffSampleConfig,
    EnergyDiffSampleCondition,
    Month,
)
from profile_generator.interfaces.energydiff.model import EnergyDiffModel

# Load the model
model = EnergyDiffModel(EnergyDiffModelConfig(
    model_path="models/energydiff-2025-12-22.ckpt",
    device="cpu"  # or "cuda" for GPU
))

# Configure sampling
sample_config = EnergyDiffSampleConfig(batch_size=5, num_steps=200)
sample_condition = EnergyDiffSampleCondition(
    month=Month.MARCH,
    annual_consumption=6500.0,  # kWh per year
)

# Generate profiles
profiles = model.sample(sample_config, sample_condition)

print(f"Generated shape: {profiles.shape}")  # (5, 96, 1)
```

## CLI Reference

### Command Syntax

```bash
python scripts/generate_profile_cli.py \
  --model_path <path> \
  --annual_consumption <value> \
  [--has_heatpump true|false] \
  [--has_solar true|false] \
  [--has_ev true|false] \
  [--num_steps <value>] \
  [--device cpu|cuda|mps] \
  [--output <path>]
```

### Parameters

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `--model_path` | **Yes** | string | - | Path to EnergyDiff model checkpoint (.ckpt) |
| `--annual_consumption` | **Yes** | float | - | Annual energy consumption in kWh |
| `--has_heatpump` | No | boolean | false | Household has heat pump |
| `--has_solar` | No | boolean | false | Household has solar panels |
| `--has_ev` | No | boolean | false | Household has electric vehicle |
| `--num_steps` | No | integer | 200 | Number of diffusion steps |
| `--device` | No | string | cpu | Device to run on (cpu, cuda, mps) |
| `--output` | No | string | output/profile.json | Output file path |

### Output Format

The CLI generates a JSON file with the following structure:

```json
{
  "metadata": {
    "annual_consumption": 7500.0,
    "has_heatpump": true,
    "has_solar": false,
    "has_ev": false,
    "generated_at": "2025-01-26T12:00:00",
    "model_info": "EnergyDiff flow-matching model",
    "num_steps": 200
  },
  "profiles": [
    {
      "month": 1,
      "month_name": "January",
      "daily_profile": [0.21, 0.19, 0.18, ...],
      "statistics": {
        "min": 0.05,
        "max": 0.42,
        "mean": 0.23,
        "intervals": 96
      }
    }
  ]
}
```

## Architecture

### EnergyDiff Model

The EnergyDiff model uses flow matching (a form of diffusion model) to generate realistic energy consumption profiles:

- **Architecture:** Transformer-based denoising network
- **Conditioning:** Month and annual consumption via embedders
- **Sampling:** ODE solver with Euler method
- **Training:** Continuous normalizing flows with velocity prediction

### Model Components

1. **FlowModelPL** - PyTorch Lightning module for training and inference
2. **DenoisingTransformer** - Transformer architecture for denoising
3. **Embedders** - Convert conditions to neural network inputs
4. **ODESolver** - Samples from the learned flow

### Data Flow

```
User Input
    ↓
EnergyDiffSampleCondition (month, annual_consumption)
    ↓
Embedder (condition → embedding)
    ↓
DenoisingTransformer (noise + embedding → profile)
    ↓
ODESolver (iterative denoising)
    ↓
96-point Profile Output
```

## Development

### Project Structure

```
profile-generator/
├── README.md
├── pyproject.toml
├── Dockerfile
├── docker-entrypoint.sh
├── configs/
│   └── energydiff_small.toml      # Model configuration
├── models/
│   └── energydiff-2025-12-22.ckpt # Pre-trained model (not in git)
├── src/profile_generator/
│   ├── __init__.py
│   ├── interfaces/
│   │   ├── base/                  # Abstract base classes
│   │   ├── demo_model/            # Simple demo model
│   │   └── energydiff/            # EnergyDiff model interface
│   ├── models/
│   │   ├── cnflow.py              # Flow matching model
│   │   ├── nn_components.py       # Neural network components
│   │   ├── configuration.py       # Model configurations
│   │   ├── embedders/             # Condition embedders
│   │   └── demo_nn.py             # Demo model
│   └── utils/
│       ├── logging.py             # Logging utilities
│       └── plot.py                # Plotting utilities
├── scripts/
│   ├── generate_profile_cli.py    # CLI for profile generation
│   └── generate_demo_data.py      # Demo script
└── tests/
    ├── interfaces/
    └── models/
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/models/test_demo_nn.py
```

## Docker Usage

### Building the Image

```bash
docker build -t profile-generator .
```

### Running Commands

#### Generate Profiles with EnergyDiff

```bash
# Mount your model and output directories
docker run --rm \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/output:/app/output \
  profile-generator generate \
  --model_path /app/models/energydiff-2025-12-22.ckpt \
  --annual_consumption 7500 \
  --output /app/output/profile.json
```

#### Run Demo (Simple Model)

```bash
docker run --rm profile-generator demo
```

#### Run Tests

```bash
docker run --rm profile-generator test
```

#### Interactive Shell

```bash
docker run --rm -it profile-generator shell
```

## License

Copyright Contributors to the ALIGN4Energy Project.
SPDX-License-Identifier: Apache-2.0

The EnergyDiff model is made available via Nan Lin and Pedro P. Vergara
from the Delft University of Technology. Nan Lin and Pedro P. Vergara are
funded via the ALIGN4Energy Project (with project number NWA.1389.20.251) of
the research programme NWA ORC 2020 which is (partly) financed by the Dutch
Research Council (NWO), The Netherlands.

## Related Projects

This profile generator is part of a larger energy system modeling project:
- **persona-segmentation** - Predicts consumer behavior personas
- **technology-adoption-agent-based-model** - Simulates technology adoption
