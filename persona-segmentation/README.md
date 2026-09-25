# Dutch address persona segmentation

Give it a list of Dutch addresses (postcode, house number and, ideally, the BAG ID) and it
returns a predicted motivational persona for each address, using a random forest trained on
LISS panel data and scored with open data (CBS postcode statistics and the BAG building
registry). Everything is one R Markdown file, `persona_assignment.Rmd`, which sources
nothing else. You do not need the survey data and you do not train anything: the trained
forest ships with the repository as `models/persona_rf.rds`.

Personas (the classes of the forest):

| Class  | Label       | Letter framing |
|--------|-------------|----------------|
| Class1 | Financially | financial savings |
| Class2 | Policy      | policy / collective |
| Class3 | Erratic     | receives the Comfort letter (see below) |
| Class4 | Comfort     | comfort / wellbeing |

The forest is a four-class model. When a persona is deployed as a letter framing, predicted
Erratic households receive the Comfort letter. Both the raw four-class prediction
(`persona_class4`) and the deployed persona (`persona`) are in the output.

## Quick start with Docker

The image contains R, the packages, the Rmd and the model. The open data (about 8 GB) lives
on a Docker volume, so it is downloaded once and reused.

```bash
cd persona-segmentation
docker build -t persona-segmentation .

# Once: download the CBS and BAG open data into the volume "persona-data"
docker run --rm -v persona-data:/data persona-segmentation download

# Predict for postcode + house number pairs
docker run --rm -v persona-data:/data -v $(pwd)/output:/app/output \
  persona-segmentation 1011AB 12 2514JG 20

# Predict for an address file (CSV or XLSX, see "Your address file")
docker run --rm -v persona-data:/data -v $(pwd)/output:/app/output \
  -v $(pwd)/addresses.csv:/app/input.csv persona-segmentation /app/input.csv

# Other commands: help, test (packages, model, data), bash
docker run --rm persona-segmentation help
```

The first prediction reads the BAG geopackage and writes the cache. In Docker Desktop on a
Mac this took about 30 minutes and 13 GB of memory, so give Docker at least 16 GB (Settings >
Resources). Later runs read the cache and take one to two minutes. Results go to `output/persona_predictions.csv` and `.xlsx`. Set
`PERSONA_CBS_YEAR` and `PERSONA_INCOME_YEAR` with `-e` to use other CBS years, and
`PERSONA_REBUILD_CACHE=TRUE` after downloading new data. `./test_docker_complete.sh` builds
the image and runs every command above.

## Quick start in RStudio

1. Clone or download this repository. Install R (4.1 or later) and RStudio; the Rmd
   installs the packages it needs (see *Requirements*).
2. Download the open data (next section) into one folder, e.g. `~/persona-data`, by hand or
   with `python3 download_netherlands_data.py ~/persona-data 2025 2023`.
3. Open `persona_assignment.Rmd`, edit the `config` chunk: `data_dir`, `cbs_year`,
   `income_year`, and `addresses` (your CSV/XLSX, or a few addresses typed in).
4. Knit it, or run it chunk by chunk. The first run reads the raw open data once (the BAG
   geopackage is the slow step, a few minutes) and writes a CSV cache in `data_dir/cache/`;
   every later run reads the cache and takes seconds. Results go to
   `output/persona_predictions.csv` and `.xlsx`, and the knitted HTML shows the model card,
   the matching diagnostics and the persona distribution.

The Rmd finds its own folder (and therefore `models/persona_rf.rds`) when knitted or run
from RStudio; if that fails it says so and you set `repo_dir` in the config chunk.

## Requirements

R packages: `tidyverse`, `data.table`, `janitor`, `readxl`, `writexl`, `ranger`, and `sf`
for the first run only (reading the BAG geopackage). The `libraries` chunk installs what is
missing.

```r
install.packages(c("tidyverse", "data.table", "janitor", "readxl", "writexl", "ranger", "sf"))
```

The model was trained with `ranger`; a different `ranger` version prints a note but still
predicts.

## Open data: what to download and where

Put everything under one folder (`data_dir`). Sub-folders are fine, the Rmd searches
recursively. Keep the original file names.

### CBS "Kerncijfers per postcode"

Page: <https://www.cbs.nl/nl-nl/dossier/nederland-regionaal/geografische-data/gegevens-per-postcode>
(section *Downloads*). Each year has three zips, one per postcode level (PC4, PC5, PC6).
Each zip contains an Excel file such as `pc6_2025_v1.xlsx`; that Excel file is what the
Rmd reads.

CBS publishes three years at a time and fills them in over time: the newest year is a first
version (`v1`), the previous year a second version (`v2`), the oldest a final version (`vol`).
Household income arrives late, so it is normally only in the `vol` files. You therefore
need two years:

- `cbs_year`: the year of the demographics (sex, age, household size, rental share,
  urbanity). Download PC6, PC5 and PC4 for this year. Newest available is fine.
- `income_year`: the newest year whose PC5 and PC4 files contain *Gemiddeld inkomen*
  (mean household income). Download PC5 and PC4 for this year. Normally `cbs_year - 2`.

At the time of writing (September 2026) that means `cbs_year = 2025` (v1 files) and
`income_year = 2023` (vol files). If you pick an `income_year` whose files have no income
column, the Rmd stops and says so.

CBS requires attribution when you use these figures.

### BAG (building registry)

`bag-light.gpkg` from the PDOK BAG Atom feed:
<https://service.pdok.nl/lv/bag/atom/bag.xml> (direct link
<https://service.pdok.nl/lv/bag/atom/downloads/bag-light.gpkg>). It is several GB. Only the
`verblijfsobject` layer is read, without geometry: BAG IDs, floor area, construction year
and the address fields. Source: Kadaster.

### The cache

The first run writes, in `data_dir/cache/`:

| File | Content |
|------|---------|
| `cbs_pc6_<year>.csv`, `cbs_pc5_<year>.csv`, `cbs_pc4_<year>.csv` | female share, mean age, household size, rental share, WOZ value, urbanity, income z-score per postcode level |
| `bag_verblijfsobjecten.csv` | one row per verblijfsobject: IDs, floor area, construction year, address key |
| `open_data_meta_<year>.csv` | income mean/SD used for the z-score, population fall-back values, source file names |

Set `rebuild_cache <- TRUE` in the config chunk to rebuild the cache (new CBS release, new
BAG extract).

## Your address file

CSV or XLSX, one row per address. Column names are matched loosely (`Postcode 6`, `BAG ID`,
`Nummeraanduiding (Bag ID)`, `Huisnummer` all work); the detected mapping is printed. If
auto-detection picks the wrong column, force it with `address_col_map` in the config chunk.
`addresses_sheet` and `addresses_skip` handle workbooks with several sheets or title rows.

| Column | Required | Notes |
|--------|----------|-------|
| postcode | yes | `1011AB`; spaces and lower case are fine |
| huisnummer | yes (unless a BAG ID is given) | `12`, `12A`, `12-D`, `10-2`; letter and toevoeging may also be separate columns |
| bag_id | recommended | 16-digit BAG nummeraanduiding ID (a verblijfsobject ID also works) |

BAG IDs are repaired automatically: leading zeros that Excel dropped are restored
(`363200000123456` becomes `0363200000123456`), spurious extra zeros are removed, and IDs
that were saved in scientific notation (`1.96e+15`, digits lost) are flagged and the
address is matched on postcode and house number instead. `bag_id_status` in the output says
what happened to each ID. The file is read with every column as text, so nothing is
rounded on the way in.

`examples/addresses_example.csv` shows the format.

## Output

`output/persona_predictions.csv` (and the same table as `.xlsx`): your columns exactly as
they were, followed by

| Column | Meaning |
|--------|---------|
| `bag_id_clean`, `bag_id_status` | the repaired 16-digit ID and what was done to it |
| `bag_match` | how the address was matched to the BAG: `nummeraanduiding`, `verblijfsobject`, `address` (postcode + house number) or `none` |
| `oppervlakte_m2`, `bouwjaar`, `year_built` | floor area, construction year and its LISS category |
| `female`, `age`, `members`, `rental`, `urban`, `nettohh_z`, `square_meters` | the model features as used |
| `cbs_fallback` | which CBS variables came from PC5 or PC4 because the PC6 value was suppressed, e.g. `income_z<-pc4` |
| `imputed_features` | features filled with population fall-backs because no data existed at any level (rare: invalid postcode, no BAG match) |
| `persona_class4`, `persona_class4_label` | the forest's four-class prediction |
| `persona`, `persona_label` | the deployed persona after Erratic -> Comfort |

If one of the appended column names already exists in your file, the appended copy gets a
`_model` suffix.

## How an address becomes a persona

1. BAG: matched by nummeraanduiding ID, then by verblijfsobject ID, then by postcode +
   house number (+ letter/toevoeging). Gives floor area and construction year. Placeholder
   values (area outside 10 to 2000 m2, implausible years) are treated as missing.
2. CBS: for each variable the PC6 value is used when CBS publishes it (at least five
   residents or dwellings), otherwise PC5, otherwise PC4. CBS missing-value codes (`-99997`
   and similar) are never treated as numbers.
3. Features: female share, mean age (from age bands), mean household size, rental share
   (CBS publishes the huur/koop split as percentages), urbanity (1 to 5), construction-year
   category, floor area, and household income as a z-score.
4. Income z-score: the field side is standardised on the mean and SD of the CBS postcode
   incomes of `income_year`; the survey side was standardised on its own mean and SD. A
   split in the forest therefore means "this many SDs above the population mean" on both
   sides, and inflation between survey year and CBS year cancels out.
5. Anything still missing gets a population fall-back (medians from the open data, or from
   the training data as a last resort) and is listed in `imputed_features`.
6. The forest predicts one of four classes; Class3 (Erratic) is folded into Class4
   (Comfort) for deployment.

## Model card

Printed in Step 2 of the Rmd and stored inside the bundle (`bundle$training`): training
date and size, class weights,
cross-validated tuning (mtry, split rule, minimum node size), four-class out-of-bag error and
confusion matrix, per-class recall, precision and lift, the same confusion matrix after the
Erratic -> Comfort fold, and permutation importance.

The shipped model (trained 2026-09-17):

- 2,212 LISS respondents: 289 Financially, 419 Policy, 279 Erratic, 1,225 Comfort.
- `ranger` 0.18.0, 1,000 trees, class-weighted; tuning picked mtry = 2, extratrees,
  minimum node size 10.
- Cross-validated accuracy 0.555 with kappa 0.014. Always predicting Comfort scores 0.554,
  so the forest adds little over the class shares.
- Out-of-bag accuracy of the weighted forest 0.343. Recall per class 0.27 to 0.39; lift
  over the class share 1.17 (Policy) to 1.75 (Erratic).
- Most important feature: rental share. The other seven features matter about equally.

```
OOB confusion (rows = true, cols = predicted)
         Class1 Class2 Class3 Class4
Class1       79     68     69     73
Class2       82    130     88    119
Class3       54     81    108     36
Class4      249    310    224    442
```

The per-respondent out-of-bag predictions that `ranger` stores were removed from the
published bundle; prediction does not use them.

## Retraining

The model is trained from LISS panel data with a private version of this Rmd (same
functions and steps, plus the training chunks). Neither the survey data nor the training
code is in this repository. The bundle records how it was trained: missForest imputation,
10-fold cross-validated tuning on the four-class problem, a class-weighted `ranger` forest
with permutation importance, diagnostics on the four-class forest, and only then packaging
with the Erratic -> Comfort deployment rule.

## Repository layout

```
persona_assignment.Rmd           the whole pipeline: config, functions, open data, model, prediction, output
models/persona_rf.rds            trained random forest + everything prediction needs
examples/addresses_example.csv   input format
download_netherlands_data.py     downloads the CBS and BAG open data
Dockerfile, docker-entrypoint.sh the Docker image and its commands
test_setup.sh                    checks the files and the open data before a Docker build
test_docker_complete.sh          builds the image and runs every documented command
output/                          written by the Rmd (not committed)
```

## Limitations

- CBS suppresses small postcodes; roughly one address in three needs a PC5 or PC4 value for
  at least one variable. The fall-back is recorded per address, so you can filter on it.
- The forest predicts from neighbourhood and building characteristics, not from the
  household itself. Treat the persona as a prior, not a diagnosis.
- Column headers in CBS files change between releases. The readers match on names
  (`CBS_VARS` in the functions chunk) and stop with the list of headers they found when a
  required one is missing, so a rename costs one line of edit.
- BAG light column names are those of the PDOK geopackage at the time of writing; the
  reader checks them and stops with the list of columns present if they changed.

## Research background and data use

The four personas come from a latent class analysis of a discrete choice experiment on
household heating technologies (Nikoloski et al., 2025). Cite that work when you use the
personas.

- CBS data: open data; CBS requires attribution.
- BAG: open data from Kadaster via PDOK.
- LISS panel: restricted access, research use only. The survey data is not in this
  repository; only the trained model and aggregate training statistics are.
