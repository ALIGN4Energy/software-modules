# Energy Usage Prediction and Recommendation

---

*This publication is part of the project ALIGN4energy (with project number NWA.1389.20.251) of the research programme NWA ORC 2020 which is (partly) financed by the Dutch Research Council (NWO).*

---

Three independent Docker-packaged models for Dutch household energy analysis.

## Models

### 1. [persona-segmentation](persona-segmentation/)
Consumer persona prediction using Random Forest ML. Classifies Dutch addresses into four behavioral types based on demographics and housing data.

### 2. [profile-generator](profile-generator/)
PyTorch-based neural network for generating synthetic daily energy consumption profiles. Generates annual profiles (12 months × 96 intervals per day) based on household characteristics and technology adoption.

### 3. [technology-adoption-agent-based-model](technology-adoption-agent-based-model/)
Agent-Based Model simulating household adoption of energy technologies (heat pumps, district heating, PV) with latent class modeling.

## Documentation

- [TUTORIAL.md](TUTORIAL.md) - Complete tutorial for using all three models
- See individual model directories for detailed README files and usage instructions
