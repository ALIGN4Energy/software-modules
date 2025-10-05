# Energy Consumption Profile Generator

A PyTorch-based neural network model for generating synthetic daily energy consumption profiles for Dutch households. The model generates 96 data points per day (15-minute intervals) conditioned on month and annual consumption.

## Overview

**What it does:** Generates realistic daily energy consumption profiles for households
**Input:** Month (1-12) and annual consumption (kWh)
**Output:** 96 time-series data points representing energy usage in 15-minute intervals
**Use case:** Synthetic data generation for energy system modeling, testing, and simulation

### Key Features

- **Conditional generation:** Profiles vary by season (month) and overall consumption level
- **Temporal resolution:** 96 intervals per day (15 minutes each)
- **Stochastic sampling:** Adds realistic variability to generated profiles
- **Extensible architecture:** Abstract base classes for easy model integration
- **Type-safe:** Full Pydantic validation for configurations
- **Well-tested:** Comprehensive test suite included

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [Python API Examples](#python-api-examples)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Development](#development)
- [Testing](#testing)
- [Docker Usage](#docker-usage)
- [Model Details](#model-details)
- [Contributing](#contributing)

## Installation

### Prerequisites

- Python ≥ 3.13
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

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

# Run demo (default)
docker run --rm profile-generator

# Run tests
docker run --rm profile-generator test

# Get help
docker run --rm profile-generator help
```

### Dependencies

The project requires:
- `torch` ≥ 2.8.0 - PyTorch for neural network implementation
- `pydantic` ≥ 2.12.2 - Configuration validation
- `numpy` ≥ 2.3.3 - Numerical operations
- `matplotlib` ≥ 3.10.7 - Visualization (optional)
- `pytest` ≥ 8.4.2 - Testing framework

## Quick Start

### Using the CLI (Recommended)

Generate annual energy consumption profiles via Docker:

```bash
# Build the Docker image
docker build -t profile-generator .

# Generate profile for a household with 6500 kWh annual consumption
docker run --rm -v $(pwd)/output:/app/output profile-generator generate \
  --annual_consumption 6500 \
  --output output/profile.json

# Generate profile for household with heat pump
docker run --rm -v $(pwd)/output:/app/output profile-generator generate \
  --annual_consumption 7500 \
  --has_heatpump true \
  --output output/heatpump_profile.json

# Generate profile with multiple technologies
docker run --rm -v $(pwd)/output:/app/output profile-generator generate \
  --annual_consumption 9000 \
  --has_heatpump true \
  --has_solar true \
  --has_ev true \
  --output output/fully_electrified.json

# Get help
docker run --rm profile-generator generate --help
```

**Output:** JSON file containing daily profiles (96 × 15-minute intervals) for all 12 months.

**Example output structure:**
```json
{
  "metadata": {
    "annual_consumption": 7500,
    "has_heatpump": true,
    "has_solar": false,
    "has_ev": false,
    "generated_at": "2025-11-02T12:00:00"
  },
  "profiles": [
    {
      "month": 1,
      "month_name": "January",
      "daily_profile": [2.1, 1.9, 1.8, ...],  // 96 values
      "statistics": {
        "min": 0.5,
        "max": 4.2,
        "mean": 2.3,
        "intervals": 96
      }
    },
    ...
  ]
}
```

### Using the Python API

For programmatic access:

```python
from profile_generator.interfaces.demo_model.config import (
    DemoModelConfig,
    DemoSampleConfig,
    DemoSampleCondition,
    Month,
)
from profile_generator.interfaces.demo_model.model import DemoModel

# Load the model
model_path = "tests/models/demo_model_state_dict.pt"
model = DemoModel(DemoModelConfig(model_path=model_path))

# Configure sampling
sample_config = DemoSampleConfig(batch_size=5)
sample_condition = DemoSampleCondition(
    month=Month.MARCH,
    annual_consumption=6500.0,  # kWh per year
)

# Generate profiles
profiles = model.sample(sample_config, sample_condition)

print(f"Generated shape: {profiles.shape}")  # (5, 96)
print(f"Generated dtype: {profiles.dtype}")   # torch.float32
```

### Running the Demo Script

**Docker:**
```bash
docker run --rm profile-generator demo
# or simply
docker run --rm profile-generator
```

Expected output:
```
Demo data generation complete.
Generated data shape: (5, 96)
Generated data dtype: torch.float32
Generated data device: cpu
```

## CLI Reference

### Command Syntax

```bash
docker run --rm -v $(pwd)/output:/app/output profile-generator generate \
  --annual_consumption <value> \
  [--has_heatpump true|false] \
  [--has_solar true|false] \
  [--has_ev true|false] \
  [--output <path>] \
  [--model_path <path>]
```

### Parameters

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `--annual_consumption` | **Yes** | float | - | Annual energy consumption in kWh |
| `--has_heatpump` | No | boolean | false | Household has heat pump |
| `--has_solar` | No | boolean | false | Household has solar panels |
| `--has_ev` | No | boolean | false | Household has electric vehicle |
| `--output` | No | string | output/profile.json | Output file path |
| `--model_path` | No | string | tests/models/demo_model_state_dict.pt | Path to trained model |

**Note:** The current demo model only uses `annual_consumption` and month. The full trained model will incorporate `has_heatpump`, `has_solar`, and `has_ev` as neural network inputs.

### Output Format

The CLI generates a JSON file with the following structure:

```json
{
  "metadata": {
    "annual_consumption": float,
    "has_heatpump": boolean,
    "has_solar": boolean,
    "has_ev": boolean,
    "generated_at": "ISO-8601 timestamp",
    "model_info": "string"
  },
  "profiles": [
    {
      "month": 1-12,
      "month_name": "string",
      "daily_profile": [96 float values],
      "statistics": {
        "min": float,
        "max": float,
        "mean": float,
        "intervals": 96
      }
    },
    // ... 12 monthly profiles
  ]
}
```

Each `daily_profile` contains 96 values representing 15-minute intervals (24 hours ÷ 96 = 15 minutes per interval).

### CLI Usage Examples

```bash
# Basic household
docker run --rm -v $(pwd)/output:/app/output profile-generator generate \
  --annual_consumption 6500 \
  --output output/basic_household.json

# Household with heat pump (higher winter consumption)
docker run --rm -v $(pwd)/output:/app/output profile-generator generate \
  --annual_consumption 7500 \
  --has_heatpump true \
  --output output/heatpump_household.json

# Household with solar (net metering effect)
docker run --rm -v $(pwd)/output:/app/output profile-generator generate \
  --annual_consumption 6000 \
  --has_solar true \
  --output output/solar_household.json

# Full electrification scenario
docker run --rm -v $(pwd)/output:/app/output profile-generator generate \
  --annual_consumption 9000 \
  --has_heatpump true \
  --has_solar true \
  --has_ev true \
  --output output/fully_electrified.json

# Get detailed help
docker run --rm profile-generator generate --help
```

## Python API Examples

### Example 1: Generate Winter vs Summer Profiles

```python
from profile_generator.interfaces.demo_model.config import *
from profile_generator.interfaces.demo_model.model import DemoModel

model = DemoModel(DemoModelConfig(model_path="tests/models/demo_model_state_dict.pt"))

# Winter profile (January, high consumption)
winter_condition = DemoSampleCondition(
    month=Month.JANUARY,
    annual_consumption=8000.0
)
winter_profiles = model.sample(
    DemoSampleConfig(batch_size=10),
    winter_condition
)

# Summer profile (July, lower consumption)
summer_condition = DemoSampleCondition(
    month=Month.JULY,
    annual_consumption=4000.0
)
summer_profiles = model.sample(
    DemoSampleConfig(batch_size=10),
    summer_condition
)

print(f"Winter avg: {winter_profiles.mean():.2f}")
print(f"Summer avg: {summer_profiles.mean():.2f}")
```

### Example 2: Batch Generation for Multiple Households

```python
import torch

# Generate profiles for 100 households
config = DemoSampleConfig(batch_size=100)
condition = DemoSampleCondition(
    month=Month.APRIL,
    annual_consumption=5500.0
)

profiles = model.sample(config, condition)

# Profiles shape: (100, 96)
# Each row is one household's daily profile
# Each column is a 15-minute interval
```

### Example 3: GPU Acceleration

```python
# Use GPU if available
model_config = DemoModelConfig(
    model_path="tests/models/demo_model_state_dict.pt",
    device="cuda" if torch.cuda.is_available() else "cpu"
)
model = DemoModel(model_config)

# Sampling will now run on GPU
profiles = model.sample(sample_config, sample_condition)
print(f"Device: {profiles.device}")
```

### Example 4: Export to NumPy for Analysis

```python
import numpy as np
import matplotlib.pyplot as plt

# Generate profile
profiles = model.sample(
    DemoSampleConfig(batch_size=1),
    DemoSampleCondition(month=Month.MARCH, annual_consumption=6000.0)
)

# Convert to numpy
profile_np = profiles[0].cpu().numpy()

# Plot
time_intervals = np.arange(96) * 15 / 60  # Convert to hours
plt.plot(time_intervals, profile_np)
plt.xlabel('Hour of Day')
plt.ylabel('Energy Consumption')
plt.title('Daily Energy Profile (March, 6000 kWh/year)')
plt.grid(True)
plt.show()
```

## Architecture

### Model Components

#### 1. Neural Network (`DemoNN`)

A simple PyTorch neural network that generates consumption profiles:

```python
class DemoNN(nn.Module):
    - month_mod: Linear(1, 1) - Processes month information
    - annual_c_mod: Linear(1, 1) - Processes annual consumption
    - magic_vector: Parameter(1, 96) - Base profile pattern (cosine wave)
```

**Forward Pass:**
```
output = (month_effect + annual_effect) * base_pattern
```

**Sampling:**
```
sample = forward(condition) + noise
sample = clamp(sample, min=0)  # Ensure non-negative values
```

#### 2. Model Interface (`DemoModel`)

High-level interface for loading and using the model:

- Loads pre-trained model weights
- Handles device management (CPU/GPU)
- Normalizes inputs (month to [0,1], consumption to [0,1])
- Provides clean API for sampling

#### 3. Configuration System

Type-safe configuration using Pydantic:

- `DemoModelConfig` - Model loading configuration
- `DemoSampleConfig` - Sampling parameters
- `DemoSampleCondition` - Generation conditions

### Data Flow

```
User Input
    ↓
DemoSampleCondition (month, annual_consumption)
    ↓
Normalization (month/11, consumption/10000)
    ↓
DemoNN.forward()
    ↓
Add Gaussian Noise
    ↓
Clamp to [0, ∞)
    ↓
96-point Profile Output
```

### Input Normalization

- **Month:** Divided by 11 to get range [0, 1]
  - January (0) → 0.0
  - December (11) → 1.0

- **Annual Consumption:** Divided by 10,000 to get range [0, ~1]
  - 5,000 kWh → 0.5
  - 10,000 kWh → 1.0

### Output Format

Generated profiles have shape `(batch_size, 96)`:
- **96 intervals** = 24 hours × 4 intervals per hour
- **15-minute resolution** = 24h / 96 = 15 minutes
- **Values:** Energy consumption (units depend on training data scale)

## API Reference

### Core Classes

#### `DemoModel`

```python
class DemoModel(ModelInterface):
    def __init__(self, model_config: DemoModelConfig)
    def sample(
        self,
        sample_config: DemoSampleConfig,
        sample_condition: DemoSampleCondition,
    ) -> torch.Tensor
```

#### `DemoModelConfig`

```python
class DemoModelConfig(BaseModel):
    device: str = "cpu"  # "cpu", "cuda", "mps", etc.
    model_path: str      # Path to .pt model file
```

#### `DemoSampleConfig`

```python
class DemoSampleConfig(BaseModel):
    batch_size: int = 100  # Number of profiles to generate
```

#### `DemoSampleCondition`

```python
class DemoSampleCondition(BaseModel):
    month: Month                  # Month enum (JANUARY...DECEMBER)
    annual_consumption: float     # Annual kWh consumption
```

#### `Month` Enum

```python
class Month(int, Enum):
    JANUARY = 0
    FEBRUARY = 1
    ...
    DECEMBER = 11
```

Can be instantiated from int or string:
```python
Month(3)           # Month.APRIL
Month.APRIL        # Month.APRIL
Month["APRIL"]     # Month.APRIL
```

### Neural Network API

#### `DemoNN`

```python
class DemoNN(nn.Module):
    def forward(self, x: dict[str, torch.Tensor]) -> torch.Tensor
    def sample(self, condition: dict[str, torch.Tensor]) -> torch.Tensor
```

**Input format:**
```python
{
    "month": torch.Tensor,         # Shape: (batch, 1)
    "annual_consumption": torch.Tensor  # Shape: (batch, 1)
}
```

## Development

### Project Structure

```
profile-generator/
│
├── README.md                              # This file
├── pyproject.toml                         # Project configuration
├── uv.lock                                # Dependency lock file
├── .gitignore                             # Git ignore rules
│
├── src/
│   └── profile_generator/
│       ├── __init__.py                    # Package exports
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   └── demo_nn.py                 # Neural network implementation
│       │
│       └── interfaces/
│           ├── __init__.py
│           │
│           ├── base/                      # Abstract base classes
│           │   ├── __init__.py
│           │   ├── model.py               # ModelInterface ABC
│           │   └── config.py              # Config ABCs
│           │
│           └── demo_model/                # Demo model implementation
│               ├── __init__.py
│               ├── model.py               # DemoModel class
│               └── config.py              # Configurations
│
├── scripts/
│   └── generate_demo_data.py              # Demo script
│
└── tests/
    ├── models/
    │   ├── demo_model_state_dict.pt       # Pre-trained weights
    │   └── test_demo_nn.py                # Neural network tests
    │
    └── interfaces/
        └── test_demo_model.py             # Interface tests
```

### Adding New Models

The architecture supports easy integration of new models:

1. **Create model class** inheriting from `nn.Module`
2. **Create configuration classes** inheriting from base configs
3. **Implement interface** inheriting from `ModelInterface`
4. **Export** in `__init__.py`

Example:

```python
# src/profile_generator/models/my_model.py
class MyModel(nn.Module):
    def forward(self, x):
        # Your implementation
        pass

# src/profile_generator/interfaces/my_model/config.py
class MyModelConfig(ModelConfigABC):
    # Your config fields
    pass

# src/profile_generator/interfaces/my_model/model.py
class MyModelInterface(ModelInterface):
    def __init__(self, model_config: MyModelConfig):
        # Load your model
        pass

    def sample(self, sample_config, **kwargs):
        # Sampling logic
        pass
```

### Code Style

The project follows:
- Python 3.13+ features (type hints, pattern matching)
- Type annotations for all functions
- Pydantic for validation
- Docstrings for public APIs

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=profile_generator

# Run specific test file
pytest tests/models/test_demo_nn.py

# Run with verbose output
pytest -v
```

### Test Structure

- `tests/models/test_demo_nn.py` - Neural network unit tests
  - Initialization tests
  - Forward pass tests
  - Sampling tests with noise

- `tests/interfaces/test_demo_model.py` - Interface tests
  - Input normalization tests
  - Integration tests

### Test Coverage

Current tests cover:
- Model initialization
- Weight initialization
- Forward pass logic
- Noise addition in sampling
- Non-negative clamping
- Input normalization
- Batch processing
- Configuration validation

## Docker Usage

### Building the Image

```bash
# Build the image
docker build -t profile-generator .

# Check image size
docker images profile-generator
```

### Running Commands

#### Demo Data Generation
```bash
# Run demo (default command)
docker run --rm profile-generator

# Or explicitly
docker run --rm profile-generator demo
```

#### Run Tests
```bash
# Run all tests
docker run --rm profile-generator test

# Run with verbose output
docker run --rm profile-generator python -m pytest tests/ -v
```

#### Interactive Shells
```bash
# Python REPL
docker run --rm -it profile-generator shell

# Bash shell
docker run --rm -it profile-generator bash
```

#### Custom Python Scripts
```bash
# Create a custom script
cat > my_generation.py << 'EOF'
from profile_generator.interfaces.demo_model.config import *
from profile_generator.interfaces.demo_model.model import DemoModel

model = DemoModel(DemoModelConfig(model_path='tests/models/demo_model_state_dict.pt'))
profiles = model.sample(
    DemoSampleConfig(batch_size=100),
    DemoSampleCondition(month=Month.DECEMBER, annual_consumption=7500.0)
)
print(f"Generated {profiles.shape[0]} profiles")
print(f"Average consumption: {profiles.mean():.2f}")
EOF

# Run it in Docker
docker run --rm -v $(pwd)/my_generation.py:/app/my_generation.py \
    profile-generator python my_generation.py
```

#### Volume Mounting for Output
```bash
# Save generated data to host
docker run --rm -v $(pwd)/output:/app/output profile-generator python << 'EOF'
import torch
from profile_generator.interfaces.demo_model.config import *
from profile_generator.interfaces.demo_model.model import DemoModel

model = DemoModel(DemoModelConfig(model_path='tests/models/demo_model_state_dict.pt'))
profiles = model.sample(
    DemoSampleConfig(batch_size=50),
    DemoSampleCondition(month=Month.MARCH, annual_consumption=6000.0)
)
torch.save(profiles, '/app/output/profiles.pt')
print('Saved to output/profiles.pt')
EOF
```

### Docker Compose (Optional)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  profile-generator:
    build: .
    image: profile-generator
    volumes:
      - ./output:/app/output
    command: demo

  test:
    build: .
    image: profile-generator
    command: test
```

Run with:
```bash
docker-compose up profile-generator  # Run demo
docker-compose up test               # Run tests
```

### Testing Docker Setup

```bash
# Run comprehensive Docker tests
./test_docker.sh
```

This script tests:
- Docker build
- Help command
- Demo generation
- Default command
- Test suite
- Custom script execution
- Python imports

## Model Details

### Training Data

The demo model (`demo_model_state_dict.pt`) is a pre-trained model with initialized weights. For production use, you would train on actual household energy consumption data.

### Model Parameters

- **Input dimensions:** 2 (month, annual_consumption)
- **Output dimensions:** 96 (15-minute intervals)
- **Parameters:** ~200 (2 linear layers + magic vector)
- **Activation:** None (linear model)
- **Noise:** Gaussian with σ=0.5

### Base Profile Pattern

The model uses a cosine wave as a base pattern:
```python
pattern = 1.5 + cos(linspace(0, 2π, 96))
```

This creates a daily cycle with:
- Peak at midday
- Trough at midnight
- Range: [0.5, 2.5]

### Limitations

1. **Simplified Model:** Demo model is for illustration; production needs training on real data
2. **No Hourly Effects:** Doesn't capture specific hour-of-day patterns (e.g., morning/evening peaks)
3. **No Day-of-Week:** All days assumed identical
4. **No Weather:** Temperature and weather not considered
5. **No Appliance-Level:** Generates aggregate consumption only
6. **Linear Relationships:** Month and consumption effects are linear

### Potential Improvements

- Train on real smart meter data
- Add hour-of-day conditioning
- Include weather variables (temperature, solar radiation)
- Model day-of-week patterns
- Add household demographics as conditions
- Use more sophisticated architectures (RNNs, Transformers)
- Implement uncertainty quantification

## Example Output

For a household with 6500 kWh annual consumption in March:

```
Interval  0 (00:00-00:15): 2.1 kWh
Interval  1 (00:15-00:30): 1.9 kWh
Interval  2 (00:30-00:45): 1.8 kWh
...
Interval 48 (12:00-12:15): 4.2 kWh  # Midday peak
...
Interval 95 (23:45-00:00): 2.3 kWh
```

Profile shape: `(batch_size, 96)`
Profile dtype: `torch.float32`

## Contributing

Contributions are welcome! Areas for improvement:

- Real data integration
- Additional model architectures
- Visualization tools
- Performance optimization
- Documentation enhancements

**To contribute:**
1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass: `pytest`
5. Submit a pull request

## License

Created by Nan Lin (nansense97@gmail.com)
Delft University of Technology
October 15, 2025

## Related Projects

This profile generator is part of a larger energy system modeling project:
- **persona-segmentation** - Predicts consumer behavior personas
- **technology-adoption-agent-based-model** - Simulates technology adoption

---

**Version:** 0.1.0
**Author:** Nan Lin
**Institution:** TU Delft
**Last Updated:** October 2025
