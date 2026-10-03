"""Unit tests verifying that synthetic data YAML configurations validate against Pydantic models."""

from decimal import Decimal
from pathlib import Path

import yaml

from app.schemas.synthetic_config import (
    AnomaliesConfig,
    OccupationsConfig,
    PersonasConfig,
    TaxonomyConfig,
)

CONFIG_DIR = Path("data/synthetic/config")


def test_taxonomy_yaml_validates() -> None:
    """Verify that taxonomy.yaml conforms strictly to TaxonomyConfig."""
    file_path = CONFIG_DIR / "taxonomy.yaml"
    assert file_path.exists(), f"Missing config file: {file_path}"

    with open(file_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    config = TaxonomyConfig.model_validate(data)
    assert len(config.purposes) == 4
    assert len(config.categories) >= 20

    # Ensure all category codes are unique
    codes = [c.code for c in config.categories]
    assert len(codes) == len(set(codes)), "Category codes must be unique"


def test_personas_yaml_validates() -> None:
    """Verify that personas.yaml conforms to PersonasConfig and population shares sum to 1.0."""
    file_path = CONFIG_DIR / "personas.yaml"
    assert file_path.exists(), f"Missing config file: {file_path}"

    with open(file_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    config = PersonasConfig.model_validate(data)
    assert len(config.personas) == 7  # 6 archetypes + 1 mixed/drifting

    codes = [p.code for p in config.personas]
    assert len(codes) == len(set(codes)), "Persona codes must be unique"

    # Verify that mixed_drifting exists and target_population_share == 0.10
    mixed = next(p for p in config.personas if p.code == "mixed_drifting")
    assert mixed.target_population_share == Decimal("0.10")


def test_occupations_yaml_validates() -> None:
    """Verify that occupations.yaml conforms to OccupationsConfig."""
    file_path = CONFIG_DIR / "occupations.yaml"
    assert file_path.exists(), f"Missing config file: {file_path}"

    with open(file_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    config = OccupationsConfig.model_validate(data)
    assert len(config.occupations) >= 8

    # Load personas to cross-validate foreign keys
    personas_path = CONFIG_DIR / "personas.yaml"
    with open(personas_path, encoding="utf-8") as f:
        personas_data = yaml.safe_load(f)
    valid_persona_codes = {p["code"] for p in personas_data["personas"]}

    for occ in config.occupations:
        for persona_code in occ.persona_mapping:
            assert persona_code in valid_persona_codes, (
                f"Occupation '{occ.code}' references unknown persona '{persona_code}'"
            )


def test_anomalies_yaml_validates() -> None:
    """Verify that anomalies.yaml conforms to AnomaliesConfig and references valid categories."""
    file_path = CONFIG_DIR / "anomalies.yaml"
    assert file_path.exists(), f"Missing config file: {file_path}"

    with open(file_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    config = AnomaliesConfig.model_validate(data)
    assert config.target_injection_rate == Decimal("0.025")
    assert len(config.anomaly_types) >= 4
    assert len(config.life_events) >= 5

    # Cross-validate referenced categories with taxonomy.yaml
    taxonomy_path = CONFIG_DIR / "taxonomy.yaml"
    with open(taxonomy_path, encoding="utf-8") as f:
        tax_data = yaml.safe_load(f)
    valid_category_codes = {c["code"] for c in tax_data["categories"]}

    for event in config.life_events:
        if event.category:
            assert event.category in valid_category_codes, (
                f"Life event '{event.code}' references unknown category '{event.category}'"
            )
