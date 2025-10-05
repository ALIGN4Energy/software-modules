REL Datasegmentation v2 — User Guide (interactive run)
Author: Louison Thépaut
Date: 2025-08-25
Purpose: Train a weighted Random Forest on LISS-based labels and predict persona classes for new addresses using CBS postcode features and BAG building attributes. Personas follow Nikoloski et al. (2025).
What you need
Software
	R (≥ 4.2 recommended). RStudio.
Input files (update paths to your machine)
	output.csv — engineered variables keyed by nomem_encr (LISS).
	data_long_4c.xls — training data with class_4class (Marjan’s survey).
	CBS 2023 Excel files:
o	pc6_2023_v2.xlsx, pc5_2023_v2.xlsx, pc4_2023_v2.xlsx.
	Income table: 150911-Gemiddeld-besteedbaar-huishoudinkomen-per-postcode-mw.xls (sheet “Tabel 1”).
	BAG: bag_data.csv (with bag_id, oppervlakte_m2, bouwjaar).
(A GeoPackage workflow is shown but commented out.)
	Address list Excel to score (REL format), with Postcode 6,  and  Bag ID. I cannot share this as it is confidential data provided by REL.
Update the hard-coded file paths in the script to your own folders (AKA all filepaths need to be set.
Personas (Nikoloski et al., 2025)
	Class 1 — Financially driven (~12.9%)
	Class 2 — Policy driven (~17.3%)
	Class 3 — Erratic choosers (~13.1%)
	Class 4 — Comfort driven (~56.7%)
These shares are used to define inverse-prevalence class weights.
How to run (interactive)
You run the script by chunks inside R/RStudio. No knitting needed. The package block will install any missing packages automatically.
What each chunk does:
Chunk 1 — Setup, packages, training data, preprocessing
	Clears the environment: rm(list = ls()).
	Ensures required packages are installed and then loads them.
	Loads training data:
o	new_vars from output.csv (cleaned names).
o	df_model_unique from data_long_4c.xls.
	Engineers members = 1 + partner + children and prints a quick sanity check.
	Sets variable types for modeling:
o	educat and urban as ordered factors (with urban shifted to 1–5),
o	categorical variables (occupation, year_built, rental, partner, female) as factors,
o	children as integer.
	Merges df_model_unique and new_vars by nomem_encr → merged_df.
	Standardizes income to nettohh_z. This is to account for inflation, so rather than looking at raw values we look at deviation from the average
	Defines class weights from persona shares.
	Selects the modeling frame (rf_training) with target class_4class and aligned predictors.
	Runs missForest to impute missing values → rf_training_imputed and prints the OOB imputation error.
Output after this chunk: rf_training_imputed ready for modeling.

Chunk 2 — Random Forest training (CV + final model)
	Converts class_4class to a factor labeled "Class1"–"Class4".
	Sets up 10-fold cross-validation with caret::train over a grid of:
o	mtry = 2:8, splitrule ∈ {gini, extratrees}, min.node.size ∈ {1,3,5,10,20}.
	Trains with 1,000 trees, permutation importance, and class weights.
	Prints the CV summary and plots the tuning results.
	Fits a final ranger model (final_rf_model) on all imputed data using the best hyperparameters; prints the model.
Output after this chunk: final_rf_model trained and ready to score.
Chunk 3 — Open data prep (CBS 2023 + Income + BAG)
	Reads CBS PC6/PC5/PC4 Excel files (sheet 1, skip headers) and cleans names.
	Converts numeric columns (replacing -99997 with 0) and computes postcode-level features:
o	female_share, avg_age, avg_build_year, rental_share, woz_corrected.
	Joins PC6 → PC5 → PC4 and builds a fallback table where PC6 gaps are filled from PC5/PC4.
	Reads the PC4 income table (sheet “Tabel 1”), creates income_z with reference mean 34,500 (To be updated if more recent data becomes available from CBS), and merges into fallback by postcode_4.
	Loads BAG from bag_data.csv and derives year_built_cat into four bins to match the LISS panel data:
o	Vóór 1940, Tussen 1940 en 1970, Tussen 1971 en 2000, In 2001 of later.
Output after this chunk:
	fallback — postcode-level feature table by PC6 with fallbacks and income_z.
	bag_data — building features with year_built_cat.
Chunk 4 — Read the address list to score
	Opens the address Excel (sheet “4. Woningen”), keeps the first 4 columns.
	Renames for consistency: Postcode = "Postcode 6", Huisnummer = "Huisnummer".
	Casts Postcode and Huisnummer to character.
Output after this chunk: addresses_clean.
Chunk 5 — Assemble the scoring dataset
	Renames Nummeraanduiding (Bag ID) → bag_id.
	Joins BAG features by bag_id and fallback postcode features by PC6 (Postcode).
	Renames merged columns to match the model’s training schema:
o	female, age, members, year_built, rental, nettohh_z, square_meters.
Output after this chunk: test_dataset — ready for prediction.
Chunk 6 — Predict persona classes & quick visualization
	Predicts class labels with predict(final_rf_model, data = test_dataset, type = "response").
	Stores the predicted class in test_dataset$predicted_persona.
	Also calls predict(..., type = "response")$predictions to attach the returned matrix (as available) as class probabilities.
	Prints a frequency table and a bar chart of the predicted class distribution.
Final output:
	test_dataset contains all features, predicted_persona, and (if available) per-class probability columns.
	A simple bar chart for a quick sanity check.
If you want a file:
write.csv(test_dataset, "predicted_personas.csv", row.names = FALSE)
Notes for collaborators (just context, no changes required)
	Paths are set for Louison’s laptop; collaborators must change them.
	CBS layout can change year-to-year (sheet names/column positions); if you swap in a new vintage, recheck the skip= rows and any hard-coded column references.
	The optional BAG GeoPackage workflow is included but commented out; the script currently uses bag_data.csv.

