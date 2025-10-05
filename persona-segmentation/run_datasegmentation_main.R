print("=== DATASEGMENTATION SCRIPT STARTING ===")
print(paste("User postcodes:", paste(user_postcodes, collapse=", ")))
print(paste("User numbers:", paste(user_numbers, collapse=", ")))

# Configure base directory from environment variable or use default
base_dir <- Sys.getenv("DATA_BASE_DIR", "/app")
confidential_data_dir <- file.path(base_dir, "confidential_data")
cbs_data_dir <- file.path(base_dir, "cbs_postcode_data")
output_dir <- file.path(base_dir, "output")

print(paste("Using base directory:", base_dir))

# Load and preprocess training data
print("=== CHUNK 1: Loading and preprocessing training data ===")

new_vars <- fread(file.path(confidential_data_dir, "output.csv"))
names(new_vars) <- gsub("^([0-9])", "X\\1", make.names(names(new_vars)))

df_model_unique <- read_excel(file.path(confidential_data_dir, "data_long_4c.xls"))

df_model_unique <- df_model_unique %>%
  mutate(
    members = 1 + partner + children,
    educat = factor(educat, levels = 1:6, ordered = TRUE),
    urban = urban + 1,
    urban = factor(urban, levels = 1:5, ordered = TRUE),
    occupation = as.factor(occupation),
    year_built = as.factor(year_built),
    rental = as.factor(rental),
    partner = as.factor(partner),
    children = as.integer(children),
    female = as.factor(female)
  )

merged_df <- merge(df_model_unique, new_vars, by = "nomem_encr", all.x = TRUE)
merged_df <- merged_df %>% mutate(nettohh_z = scale(nettohh)[, 1])

class_weights <- c(
  Class1 = 1 / 0.129,
  Class2 = 1 / 0.173,
  Class3 = 1 / 0.131,
  Class4 = 1 / 0.567
)

rf_training <- merged_df %>%
  select(
    nomem_encr, class_4class, female, age, members,
    year_built, rental, urban, nettohh_z, square_meters
  ) %>%
  filter(!is.na(class_4class))

rf_for_impute <- rf_training %>%
  select(-nomem_encr) %>%
  mutate(class_4class = as.factor(class_4class))

set.seed(123)
print("Running missForest imputation...")
rf_imputed_result <- missForest(rf_for_impute)
rf_training_imputed <- rf_imputed_result$ximp

print(paste("Imputed training data dimensions:", nrow(rf_training_imputed), "x", ncol(rf_training_imputed)))

# Train Random Forest model
print("=== CHUNK 2: Training Random Forest model ===")

rf_data <- rf_training_imputed %>%
  mutate(class_4class = factor(class_4class, levels = 1:4, labels = c("Class1", "Class2", "Class3", "Class4")))

set.seed(123)
cv_control <- trainControl(method = "cv", number = 3, classProbs = TRUE, savePredictions = "final")
rf_grid <- expand.grid(mtry = c(3, 5), splitrule = "gini", min.node.size = c(1, 5))

print("Training model with cross-validation...")
cv_model <- train(
  class_4class ~ ., 
  data = rf_data,
  method = "ranger",
  trControl = cv_control,
  importance = "permutation",
  tuneGrid = rf_grid,
  num.trees = 300,
  class.weights = class_weights
)

final_rf_model <- ranger(
  class_4class ~ .,
  data = rf_data,
  importance = "permutation",
  mtry = cv_model$bestTune$mtry,
  splitrule = cv_model$bestTune$splitrule,
  min.node.size = cv_model$bestTune$min.node.size,
  num.trees = 300,
  seed = 123,
  class.weights = class_weights
)

print("Model trained successfully!")
print(final_rf_model)

# Load and process CBS/BAG data
print("=== CHUNK 3: Processing CBS and BAG data ===")

bag_data <- read_csv(file.path(cbs_data_dir, "bag_data.csv"))
bag_data <- bag_data %>%
  mutate(
    year_built_cat = case_when(
      bouwjaar < 1940 ~ "Vóór 1940",
      bouwjaar >= 1940 & bouwjaar <= 1970 ~ "Tussen 1940 en 1970",
      bouwjaar >= 1971 & bouwjaar <= 2000 ~ "Tussen 1971 en 2000",
      bouwjaar >= 2001 ~ "In 2001 of later",
      TRUE ~ "Tussen 1971 en 2000"
    )
  ) %>%
  filter(!is.na(bag_id), bag_id != "")

# Create regional demographics (simplified - use Dutch averages by postcode type)
get_regional_demo <- function(postcode) {
  pc2 <- substr(postcode, 1, 2)
  
  # Basic regional demographics based on first 2 digits of postcode
  if (pc2 %in% c("10", "11", "12")) {
    # Amsterdam area
    list(female = 0.52, age = 36, members = 1.9, rental = 0.65, urban = 5, income_z = 0.3)
  } else if (pc2 %in% c("20", "21", "22", "23", "24", "25", "26", "27")) {
    # The Hague/Rotterdam area
    list(female = 0.51, age = 40, members = 2.2, rental = 0.35, urban = 4, income_z = 0.1)
  } else if (pc2 %in% c("30", "31", "32", "33", "34", "35", "36", "37", "38", "39")) {
    # Utrecht area
    list(female = 0.51, age = 38, members = 2.3, rental = 0.30, urban = 4, income_z = 0.2)
  } else {
    # Rest of Netherlands
    list(female = 0.50, age = 43, members = 2.4, rental = 0.25, urban = 3, income_z = 0.0)
  }
}

# Create user addresses
print("=== CHUNK 4-6: Creating predictions for user addresses ===")

user_addresses <- data.frame(
  bag_id = paste0("USER_", user_postcodes, "_", user_numbers),
  Postcode = user_postcodes,
  Huisnummer = user_numbers,
  stringsAsFactors = FALSE
)

# Add regional demographics
for(i in 1:nrow(user_addresses)) {
  demo <- get_regional_demo(user_addresses$Postcode[i])
  user_addresses$female[i] <- demo$female
  user_addresses$age[i] <- demo$age
  user_addresses$members[i] <- demo$members
  user_addresses$rental[i] <- demo$rental
  user_addresses$urban[i] <- demo$urban
  user_addresses$nettohh_z[i] <- demo$income_z
}

# Add building characteristics (defaults)
user_addresses <- user_addresses %>%
  mutate(
    year_built = "Tussen 1971 en 2000",  # Most common period
    square_meters = 80  # Average house size
  )

# Convert to proper factor types
user_addresses <- user_addresses %>%
  mutate(
    female = as.factor(female),
    year_built = factor(year_built, levels = c("Vóór 1940", "Tussen 1940 en 1970", "Tussen 1971 en 2000", "In 2001 of later")),
    rental = as.factor(rental),
    urban = factor(urban, levels = 1:5, ordered = TRUE)
  )

print("Making predictions...")

# Make predictions
predictions <- predict(final_rf_model, data = user_addresses, type = "response")
user_addresses$predicted_persona <- predictions$predictions

# Display results
print("=== PREDICTION RESULTS ===")

personas <- data.frame(
  Class = c("Class1", "Class2", "Class3", "Class4"),
  Description = c(
    "Financially driven (~12.9%)",
    "Policy driven (~17.3%)", 
    "Erratic choosers (~13.1%)",
    "Comfort driven (~56.7%)"
  )
)

for(i in 1:nrow(user_addresses)) {
  cat("\n--- Address", i, "---\n")
  cat("Postcode:", user_addresses$Postcode[i], ", Number:", user_addresses$Huisnummer[i], "\n")
  cat("Predicted Persona:", as.character(user_addresses$predicted_persona[i]), "\n")
  
  desc <- personas$Description[personas$Class == as.character(user_addresses$predicted_persona[i])]
  cat("Description:", desc, "\n")
  
  cat("Characteristics used:\n")
  cat("  - Female share:", as.character(user_addresses$female[i]), "\n")
  cat("  - Age:", user_addresses$age[i], "\n")
  cat("  - Household size:", user_addresses$members[i], "\n")
  cat("  - Construction period:", as.character(user_addresses$year_built[i]), "\n")
  cat("  - Rental share:", as.character(user_addresses$rental[i]), "\n")
  cat("  - Urban level:", as.character(user_addresses$urban[i]), "\n")
  cat("  - Income z-score:", user_addresses$nettohh_z[i], "\n")
  cat("  - Square meters:", user_addresses$square_meters[i], "\n")
}

# Save results
output_file <- file.path(output_dir, "user_predictions.csv")
write.csv(user_addresses, output_file, row.names = FALSE)
print("\n=== SCRIPT COMPLETED ===")
print(paste("Results saved to:", output_file))

# Create summary
summary_table <- table(user_addresses$predicted_persona)
print("\nPrediction Summary:")
print(summary_table)