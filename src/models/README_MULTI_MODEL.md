# Multi-Model Training Framework

This framework provides a standardized, extensible way to train and compare multiple ML models for the accident prediction project.

## Overview

The multi-model training framework consists of:

1. **Base Trainer** (`base_trainer.py`): Abstract base class with common functionality
2. **Model Trainers** (`model_trainers.py`): Specific implementations for each model type
3. **Multi-Model Orchestrator** (`train_multi_model.py`): Trains multiple models and compares them
4. **MLflow Integration** (`mlflow_utils.py`): Reusable MLflow logging utilities

## Supported Models

- **XGBoost** (`xgboost`)
- **Random Forest** (`random_forest`)
- **Logistic Regression** (`logistic_regression`)
- **LightGBM** (`lightgbm`)

## Quick Start

### Train All Models

```bash
python src/models/train_multi_model.py
```

This will train all models specified in `model_config.yaml` under `multi_model.enabled_models`.

### Train Specific Models

```bash
python src/models/train_multi_model.py --models xgboost random_forest
```

### Use Grid Search

```bash
python src/models/train_multi_model.py --grid-search
```

## Configuration

Configure models in `src/config/model_config.yaml`:

```yaml
multi_model:
  enabled_models:  # List of models to train (multi-model is the default training method)
    - "xgboost"
    - "random_forest"
    - "logistic_regression"
    - "lightgbm"

# Model-specific parameters
xgboost:
  default_params:
    learning_rate: 0.05
    max_depth: 5
    n_estimators: 300
    # ... more params

random_forest:
  default_params:
    n_estimators: 100
    max_depth: 10
    # ... more params

# Grid search parameters for each model
grid_search:
  param_grid:  # XGBoost
    xgb__n_estimators: [300, 500, 750]
    # ...
  param_grid_rf:  # Random Forest
    rf__n_estimators: [100, 200, 300]
    # ...
  param_grid_lr:  # Logistic Regression
    lr__C: [0.1, 1.0, 10.0]
    # ...
  param_grid_lgbm:  # LightGBM
    lgbm__n_estimators: [300, 500, 750]
    # ...
```

## MLflow Integration

All models are logged to MLflow with:

- **Tags**: `model_type` (e.g., "xgboost", "random_forest") for easy filtering
- **Registered Model Names**: Each model type gets its own registered model name (format: `Accident_Prediction_{ModelType}`)
  - XGBoost: `Accident_Prediction_XGBoost`
  - Random Forest: `Accident_Prediction_Random_Forest`
  - Logistic Regression: `Accident_Prediction_Logistic_Regression`
  - LightGBM: `Accident_Prediction_Lightgbm`

### Viewing Models in MLflow

Filter by model type using the tag:
```
tags.model_type = 'xgboost'
```

Or view all models in the experiment to compare performance.

## Adding New Models

To add a new model type:

1. **Create a trainer class** in `model_trainers.py`:

```python
class MyModelTrainer(BaseTrainer):
    model_type = "my_model"
    
    def _build_model(self, X_train, y_train, use_grid_search=False):
        # Implement model building logic
        pass
    
    def _get_model_params(self, model):
        # Extract parameters for logging
        pass
```

2. **Register the trainer** in `train_multi_model.py`:

```python
MODEL_TRAINERS = {
    # ... existing models
    "my_model": MyModelTrainer,
}
```

3. **Add configuration** to `model_config.yaml`:

```yaml
my_model:
  default_params:
    param1: value1
    param2: value2
    random_state: 42

grid_search:
  param_grid_my_model:
    my_model__param1: [value1, value2, value3]
    # ...
```

4. **Add to enabled models** (optional):

```yaml
multi_model:
  enabled_models:
    - "xgboost"
    - "my_model"
```

## Output Files

After training, you'll find:

- **Models**: `models/{model_type}_model.joblib` (one for each trained model)
- **Metadata**: `models/{model_type}_model_metadata.joblib` (one for each trained model)
- **Metrics**: `data/metrics/{model_type}_metrics.json` (one for each trained model)
- **Comparison**: `data/metrics/model_comparison.csv` (ranks all models by F1 score)

### DVC Tracking

All model files are tracked by DVC in `dvc.yaml`. By default, all 4 models (XGBoost, Random Forest, Logistic Regression, LightGBM) are trained and tracked. 

**Note**: If you modify `enabled_models` in the config to train fewer models, you may need to update `dvc.yaml` to remove the corresponding output entries, as DVC requires all listed outputs to exist after the command runs.

## Model Comparison

The framework automatically generates a comparison report:

```
model_type        accuracy  precision  recall  f1_score
xgboost           0.8500    0.8200    0.7800  0.8000
random_forest     0.8400    0.8100    0.7700  0.7900
logistic_regression 0.8300  0.8000    0.7600  0.7800
```

Models are sorted by F1 score (descending).

## Best Practices

1. **Use the same train/test split**: The framework ensures all models use the same split for fair comparison
2. **Use MLflow tags**: Filter and compare models using the `model_type` tag
3. **Version control configs**: Keep model configurations in `model_config.yaml`
4. **Extend BaseTrainer**: All new models should inherit from `BaseTrainer` for consistency

## Integration with Existing Code

The framework uses `train_multi_model.py` for all model training. It supports training multiple models and comparing their performance, using the same configuration file and MLflow setup.

