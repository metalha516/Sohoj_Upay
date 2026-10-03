# Machine Learning & Analytics Pipeline

Offline and online ML pipelines for user behavior profiling, anomaly detection, and expense forecasting.

## Principles
- All outputs are probabilistic estimates with explicit confidence intervals and model version tags.
- Ground truth from synthetic generators is strictly separated from features.
- Model artifacts are stored in `models/` (git-ignored, tracked via metadata/registry).

## Structure
- `data/raw/`: Raw exported datasets (git-ignored).
- `data/processed/`: Feature stores and cleaned tabular matrices.
- `notebooks/`: Exploratory analysis and model evaluation notebooks (cleared via nbstripout before commit).
- `preprocessing/`: Feature cleaners, scalers, and encoders.
- `features/`: Feature engineering pipelines.
- `training/`: Training scripts for LightGBM, scikit-learn classifiers, and anomaly detectors.
- `evaluation/`: Validation, SHAP explainability, and metrics generation.
- `models/`: Exported model binaries and metadata.
