# Energy Technology Adoption Agent-Based Model

This project simulates household adoption of energy technologies (heat pumps, district heating, PV panels) using an agent-based model based on discrete choice modeling and latent class membership from academic research.

## Model Overview

The ABM simulates household energy technology adoption decisions based on:

- **Latent Class Membership**: Four consumer personas (Financially driven, Policy driven, Erratic choosers, Comfort driven)
- **Individual Preferences**: Heterogeneous utility parameters drawn from class-specific distributions
- **Decision Attributes**: Cost, policy support, payback time, CO2 savings, comfort, disruptiveness
- **Peer Effects**: Network influence from neighboring households
- **Affordability Constraints**: Households can only adopt technologies they can afford

## Quick Start

### Option 1: Docker (Recommended)

**Prerequisites:**
- Docker Desktop installed and running
- 500MB+ available disk space

**Steps:**

```bash
# Test the setup first
./test_setup.sh

# Build the Docker image (takes 2-3 minutes)
docker build -t technology-adoption-abm .

# Run with tutorial data (100 runs, 10 years, policy=true, peer_effect=0.2)
docker run --rm -v $(pwd):/app technology-adoption-abm \
  --household_data tutorial_households.csv \
  --tech_config tutorial_technologies.csv

# Get help
docker run --rm technology-adoption-abm help
```

### Option 2: Local Python Installation

**Prerequisites:**
- Python 3.11+ with packages: `numpy`, `pandas`, `mesa`, `networkx`

**Steps:**

```bash
# Install dependencies
pip install numpy pandas mesa networkx

# Run simulation with tutorial data
python run_abm.py --household_data tutorial_households.csv --tech_config tutorial_technologies.csv

# Or run original script directly (uses hardcoded example data)
python ABM.py
```

## Usage Examples

### Basic Usage

```bash
# Basic run with tutorial data (100 runs, 10 years)
docker run --rm -v $(pwd):/app technology-adoption-abm \
  --household_data tutorial_households.csv \
  --tech_config tutorial_technologies.csv

# Custom Monte Carlo runs and simulation years
docker run --rm -v $(pwd):/app technology-adoption-abm \
  --household_data tutorial_households.csv \
  --tech_config tutorial_technologies.csv \
  --n_runs 50 --years 15

# Get help and see all options
docker run --rm technology-adoption-abm help
```

### Policy Scenarios

```bash
# With policy support (subsidies/incentives)
docker run --rm -v $(pwd):/app technology-adoption-abm \
  --household_data tutorial_households.csv \
  --tech_config tutorial_technologies.csv \
  --policy true

# Without policy support
docker run --rm -v $(pwd):/app technology-adoption-abm \
  --household_data tutorial_households.csv \
  --tech_config tutorial_technologies.csv \
  --policy false
```

### Peer Effect Analysis

```bash
# No peer effects
docker run --rm -v $(pwd):/app technology-adoption-abm \
  --household_data tutorial_households.csv \
  --tech_config tutorial_technologies.csv \
  --peer_effect 0.0

# Strong peer effects
docker run --rm -v $(pwd):/app technology-adoption-abm \
  --household_data tutorial_households.csv \
  --tech_config tutorial_technologies.csv \
  --peer_effect 0.5
```

### Combined Scenarios

```bash
# Comprehensive scenario: 200 runs, 20 years, with policy, strong peers
docker run --rm -v $(pwd):/app technology-adoption-abm \
  --household_data tutorial_households.csv \
  --tech_config tutorial_technologies.csv \
  --n_runs 200 --years 20 --policy true --peer_effect 0.3

# Quick test: 20 runs, 5 years
docker run --rm -v $(pwd):/app technology-adoption-abm \
  --household_data tutorial_households.csv \
  --tech_config tutorial_technologies.csv \
  --n_runs 20 --years 5

# Custom data files
docker run --rm -v $(pwd):/app technology-adoption-abm \
  --household_data my_households.csv \
  --tech_config my_technologies.csv \
  --n_runs 100 --years 10
```

### Parameters

**Required:**
- `--household_data PATH`: Path to household CSV file (required)
- `--tech_config PATH`: Path to technology config CSV file (required)

**Optional:**
- `--n_runs N`: Number of Monte Carlo simulation runs (default: 100)
- `--years Y`: Simulation years per run (default: 10)
- `--policy true/false`: Enable/disable policy support (default: true)
- `--peer_effect P`: Peer effect strength 0-1 (default: 0.2)
- `--output_dir PATH`: Output directory (default: output)

## Output

Results are saved to `./output/` with two files:

### 1. monte_carlo_results.csv

Detailed results for each simulation run:

| Column | Description |
|--------|-------------|
| `run` | Run number (0 to n_runs-1) |
| `{tech}_adoption_rate` | Overall adoption rate for each technology |
| `class_{1-4}_size` | Number of households in each latent class |
| `class_{1-4}_{tech}_rate` | Adoption rate by latent class and technology |

### 2. summary_statistics.txt

Aggregated statistics across all runs:
- Mean adoption rates with standard deviations and 95% confidence intervals
- Overall adoption by technology type
- Adoption rates broken down by latent class

### Sample Output

```
=== OVERALL ADOPTION RATES ===
Heat Pump: 0.245 ± 0.087 [95% CI: 0.089-0.412]
District Heating: 0.178 ± 0.065 [95% CI: 0.067-0.301]
PV: 0.312 ± 0.093 [95% CI: 0.145-0.487]

=== ADOPTION BY LATENT CLASS ===

Class 1 - Financially driven (~12.9%) (avg size: 13)
  Heat Pump: 0.189 ± 0.156 [95% CI: 0.000-0.462]
  District Heating: 0.134 ± 0.128 [95% CI: 0.000-0.385]
  PV: 0.267 ± 0.172 [95% CI: 0.000-0.538]

Class 2 - Policy driven (~17.3%) (avg size: 17)
  Heat Pump: 0.412 ± 0.198 [95% CI: 0.059-0.765]
  ...
```

## How It Works

### Model Architecture

1. **Agent Creation**: Households initialized with demographics, income, savings, energy use
2. **Latent Class Assignment**: Probabilistic assignment based on household characteristics using multinomial logit
3. **Individual Preferences**: Beta coefficients drawn from class-specific normal distributions
4. **Network Formation**: Random network with Poisson degree distribution (avg 5 neighbors)
5. **Decision Process**: Each year, households calculate utilities for available technologies and choose option with highest utility (including status quo)
6. **Monte Carlo**: Process repeated N times to account for stochastic variation

### Latent Classes (Consumer Personas)

- **Class 1: Financially driven** (~12.9% of population)
  - High sensitivity to costs and payback time
  - Focus on financial returns

- **Class 2: Policy driven** (~17.3% of population)
  - Strong response to policy support and subsidies
  - Motivated by CO2 savings and environmental impact

- **Class 3: Erratic choosers** (~13.1% of population)
  - Inconsistent preferences and high variance
  - Less predictable adoption patterns

- **Class 4: Comfort driven** (~56.7% of population)
  - Prioritize comfort and convenience
  - Most common persona type

### Decision Attributes

Each technology is characterized by:
- **Cost**: Base cost + per-kWh cost × energy use
- **Policy Support**: Binary (1=subsidy available, 0=none)
- **Payback Time**: Years to recover investment (categorized: short/moderate/long)
- **CO2 Savings**: Percentage reduction (categorized: low/moderate/high)
- **Comfort**: Level 1-3 (higher = more comfortable)
- **Disruptiveness**: Installation disruption (categorized: low/moderate/high)

### Utility Calculation

```
Utility = Σ(beta_i × attribute_i) + peer_effect + Gumbel_error

Where:
- beta_i: Individual preference parameter
- attribute_i: Technology attribute value
- peer_effect: peer_strength × (fraction of neighbors who adopted)
- Gumbel_error: Random noise for stochasticity
```

Households choose the option (or status quo) with highest utility, subject to affordability constraints.

## Project Structure

```
technology-adoption-agent-based-model/
├── Dockerfile                 # Container definition
├── docker-entrypoint.sh      # Container entrypoint script
├── README.md                 # This file
├── test_setup.sh             # Setup validation script
├── .dockerignore             # Docker ignore rules
│
├── ABM.py                    # Core agent-based model
├── run_abm.py                # Wrapper script for Docker
│
├── tutorial_households.csv   # Household characteristics (tutorial data)
├── tutorial_technologies.csv # Technology attributes (tutorial data)
│
└── output/                   # Results directory
    ├── monte_carlo_results.csv
    └── summary_statistics.txt
```

## Development

### Testing the Setup

```bash
# Validate all required files
./test_setup.sh

# Test Docker build
docker build -t abm .

# Run container health check
docker run --rm abm test

# Interactive container access
docker run --rm -it abm bash
```

### Customizing the Model

1. **Modify household data**: Edit `household_data.csv`
   - Columns: Agent_id, Income, Savings, Age_group, Is_owner, Has_children, Renovation_experience, Education_level, Female, Partner, Energy_use

2. **Add/modify technologies**: Edit `technology_config.csv`
   - Columns: technology, base_cost, cost_per_kwh_unit, payback_years, co2_savings_pct, comfort_level, disruption_level, policy_support_available, co2_factor

3. **Adjust model parameters**: Modify `ABM.py`
   - Latent class coefficients (lines 50-170)
   - Preference distributions (lines 239-272)
   - Network structure (lines 534-544)

### Running Local Python

```bash
# Basic run (uses hardcoded example data)
python ABM.py

# Using wrapper with custom parameters
python run_abm.py \
  --household_data tutorial_households.csv \
  --tech_config tutorial_technologies.csv \
  --n_runs 50 --years 15 --policy false

# Get help
python run_abm.py --help
```

### Troubleshooting

**Common Issues:**

- **Docker build fails**: Ensure Docker Desktop is running with sufficient memory (>1GB)
- **Permission errors**: Ensure `output/` directory exists and is writable
- **Import errors**: Check Python version (3.11+) and install required packages

**Debug Commands:**

```bash
# Check container logs
docker logs <container_id>

# Interactive container access
docker run --rm -it abm bash

# Container health check
docker run --rm abm test

# Validate Python packages
python -c "import numpy, pandas, mesa, networkx; print('OK')"
```

## Model Background

This ABM is based on discrete choice modeling research on household energy technology adoption. The latent class framework and preference parameters are derived from empirical survey data (LISS panel).

**Key References:**
- Latent class membership coefficients (Tables 5A-8A in research paper)
- Preference parameters by class (Table 4A in research paper)
- Nikoloski et al. (2025) persona framework

## Input File Formats

### household_data_example.csv

```csv
Agent_id,Income,Savings,Age_group,Is_owner,Has_children,Renovation_experience,Education_level,Female,Partner,Energy_use
1,3245.67,6789.45,2,TRUE,FALSE,TRUE,3,FALSE,TRUE,2634.12
2,2890.34,5432.87,1,TRUE,TRUE,FALSE,4,TRUE,TRUE,3156.78
```

- `Income`: Monthly household income (EUR)
- `Savings`: Current savings (EUR)
- `Age_group`: 0=25-34, 1=35-44, 2=45-54, 3=55-64, 4=65+
- `Is_owner`: TRUE if homeowner, FALSE if renter
- `Education_level`: 1-6 (1=lowest, 6=highest)
- `Energy_use`: Annual energy consumption (kWh)

### technology_config_example.csv

```csv
technology,base_cost,cost_per_kwh_unit,payback_years,co2_savings_pct,comfort_level,disruption_level,policy_support_available,co2_factor
heat_pump,6000,500,10,0.5,2,1.5,1,0.05
district_heating,3000,350,7,0.3,1,0.5,2,0.25
PV,8000,600,12,0.6,2,2,2,0.03
```

- `base_cost`: Fixed installation cost (EUR)
- `cost_per_kwh_unit`: Additional cost per 1000 kWh capacity (EUR)
- `payback_years`: Expected payback period (years)
- `co2_savings_pct`: CO2 reduction percentage (0-1)
- `comfort_level`: 1-3 (higher = more comfortable)
- `disruption_level`: Installation disruption (0-3, higher = more disruptive)
- `policy_support_available`: 0=no subsidy, 1=subsidy when policy=true, 2=always subsidized
- `co2_factor`: kg CO2 per kWh

## Contributing

1. Fork the repository
2. Create a feature branch
3. Test your changes with `./test_setup.sh`
4. Submit a pull request

For questions or issues, please open a GitHub issue with details about your use case and any error messages.
