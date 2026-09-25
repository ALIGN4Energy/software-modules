# Energy Model Tutorial

This tutorial demonstrates how to use the three energy models in this repository:
1. **Persona Segmentation** - Predict consumer personas for Dutch households
2. **Profile Generator** - Generate synthetic daily energy consumption profiles
3. **Technology Adoption ABM** - Simulate household energy technology adoption decisions

## Table of Contents

- [Prerequisites](#prerequisites)
- [Part 1: Persona Segmentation Model](#part-1-persona-segmentation-model)
- [Part 2: Profile Generator](#part-2-profile-generator)
- [Part 3: Technology Adoption ABM](#part-3-technology-adoption-abm)
- [Part 4: Combining All Models](#part-4-combining-all-models)
- [Data File Formats](#data-file-formats)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker installed and running

## Part 1: Persona Segmentation Model

### Overview

The persona segmentation model predicts which of four behavioral consumer types a Dutch household belongs to based on their postcode and house number:

- **Class 1 - Financially driven** (~12.9%): Focus on cost-effectiveness and return on investment
- **Class 2 - Policy driven** (~17.3%): Motivated by government incentives and environmental policies
- **Class 3 - Erratic choosers** (~13.1%): Inconsistent decision patterns
- **Class 4 - Comfort driven** (~56.7%): Prioritize comfort and convenience over cost

The model uses CBS postcode statistics and BAG building data for each address. Treat the prediction as a prior, not a diagnosis: the model is only slightly better than chance (see the model card in [persona-segmentation/README.md](persona-segmentation/README.md#model-card)).

### Running with Docker

```bash
cd persona-segmentation

# Build the Docker image
docker build -t persona-segmentation .

# Download the open data once (about 8 GB, kept in the Docker volume "persona-data")
docker run --rm -v persona-data:/data persona-segmentation download

# Predict for postcode + house number pairs
docker run --rm -v persona-data:/data -v $(pwd)/output:/app/output persona-segmentation 1011AB 12 2514JG 20

# View results
cat output/persona_predictions.csv
```

The first prediction builds a cache from the BAG data. This takes up to 30 minutes and needs about 13 GB of memory, so give Docker at least 16 GB. Later runs take one to two minutes.

### Input Format

Give postcode and house number pairs on the command line, or an address file (CSV or XLSX with columns `postcode`, `huisnummer` and optionally `bag_id`):

```bash
docker run --rm -v persona-data:/data -v $(pwd)/output:/app/output \
  -v $(pwd)/addresses.csv:/app/input.csv persona-segmentation /app/input.csv
```

See `persona-segmentation/examples/addresses_example.csv` for the file format.

### Output Format

The model writes `output/persona_predictions.csv` and `output/persona_predictions.xlsx`: your input columns, followed by

| Column | Description |
|--------|-------------|
| `bag_id_clean`, `bag_id_status` | Repaired 16-digit BAG ID and what was done to it |
| `bag_match` | How the address was matched to the BAG (`nummeraanduiding`, `verblijfsobject`, `address` or `none`) |
| `oppervlakte_m2`, `bouwjaar`, `year_built` | Floor area, construction year and its category |
| `female`, `age`, `members`, `rental`, `urban`, `nettohh_z`, `square_meters` | Model features, from CBS postcode statistics and the BAG |
| `cbs_fallback` | CBS variables taken from PC5 or PC4 because the PC6 value is suppressed |
| `imputed_features` | Features filled with population averages because no data was found |
| `persona_class4`, `persona_class4_label` | The model's four-class prediction |
| `persona`, `persona_label` | The persona to use, with Erratic folded into Comfort |

### Example Output

Selected columns for `examples/addresses_example.csv` (four city halls):

```csv
postcode,huisnummer,bag_match,year_built,rental,urban,nettohh_z,persona_class4_label,persona_label
1011PN,1,nummeraanduiding,Tussen 1971 en 2000,0.80,1,-0.14,Comfort,Comfort
2511BT,70,nummeraanduiding,Tussen 1971 en 2000,1.00,1,-0.26,Policy,Policy
3011AD,40,address,Vóór 1940,0.90,1,-1.07,Policy,Policy
3521AZ,1,nummeraanduiding,In 2001 of later,0.80,1,0.59,Financially,Financially
```

City halls have no residents in their own PC6 postcode, so the CBS values come from PC5 (`cbs_fallback`). Their office floor areas are outside the residential range, so `square_meters` is a population fall-back (`imputed_features`).

## Part 2: Profile Generator

### Overview

The profile generator creates synthetic annual energy consumption profiles for households using a PyTorch-based neural network. It generates **12 monthly profiles**, each with 96 data points per day (15-minute intervals).

**Inputs:**
- **Annual consumption** (kWh): Total yearly energy usage
- **Technology adoption**: Heat pump, solar panels, electric vehicle
- **Month**: Automatically generates profiles for all 12 months

**Output:**
- JSON file with daily profiles for each month
- Each profile has 96 intervals (15 minutes each = 24 hours)
- Includes statistics (min, max, mean) per month

**Use cases:**
- Generate synthetic energy consumption data for simulation
- Create realistic daily usage patterns for the ABM
- Test energy system models with varied consumption profiles
- Analyze seasonal variation and technology impacts

### Running with Docker

```bash
cd profile-generator

# Build the Docker image
docker build -t profile-generator .

# Generate profile for basic household (6500 kWh/year)
docker run --rm -v $(pwd)/output:/app/output profile-generator generate \
  --annual_consumption 6500 \
  --output output/household_profile.json

# Generate profile for household with heat pump
docker run --rm -v $(pwd)/output:/app/output profile-generator generate \
  --annual_consumption 7500 \
  --has_heatpump true \
  --output output/heatpump_household.json

# Generate profile with all technologies
docker run --rm -v $(pwd)/output:/app/output profile-generator generate \
  --annual_consumption 9000 \
  --has_heatpump true \
  --has_solar true \
  --has_ev true \
  --output output/fully_electrified.json

# Get help
docker run --rm profile-generator generate --help
```

### CLI Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--annual_consumption` | **Yes** | - | Annual energy consumption in kWh |
| `--has_heatpump` | No | false | Household has heat pump |
| `--has_solar` | No | false | Household has solar panels |
| `--has_ev` | No | false | Household has electric vehicle |
| `--output` | No | output/profile.json | Output JSON file path |

**Note:** The current demo model only uses `annual_consumption`. The full trained model will incorporate technology parameters (`has_heatpump`, `has_solar`, `has_ev`) as neural network inputs.

### Output Format

The CLI generates a JSON file with annual profiles:

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
    // ... 12 monthly profiles total
  ]
}
```

**Time intervals:**
- 96 intervals per day = 15 minutes each
- Interval 0: 00:00-00:15
- Interval 48: 12:00-12:15 (typically peak)
- Interval 95: 23:45-00:00

### Example Output

For a household with 7500 kWh annual consumption and heat pump:

```
=== PROFILE GENERATION STARTING ===
Annual consumption: 7500.0 kWh
Heat pump: True
Solar panels: False
Electric vehicle: False

Loading model...
Model loaded successfully

Generating profiles for 12 months...
Profiles saved to output/heatpump_household.json

=== GENERATION SUMMARY ===
Months generated: 12
Intervals per day: 96 (15-minute resolution)
Total data points: 1152

Profile statistics (average across all months):
  Average consumption: 2.45
  Min consumption: 0.32
  Max consumption: 5.12

=== GENERATION COMPLETED ===
```

## Part 3: Technology Adoption ABM

### Overview

The Agent-Based Model (ABM) simulates household adoption decisions for energy technologies (heat pumps, solar PV, district heating, etc.) over multiple years. Each household is assigned a latent class and makes decisions based on:

- Cost and affordability
- Policy support availability
- Payback time
- CO2 savings
- Comfort improvements
- Installation disruption
- Peer effects (neighbor adoption)

### Data Preparation

#### Step 1: Create Household Data CSV

Create a file `tutorial_households.csv` with household characteristics:

```csv
Agent_id,Income,Savings,Age_group,Is_owner,Has_children,Renovation_experience,Education_level,Female,Partner,Energy_use
1,3500.00,12000.00,2,TRUE,TRUE,TRUE,4,FALSE,TRUE,2800.00
2,4200.00,18000.00,3,TRUE,FALSE,TRUE,5,TRUE,FALSE,2400.00
3,2800.00,8000.00,1,FALSE,TRUE,FALSE,3,TRUE,TRUE,3200.00
4,5000.00,25000.00,4,TRUE,FALSE,TRUE,6,FALSE,TRUE,2600.00
5,3200.00,10000.00,2,TRUE,TRUE,FALSE,4,FALSE,TRUE,3000.00
```

**Column Definitions:**

| Column | Type | Range/Values | Description |
|--------|------|--------------|-------------|
| `Agent_id` | integer | 1+ | Unique household identifier |
| `Income` | float | >0 | Monthly household income (euros) |
| `Savings` | float | ≥0 | Current household savings (euros) |
| `Age_group` | integer | 0-4 | Age category: 0=25-34, 1=35-44, 2=45-54, 3=55-64, 4=65+ |
| `Is_owner` | boolean | TRUE/FALSE | Home ownership status |
| `Has_children` | boolean | TRUE/FALSE | Presence of children in household |
| `Renovation_experience` | boolean | TRUE/FALSE | Previous home renovation experience |
| `Education_level` | integer | 1-6 | Education level (1=lowest, 6=highest) |
| `Female` | boolean | TRUE/FALSE | Female head of household |
| `Partner` | boolean | TRUE/FALSE | Living with partner |
| `Energy_use` | float | >0 | Annual energy consumption (kWh) |

#### Step 2: Create Technology Configuration CSV

Create a file `tutorial_technologies.csv` defining available technologies:

```csv
technology,base_cost,cost_per_kwh_unit,payback_years,co2_savings_pct,comfort_level,disruption_level,policy_support_available,co2_factor
heat_pump,7000,600,12,0.6,2,2.0,2,0.04
solar_pv,9000,700,15,0.7,1,1.0,2,0.02
district_heating,4000,400,8,0.4,1,1.5,2,0.20
hybrid_heating,5500,500,10,0.5,2,1.0,1,0.15
```

**Column Definitions:**

| Column | Type | Range | Description |
|--------|------|-------|-------------|
| `technology` | string | - | Technology name (use underscores, not spaces) |
| `base_cost` | float | >0 | Fixed installation cost (euros) |
| `cost_per_kwh_unit` | float | >0 | Running cost per 1000 kWh of household energy use |
| `payback_years` | float | >0 | Years to recover investment through savings |
| `co2_savings_pct` | float | 0-1 | CO2 emissions reduction (0.5 = 50% reduction) |
| `comfort_level` | integer | 0-2 | Comfort: 0=status quo, 1=standard, 2=advanced |
| `disruption_level` | float | 0-3 | Installation disruption: 0-1=quick, 1-2=temporary, 2-3=extended |
| `policy_support_available` | integer | 1-2 | 1=no support, 2=support available |
| `co2_factor` | float | 0-0.5 | CO2 emissions per kWh (kg CO2/kWh) |

**Cost Calculation Formula:**

For each household, the actual technology cost is calculated as:

```
Total Cost = base_cost + cost_per_kwh_unit × ⌈energy_use / 1000⌉
```

**Example**: For a household using 2750 kWh with heat_pump (base=7000, per_unit=600):
```
Total Cost = 7000 + 600 × ⌈2750/1000⌉ = 7000 + 600 × 3 = 8800 euros
```

### Running the ABM with Docker

```bash
cd technology-adoption-agent-based-model

# Build the Docker image
docker build -t technology-adoption-abm .

# Run with tutorial data (100 runs, 10 years)
docker run --rm \
  -v $(pwd):/app \
  technology-adoption-abm \
  --household_data tutorial_households.csv \
  --tech_config tutorial_technologies.csv

# Custom parameters
docker run --rm \
  -v $(pwd):/app \
  technology-adoption-abm \
  --household_data tutorial_households.csv \
  --tech_config tutorial_technologies.csv \
  --n_runs 200 \
  --years 15 \
  --policy true \
  --peer_effect 0.3

# Use custom data files
docker run --rm \
  -v $(pwd):/app \
  technology-adoption-abm \
  --household_data my_households.csv \
  --tech_config my_technologies.csv

# View results
cat output/summary_statistics.txt
```

### ABM Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `--household_data` | string | **Yes** | - | Path to household CSV file |
| `--tech_config` | string | **Yes** | - | Path to technology config CSV |
| `--n_runs` | integer | No | 100 | Number of Monte Carlo simulation runs |
| `--years` | integer | No | 10 | Simulation years per run |
| `--policy` | boolean | No | true | Enable government policy support |
| `--peer_effect` | float | No | 0.2 | Peer influence strength (0-1) |
| `--output_dir` | string | No | output | Output directory for results |

### ABM Output Files

#### 1. `monte_carlo_results.csv`

Detailed results from all simulation runs:

```csv
run,heat_pump_adoption_rate,solar_pv_adoption_rate,district_heating_adoption_rate,...
0,0.2,0.0,0.6,...
1,0.4,0.2,0.4,...
```

#### 2. `summary_statistics.txt`

Aggregated statistics across all runs:

```
=== MONTE CARLO RESULTS ===
Runs: 100
Years: 10
Policy Support: True
Peer Effect: 0.2

=== OVERALL ADOPTION RATES ===
Heat Pump: 0.325 ± 0.145 [95% CI: 0.150-0.550]
Solar Pv: 0.125 ± 0.098 [95% CI: 0.000-0.300]
District Heating: 0.480 ± 0.178 [95% CI: 0.200-0.750]

=== ADOPTION BY LATENT CLASS ===

Class 1 - Financially driven (~12.9%) (avg size: 1)
  Heat Pump: 0.245 ± 0.312 [95% CI: 0.000-0.800]
  Solar Pv: 0.089 ± 0.195 [95% CI: 0.000-0.500]
  ...
```
