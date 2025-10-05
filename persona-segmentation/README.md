# Dutch Address Persona Segmentation

This project predicts consumer personas for Dutch addresses using a Random Forest classifier trained on LISS panel survey data. It combines demographic data from CBS (Statistics Netherlands), household income statistics, and BAG building information to classify addresses into four distinct consumer behavior types.

## Overview

**What it does:** Predicts which consumer persona a household belongs to based on their address
**Input:** Dutch postcodes (6P4) and house numbers
**Output:** Classification into one of four behavioral personas with demographic features
**Use case:** Understanding consumer behavior for energy technology adoption decisions

### Persona Types

The model predicts one of four consumer personas identified in energy technology adoption research:

- **Class 1: Financially driven** (~12.9% of population)
  - Price-sensitive consumers who prioritize cost savings and economic benefits
  - Key decision factor: Financial return on investment

- **Class 2: Policy driven** (~17.3% of population)
  - Influenced by policies, regulations, and social responsibility
  - Key decision factor: Environmental impact and societal benefits

- **Class 3: Erratic choosers** (~13.1% of population)
  - Inconsistent decision-making patterns across different choices
  - Key decision factor: Variable, difficult to predict

- **Class 4: Comfort driven** (~56.7% of population)
  - Prioritize convenience, comfort, and minimal disruption
  - Key decision factor: Ease of use and comfort level

**Note:** These classifications are based on research into energy technology adoption behavior and may not apply perfectly to all decision contexts.

## Table of Contents

- [Overview](#overview) - What this project does
- [Quick Start](#quick-start) - Get running in 5 minutes
- [Usage Examples](#usage-examples) - Command examples
- [Output](#output) - Understanding results
- [How It Works](#how-it-works) - Model architecture and approach
- [Project Structure](#project-structure) - File organization
- [Development](#development) - Testing and customization
- [Model Performance and Limitations](#model-performance-and-limitations) - Important caveats
- [Data Sources](#data-sources) - Where data comes from
- [Research Background](#research-background) - Academic context
- [Contributing](#contributing) - How to help improve this project

## Quick Start

### Prerequisites

**Required:**
- Docker Desktop installed and running
- 2GB+ available disk space
- Confidential training data files (see Data Requirements below)

**Data Requirements:**
This model requires confidential LISS panel survey data that is NOT included in the repository. You must have:
- `confidential_data/output.csv` - Engineered features from LISS panel
- `confidential_data/data_long_4c.xls` - LISS survey responses with consumer class labels
- `confidential_data/150911-Gemiddeld-besteedbaar-huishoudinkomen-per-postcode-mw.xls` - Income data

These files must be placed in the `confidential_data/` directory before building the Docker container.

### Option 1: Docker (Recommended)

```bash
# Navigate to the project directory
cd persona-segmentation

# Test the setup first (validates all required files are present)
./test_setup.sh

# Build the Docker image (takes 5-10 minutes first time)
docker build -t datasegmentation .

# Run with default addresses (2051ER #2 and 2051NA #13-D)
docker run --rm -v $(pwd)/output:/app/output datasegmentation

# Run with your own addresses
docker run --rm -v $(pwd)/output:/app/output datasegmentation "1011AB" "1021AC" "12" "5A"

# Get help and see all usage options
docker run --rm datasegmentation help

# Test the container health
docker run --rm datasegmentation test
```

### Option 2: Local R Installation

**Prerequisites:**
- R (≥ 4.2) with packages: `dplyr`, `readr`, `readxl`, `ggplot2`, `janitor`, `ranger`, `caret`, `missForest`, `data.table`, `stringr`
- Python 3 with `requests` package
- RStudio (recommended)

**Steps:**
1. Download CBS/BAG data: `python3 download_netherlands_data.py`
2. Ensure confidential data files are in `confidential_data/` directory
3. Open `Datasegmentation.Rmd` in RStudio
4. Run chunks sequentially (recommended) or knit the document
5. Modify postcodes in the final chunk for your specific addresses

**Note:** The Rmd file contains hardcoded file paths that need to be updated to match your local directory structure.

## Usage Examples

### Predict for Specific Addresses

```bash
# Single family homes in different areas
docker run --rm -v $(pwd)/output:/app/output datasegmentation "1011AB" "2051ER" "12" "5"

# Apartment buildings
docker run --rm -v $(pwd)/output:/app/output datasegmentation "1071AA" "3521AB" "45A" "12-D"

# Rural vs Urban comparison
docker run --rm -v $(pwd)/output:/app/output datasegmentation "7411AA" "1012JS" "8" "156"

# Just provide postcodes (uses default house numbers)
docker run --rm -v $(pwd)/output:/app/output datasegmentation "1011AB" "2051ER"

# Get help and see all usage options
docker run --rm datasegmentation help
```

### Parameters

- **Argument 1**: First postcode (6 characters, e.g., "1011AB")
- **Argument 2**: Second postcode (6 characters, e.g., "2051ER")  
- **Argument 3**: First house number (e.g., "12", "5A", "123-C")
- **Argument 4**: Second house number (e.g., "5", "25B", "10-D")

### Input Validation

- Postcodes must be valid Dutch format (4 digits + 2 letters)
- House numbers can include letters and hyphens
- Invalid postcodes will use regional averages

## Output

Results are saved to `./output/user_predictions.csv` with columns:

| Column | Description |
|--------|-------------|
| `bag_id` | Internal identifier (USER_postcode_number) |
| `Postcode` | Input postcode (6-digit Dutch format) |
| `Huisnummer` | Input house number |
| `female` | Regional female proportion used for prediction |
| `age` | Regional average age used for prediction |
| `members` | Regional average household size used for prediction |
| `rental` | Regional rental proportion used for prediction |
| `urban` | Regional urbanization level (1-5) used for prediction |
| `nettohh_z` | Regional income z-score used for prediction |
| `year_built` | Building construction period (default or from BAG data) |
| `square_meters` | Building size in square meters (default or from BAG data) |
| `predicted_persona` | Predicted consumer persona class (Class1-Class4) |

**Note:** The output includes all demographic and housing characteristics used to generate the prediction, allowing you to understand what regional averages were applied for each address.

### Sample Output

```csv
bag_id,Postcode,Huisnummer,female,age,members,rental,urban,nettohh_z,year_built,square_meters,predicted_persona
USER_1011AB_12,1011AB,12,0.52,36,1.9,0.65,5,0.3,Tussen 1971 en 2000,80,Class4
USER_2514JG_5A,2514JG,5A,0.51,40,2.2,0.35,4,0.1,Tussen 1971 en 2000,80,Class2
```

## How It Works

### Data Pipeline

1. **Training Phase** (done once during Docker build):
   - Load LISS panel survey data with known consumer personas
   - Merge with demographic and housing features
   - Apply missing value imputation using missForest
   - Train Random Forest classifier with cross-validation
   - Save trained model for predictions

2. **Prediction Phase** (each time container runs):
   - Accept user-provided postcodes and house numbers
   - Look up regional demographics based on postcode
   - Apply default housing characteristics
   - Use trained model to predict persona
   - Output results with all features used

### Model Architecture

**Algorithm:** Random Forest (ranger implementation)
- **Trees:** 300 decision trees
- **Tuning:** Grid search over mtry (3, 5) and min.node.size (1, 5)
- **Cross-validation:** 3-fold CV on training data
- **Class weights:** Inverse frequency (Class1: 7.75, Class2: 5.78, Class3: 7.63, Class4: 1.76)
- **Importance:** Permutation-based feature importance

**Features (8 total):**
1. `female` - Female population share (0-1)
2. `age` - Average age
3. `members` - Average household size
4. `year_built` - Construction period category (4 levels)
5. `rental` - Rental housing share (0-1)
6. `urban` - Urbanization level (1-5, ordinal)
7. `nettohh_z` - Standardized household income (z-score)
8. `square_meters` - Building surface area

**Missing Value Handling:**
- Training data: missForest imputation (iterative Random Forest)
- Prediction data: Regional demographics fallback (see below)

### Regional Demographics Fallback

**Important:** For new addresses not in the training data, the model uses **regional averages** based on postcode prefix. This is an approximation that assumes demographic similarity within regions.

| Postcode Range | Region | Demographics |
|---------------|---------|--------------|
| 10xx-12xx | Amsterdam | female=0.52, age=36, members=1.9, rental=0.65, urban=5, income_z=0.3 |
| 20xx-27xx | The Hague/Rotterdam | female=0.51, age=40, members=2.2, rental=0.35, urban=4, income_z=0.1 |
| 30xx-39xx | Utrecht | female=0.51, age=38, members=2.3, rental=0.30, urban=4, income_z=0.2 |
| Other | Rest of NL | female=0.50, age=43, members=2.4, rental=0.25, urban=3, income_z=0.0 |

**Building characteristics** (defaults when actual data unavailable):
- `year_built`: "Tussen 1971 en 2000" (most common construction period)
- `square_meters`: 80m² (Dutch average house size)

**Limitations:**
- Regional averages may not reflect specific neighborhood characteristics
- Default building values assume typical Dutch housing
- Predictions are less accurate than training data which had actual household-level features
- No individual-level variation within a region

See `run_datasegmentation_main.R:117` for the `get_regional_demo()` function implementation.

## Project Structure

```
persona-segmentation/
│
├── README.md                              # This file
├── Dockerfile                             # Docker container definition
├── docker-entrypoint.sh                  # Container entrypoint script
├── test_setup.sh                         # Setup validation script
│
├── download_netherlands_data.py          # CBS/BAG data download script
├── run_datasegmentation_main.R           # Main prediction script (executed in Docker)
├── Datasegmentation.Rmd                  # Original R Markdown notebook
│
├── confidential_data/                    # REQUIRED but gitignored
│   ├── output.csv                        #    LISS panel features (engineered)
│   ├── data_long_4c.xls                 #    LISS survey responses with class labels
│   └── 150911-Gemiddeld-besteedbaar-huishoudinkomen-per-postcode-mw.xls  # Income data
│
├── cbs_postcode_data/                   # Downloaded by script, gitignored
│   ├── pc6_2023_v2.xlsx                 #    CBS 6-digit postcode demographics
│   ├── pc5_2023_v2.xlsx                 #    CBS 5-digit postcode demographics
│   ├── pc4_2023_v2.xlsx                 #    CBS 4-digit postcode demographics
│   └── bag_data.csv                      #    3DBAG building data
│
└── output/                               # Results directory (created by Docker)
    └── user_predictions.csv              # Prediction output
```

**Key Files:**

- `run_datasegmentation_main.R` - Core prediction logic, model training, and regional demographics
- `Datasegmentation.Rmd` - Original research notebook (for understanding methodology)
- `download_netherlands_data.py` - Fetches CBS and 3DBAG public data
- `docker-entrypoint.sh` - Handles command-line arguments and help text
- `test_setup.sh` - Validates all required files before Docker build

## Development

### Testing the Setup

```bash
# Validate all required files and data downloads
./test_setup.sh

# Test Docker build without running
docker build -t datasegmentation . --target test

# Run with verbose output
docker run --rm -v $(pwd)/output:/app/output -e R_LIBS_USER=/usr/local/lib/R/site-library datasegmentation
```

### Customizing the Model

1. **Add new features**: Edit `run_datasegmentation_main.R` 
2. **Modify regional demographics**: Update `get_regional_demo()` function
3. **Adjust model parameters**: Change Random Forest hyperparameters
4. **Add new postcodes**: Extend the regional classification logic

### Troubleshooting

**Common Issues:**

| Problem | Cause | Solution |
|---------|-------|----------|
| `test_setup.sh` fails | Missing confidential data files | Ensure `confidential_data/output.csv` and `data_long_4c.xls` exist |
| Docker build fails | Docker Desktop not running or insufficient memory | Start Docker Desktop, allocate >2GB RAM in settings |
| Data download timeout | CBS servers slow or unavailable | Retry later or check network connection |
| Permission denied on output | Output directory not writable | Run `mkdir -p output && chmod 777 output` |
| "Package 'X' not found" | R package installation failed during build | Check Docker build logs, may need proxy or different CRAN mirror |
| Invalid postcode format | Wrong postcode format provided | Use 6-character format: 4 digits + 2 letters (e.g., "1011AB") |
| All predictions are Class4 | Using regional averages (expected) | Class4 is most common (56.7%), predictions may be biased toward it |

**Debug Commands:**

```bash
# Validate setup before building
./test_setup.sh

# Check container health and installed packages
docker run --rm datasegmentation test

# Interactive container access for debugging
docker run --rm -it datasegmentation bash

# Check R package versions
docker run --rm datasegmentation Rscript -e "packageVersion('ranger')"

# View container logs (for running containers)
docker logs <container_id>

# Test with verbose R output
docker run --rm -v $(pwd)/output:/app/output datasegmentation 2>&1 | tee debug.log
```

### Understanding Prediction Quality

**Expected Accuracy:**
- The model is trained on LISS panel data with actual household-level characteristics
- Predictions for new addresses use **regional demographic averages**, not actual household data
- This means predictions are **estimates based on regional patterns**, not individual household behavior

**Confidence Considerations:**
- Higher confidence: Addresses in well-represented regions (major cities)
- Lower confidence: Rural areas, new developments, or unusual postcodes
- No confidence scores are provided - all predictions are point estimates

**Class Distribution Bias:**
- Class 4 (Comfort driven) represents 56.7% of the population
- The model may be biased toward predicting Class 4, especially when using regional averages
- Class 1 and Class 3 are underrepresented (~13% each), so predictions for these classes should be interpreted cautiously

**When to Trust Predictions:**
- Use predictions as **population-level estimates** for regions
- Do NOT use for **individual household decisions** without additional validation
- Best for: Planning, scenario analysis, population segmentation
- Not suitable for: Individual targeting, precise behavioral prediction

## Model Performance and Limitations

### Training Data vs Prediction Data Gap

**Critical Understanding:**

The model is trained on **household-level survey data** with:
- Individual responses to energy technology choice experiments
- Actual household demographics (age, gender, income, education)
- Real housing characteristics (construction year, size, ownership)
- Known behavioral preferences and decision patterns

But predictions for new addresses use **regional averages**:
- No individual household data available
- Demographic estimates based on postcode prefix (2 digits)
- Default building characteristics
- No actual behavioral data

**This gap means:**
- Training accuracy ≠ prediction accuracy
- Predictions are **informed guesses** based on regional patterns
- Individual variation within regions is not captured
- Results should be validated with actual data when possible

### Known Limitations

1. **Regional Aggregation**
   - Only 4 region types defined (Amsterdam, Randstad, Utrecht, Other)
   - Large within-region variation ignored
   - Postcode-level demographics not utilized from CBS data (could be improved)

2. **Default Values**
   - Building characteristics assume typical Dutch housing
   - No integration with actual BAG data for specific addresses
   - Income data is at 4-digit postcode level but averaged to region

3. **Class Imbalance**
   - 56.7% of training data is Class 4
   - Model may over-predict Class 4
   - Rare classes (1, 3) may be under-predicted

4. **Temporal Issues**
   - Training data is from specific time period
   - Demographics and preferences may shift over time
   - No mechanism to update with new behavioral patterns

5. **Missing Features**
   - No neighborhood-level social effects
   - No economic conditions (energy prices, subsidies)
   - No access to actual building registry for specific addresses
   - No individual behavioral or attitudinal data

### Potential Improvements

**Short-term:**
- Add more granular regional demographics (expand from 4 to 10+ regions)
- Integrate actual BAG API lookups for building characteristics
- Use CBS API for postcode-level demographics instead of regional averages
- Output probability distributions instead of point predictions

**Long-term:**
- Validate predictions against ground truth data
- Retrain with updated survey data periodically
- Add calibration to account for regional average bias
- Develop confidence intervals or prediction uncertainty estimates
- Integrate with energy consumption data if available

### Use Case Recommendations

| Use Case | Suitability | Notes |
|----------|-------------|-------|
| Regional planning | Good | Useful for understanding area-level patterns |
| Policy scenario analysis | Good | Can model regional response to policies |
| Marketing segmentation | Moderate | Better with validation data |
| Individual targeting | Poor | Insufficient individual-level accuracy |
| Academic research | Good | Useful as input for ABM or other models |
| Real-time decisions | Poor | No confidence scores, static demographics |

## Data Sources

### Public Data (automatically downloaded)

- **CBS (Statistics Netherlands)** - https://www.cbs.nl/
  - Postcode-level demographic statistics (age, gender, household composition)
  - Housing characteristics (construction year, rental/ownership, urbanization)
  - Files: `pc6_2023_v2.xlsx`, `pc5_2023_v2.xlsx`, `pc4_2023_v2.xlsx`
  - License: Open data under CBS terms of use

- **3DBAG (Dutch 3D Building Dataset)** - https://3dbag.nl/
  - Building footprints, construction years, and surface areas
  - API access for building characteristics
  - File: `bag_data.csv` (downloaded via API)
  - License: CC0 1.0 Universal

### Confidential Data (must be provided separately)

- **LISS Panel (Longitudinal Internet Studies for the Social Sciences)** - https://www.lissdata.nl/
  - Survey responses on energy technology preferences and choices
  - Consumer persona classification (Class 1-4)
  - Household-level demographics and housing characteristics
  - Files: `output.csv`, `data_long_4c.xls`
  - Access: Requires research agreement with CentERdata

- **CBS Household Income Statistics**
  - Disposable household income by 4-digit postcode
  - File: `150911-Gemiddeld-besteedbaar-huishoudinkomen-per-postcode-mw.xls`
  - Access: Public data, but not redistributable

### Data Privacy and Usage

- **DO NOT** commit confidential data files to version control
- **DO NOT** share LISS panel data without proper authorization
- Training data is kept in `confidential_data/` (gitignored)
- Predictions use aggregated regional demographics, not individual data
- Output CSV files may be shared as they contain only synthetic user-provided addresses

## Research Background

This model implements methodology from energy technology adoption research using latent class modeling and Random Forest classification. The four persona types are based on discrete choice experiments examining household preferences for heating technologies.

**Key Research Concepts:**
- Latent class membership based on stated preferences
- Demographic and housing predictors of consumer behavior
- Application to energy transition decision-making

For academic use, please cite the underlying research appropriately.

## License

This code is provided for research and educational purposes.

**Code:** Available under project license terms
**Data:** Multiple sources with different licenses:
- CBS data: Open data with attribution requirement
- 3DBAG: CC0 (public domain)
- LISS Panel: Restricted access, research use only

When using this model, please:
1. Cite the original research on consumer persona classification
2. Acknowledge CBS and 3DBAG data sources
3. Do not redistribute confidential LISS panel data
4. Include disclaimer about prediction limitations when sharing results

## Contributing

Contributions are welcome, particularly:
- Improved regional demographics (more granular postcode mappings)
- Integration with actual CBS API for real-time demographics
- Model enhancements (e.g., probability outputs, confidence intervals)
- Additional validation with ground truth data

**To contribute:**
1. Fork the repository
2. Create a feature branch
3. Test changes with `./test_setup.sh` and Docker build
4. Ensure no confidential data is committed
5. Submit a pull request with clear description

**For questions or issues:**
- Open a GitHub issue with:
  - Your use case and context
  - Error messages or unexpected behavior
  - System info (OS, Docker version)
  - Whether you have the required confidential data files

---

## 🔖 Quick Reference

### Common Commands

```bash
# Setup and validation
./test_setup.sh                                          # Validate all required files

# Docker build
docker build -t datasegmentation .                       # Build container

# Run predictions
docker run --rm -v $(pwd)/output:/app/output datasegmentation                        # Default addresses
docker run --rm -v $(pwd)/output:/app/output datasegmentation "1011AB" "2051ER"      # Custom postcodes
docker run --rm -v $(pwd)/output:/app/output datasegmentation "1011AB" "2051ER" "12" "5A"  # Full custom

# Help and testing
docker run --rm datasegmentation help                    # Show usage help
docker run --rm datasegmentation test                    # Health check

# Debugging
docker run --rm -it datasegmentation bash                # Interactive shell
docker run --rm datasegmentation Rscript -e "packageVersion('ranger')"  # Check package
```

### File Locations

| Type | Location | Description |
|------|----------|-------------|
| Training data | `confidential_data/output.csv` | LISS features (required) |
| Training labels | `confidential_data/data_long_4c.xls` | LISS class labels (required) |
| Income data | `confidential_data/150911-*.xls` | Income statistics (required) |
| CBS data | `cbs_postcode_data/*.xlsx` | Downloaded automatically |
| Predictions | `output/user_predictions.csv` | Output file |
| Main script | `run_datasegmentation_main.R` | Core prediction logic |
| Original notebook | `Datasegmentation.Rmd` | Research notebook |

### Regional Demographics Quick Lookup

| Postcode | Region | female | age | members | rental | urban | income_z |
|----------|--------|--------|-----|---------|--------|-------|----------|
| 10xx-12xx | Amsterdam | 0.52 | 36 | 1.9 | 0.65 | 5 | 0.3 |
| 20xx-27xx | Randstad | 0.51 | 40 | 2.2 | 0.35 | 4 | 0.1 |
| 30xx-39xx | Utrecht | 0.51 | 38 | 2.3 | 0.30 | 4 | 0.2 |
| Other | Rest NL | 0.50 | 43 | 2.4 | 0.25 | 3 | 0.0 |

### Model Quick Facts

- **Algorithm:** Random Forest (ranger)
- **Trees:** 300
- **Features:** 8 (demographics + housing)
- **Classes:** 4 behavioral personas
- **Training data:** LISS panel survey
- **Prediction basis:** Regional demographic averages
- **Use case:** Population-level segmentation
- **NOT for:** Individual targeting

### Troubleshooting Quick Fixes

| Error | Fix |
|-------|-----|
| Setup fails | Check `confidential_data/` has required files |
| Build fails | Ensure Docker Desktop running, >2GB RAM |
| Permission denied | `mkdir -p output && chmod 777 output` |
| All Class4 predictions | Normal with regional averages (56.7% baseline) |

---

**Version:** 2.0 (Containerized)
**Author:** Louison Thépaut (original), Adapted for Docker deployment
**Last Updated:** 2025