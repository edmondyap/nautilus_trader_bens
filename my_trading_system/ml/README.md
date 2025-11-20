# Machine Learning

This directory contains all machine learning components for trading strategies.

## Structure

```
ml/
├── features/       # Feature engineering
├── models/         # Model definitions
├── training/       # Training utilities
├── inference/      # Model serving
└── utils/          # ML utilities
```

## Workflow

```
1. Research (notebooks/ml_research/)
   └─> Experiment with features, models, parameters

2. Feature Engineering (ml/features/)
   └─> Extract reusable feature code

3. Model Definition (ml/models/)
   └─> Create model classes

4. Training (notebooks/ml_training/)
   └─> Production training pipelines

5. Save Models (models/)
   └─> Versioned model artifacts

6. Use in Strategies (strategies/ml/)
   └─> Deploy in trading strategies
```

## Components

### Features (`features/`)

Feature engineering modules that transform raw data into ML features.

**Example modules:**
- `technical.py` - Technical indicators as features
- `microstructure.py` - Order book, volume features
- `alternative_data.py` - News sentiment, social features
- `temporal.py` - Time-based features
- `pipeline.py` - Complete feature pipeline

**Pattern:**
```python
# ml/features/technical.py
class TechnicalFeatures:
    @staticmethod
    def create_features(df: pd.DataFrame) -> pd.DataFrame:
        # Add technical features
        df['sma_20'] = df['close'].rolling(20).mean()
        df['rsi'] = calculate_rsi(df['close'])
        return df
```

### Models (`models/`)

ML model definitions with consistent interface.

**Example models:**
- `direction_predictor.py` - Predict price direction (up/down)
- `volatility_forecaster.py` - Forecast volatility
- `regime_classifier.py` - Classify market regime
- `base_model.py` - Base class for all models

**Pattern:**
```python
# ml/models/direction_predictor.py
class DirectionPredictor:
    def __init__(self, model_params=None):
        self.model = RandomForestClassifier(**model_params)
        self.scaler = StandardScaler()

    def fit(self, X, y):
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)

    def predict(self, X):
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def save(self, path):
        # Save model, scaler, metadata

    @classmethod
    def load(cls, path):
        # Load saved model
```

### Training (`training/`)

Utilities for model training.

**Example modules:**
- `trainer.py` - Training loop
- `evaluator.py` - Model evaluation
- `cross_validation.py` - Walk-forward CV for time series

**Pattern:**
```python
# ml/training/evaluator.py
class ModelEvaluator:
    def evaluate(self, model, X_test, y_test):
        y_pred = model.predict(X_test)
        return {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred)
        }
```

### Inference (`inference/`)

Model serving for real-time predictions.

**Example modules:**
- `predictor.py` - Real-time inference wrapper
- `batch_predictor.py` - Batch predictions

**Pattern:**
```python
# ml/inference/predictor.py
class RealtimePredictor:
    def __init__(self, model_path):
        self.model = Model.load(model_path)
        self.feature_pipeline = FeaturePipeline()

    def predict(self, latest_data):
        features = self.feature_pipeline.create_features(latest_data)
        return self.model.predict(features)
```

### Utils (`utils/`)

General ML utilities.

**Example modules:**
- `data_preparation.py` - Train/test splits, data prep
- `metrics.py` - Custom metrics for trading

## Model Versioning

Save models with versioned directories:

```
models/
├── direction_predictor/
│   ├── v1_20241101/
│   │   ├── model.pkl          # Scikit-learn model
│   │   ├── scaler.pkl         # Feature scaler
│   │   ├── metadata.json      # Model info
│   │   └── metrics.json       # Training metrics
│   ├── v2_20241115/           # Retrained version
│   │   └── ...
│   └── production -> v2_20241115/  # Symlink to production
└── volatility_forecaster/
    └── v1_20241101/
```

## Best Practices

### 1. Time Series Awareness
```python
# Always split chronologically for time series
split_idx = int(len(data) * 0.8)
train = data[:split_idx]  # Earlier data
test = data[split_idx:]   # Later data

# Never shuffle time series data!
```

### 2. Walk-Forward Validation
```python
# Use walk-forward CV, not k-fold
for train_start, train_end, test_start, test_end in walk_forward_splits:
    train_data = data[train_start:train_end]
    test_data = data[test_start:test_end]
    # Train and evaluate
```

### 3. Feature Leakage Prevention
```python
# Bad: Using future information
df['target'] = df['close'].shift(-1)  # Looking ahead!

# Good: Only use past information
df['target'] = (df['close'].shift(-1) > df['close']).shift(1)
```

### 4. Model Metadata
```python
# Save everything needed to reproduce
metadata = {
    'trained_at': datetime.now().isoformat(),
    'training_data': 'BTCUSDT_2024-01-01_to_2024-10-31',
    'features': feature_names,
    'model_params': model_params,
    'metrics': training_metrics
}
```

### 5. Separate Research from Production
```python
# Research (notebooks): Try many things quickly
# Production (ml/): Only stable, tested code
```

## Example: Complete ML Pipeline

### 1. Feature Engineering
```python
# ml/features/technical.py
from ml.features.technical import TechnicalFeatures

df = load_data()
df = TechnicalFeatures.create_features(df)
```

### 2. Model Training
```python
# notebooks/ml_training/train_direction_model.ipynb
from ml.models.direction_predictor import DirectionPredictor

model = DirectionPredictor(model_params={'n_estimators': 100})
model.fit(X_train, y_train)

# Evaluate
metrics = evaluate(model, X_test, y_test)

# Save
model.save('models/direction_predictor/v1_20241119')
```

### 3. Use in Strategy
```python
# strategies/ml/direction_strategy.py
from ml.models.direction_predictor import DirectionPredictor

class DirectionStrategy(Strategy):
    def __init__(self, config):
        super().__init__(config)
        self.model = DirectionPredictor.load(config.model_path)

    def on_bar(self, bar):
        prediction = self.model.predict(features)
        if prediction == 1:  # Bullish
            # Go long
```

## Model Types

### Classification
Predict discrete outcomes:
- Direction (up/down)
- Regime (trending/ranging/volatile)
- Signal (buy/sell/hold)

### Regression
Predict continuous values:
- Price levels
- Volatility
- Returns

### Reinforcement Learning
Learn optimal actions:
- Order execution
- Position sizing
- Entry/exit timing

## Experiment Tracking

Use MLflow or Weights & Biases:

```python
import mlflow

with mlflow.start_run():
    mlflow.log_params(model_params)
    mlflow.log_metrics(metrics)
    mlflow.sklearn.log_model(model, "model")
```

Results stored in `experiments/` directory.

## Adding New ML Components

### New Feature Type
```python
# Create ml/features/new_feature_type.py
class NewFeatureType:
    @staticmethod
    def create_features(df):
        # Feature engineering logic
        return df
```

### New Model Type
```python
# Create ml/models/new_model_type.py
class NewModelType:
    def __init__(self, params):
        # Initialize model

    def fit(self, X, y):
        # Training logic

    def predict(self, X):
        # Inference logic

    def save(self, path):
        # Serialization

    @classmethod
    def load(cls, path):
        # Deserialization
```

## Resources

- [Scikit-learn Documentation](https://scikit-learn.org/)
- [PyTorch Documentation](https://pytorch.org/)
- [MLflow Documentation](https://mlflow.org/)
- Main README: [../README.md](../README.md)
