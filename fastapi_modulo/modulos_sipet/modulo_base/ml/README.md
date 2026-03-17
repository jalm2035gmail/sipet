# Convención ML

- `ml/models/`: modelos serializados con `joblib`.
- `ml/pipelines/`: pipelines de preprocesamiento y feature engineering.
- `ml/artifacts/`: artefactos auxiliares de inferencia.

El módulo base no obliga `scikit-learn`, `numpy` ni `joblib`, pero define este contrato para módulos de scoring, predicción o recomendación.
