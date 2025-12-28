from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IrisRuleModel:
    feature_names: list[str]
    class_names: list[str]
    version: str
    thresholds: dict[str, float]

    def predict(self, features: list[float]) -> tuple[str, float]:
        if len(features) != len(self.feature_names):
            raise ValueError(
                f"Expected {len(self.feature_names)} features, got {len(features)}."
            )
        values = dict(zip(self.feature_names, features, strict=False))
        petal_length = values["petal_length"]
        petal_width = values["petal_width"]

        if petal_length < self.thresholds["petal_length_setosa"]:
            label = "setosa"
        elif petal_width < self.thresholds["petal_width_split"]:
            if petal_length < self.thresholds["petal_length_mid"]:
                label = "versicolor"
            else:
                label = "virginica"
        else:
            if petal_length < self.thresholds["petal_length_high"]:
                label = "versicolor"
            else:
                label = "virginica"
        return label, 1.0


def load_model(model_path: Path) -> IrisRuleModel:
    data = json.loads(model_path.read_text(encoding="utf-8"))
    class_names = data.get("class_names")
    feature_names = data.get("feature_names")
    thresholds = data.get("thresholds")
    if not class_names or not feature_names or not thresholds:
        raise ValueError("Model file is missing required fields.")
    version = str(data.get("version", "unknown"))
    return IrisRuleModel(
        feature_names=[str(item) for item in feature_names],
        class_names=[str(item) for item in class_names],
        version=version,
        thresholds={key: float(value) for key, value in thresholds.items()},
    )
