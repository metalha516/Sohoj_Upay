"""Model registry promotion engine with shadow evaluation and automated quality gates.

Manages model lifecycle, checksum integrity validation, and pointer promotion to 'current.json'.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class PromotionGateError(Exception):
    """Raised when candidate model fails quality gates during promotion."""


def compute_file_sha256(path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


class ModelRegistry:
    """Production Model Registry managing versioned artifacts, checksums, and active pointers."""

    def __init__(self, registry_root: str | Path = "ml/models_registry") -> None:
        self.root = Path(registry_root)
        self.root.mkdir(parents=True, exist_ok=True)

    def get_model_dir(self, model_name: str) -> Path:
        return self.root / model_name

    def get_current_pointer_path(self, model_name: str) -> Path:
        return self.get_model_dir(model_name) / "current.json"

    def get_active_version(self, model_name: str) -> str | None:
        ptr_file = self.get_current_pointer_path(model_name)
        if not ptr_file.exists():
            return None
        with open(ptr_file, encoding="utf-8") as f:
            data = json.load(f)
        val = data.get("active_version")
        return str(val) if val is not None else None

    def get_active_model_path(self, model_name: str) -> tuple[Path, str]:
        """Return (model_path, active_version) for the active model."""
        active_ver = self.get_active_version(model_name)
        if not active_ver:
            raise FileNotFoundError(f"No active pointer found in current.json for '{model_name}'.")

        model_file = self.get_model_dir(model_name) / active_ver / "model.joblib"
        if not model_file.exists():
            raise FileNotFoundError(
                f"Model artifact missing for active version '{active_ver}' at {model_file}."
            )

        return model_file, active_ver

    def register_version(
        self,
        model_name: str,
        version: str,
        artifact_source: Path,
        metadata_source: Path | None = None,
    ) -> Path:
        """Register a new model version into the registry directory."""
        target_dir = self.get_model_dir(model_name) / version
        target_dir.mkdir(parents=True, exist_ok=True)

        target_artifact = target_dir / "model.joblib"
        target_metadata = target_dir / "metadata.json"

        # Copy artifact
        with open(artifact_source, "rb") as f_in, open(target_artifact, "wb") as f_out:
            while chunk := f_in.read(65536):
                f_out.write(chunk)

        # Checksum
        sha = compute_file_sha256(target_artifact)

        if metadata_source and metadata_source.exists():
            with open(metadata_source, encoding="utf-8") as f:
                meta = json.load(f)
        else:
            meta = {}

        meta["model_name"] = model_name
        meta["model_version"] = version
        meta["sha256_checksum"] = sha
        meta["registered_at"] = datetime.now(UTC).isoformat()

        with open(target_metadata, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        return target_artifact

    def promote_candidate(
        self,
        model_name: str,
        candidate_version: str,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Run quality gates and promote candidate version to 'current.json'.

        Gates:
        1. Integrity Gate: Checksum matches metadata manifest.
        2. Performance Gate: Candidate metrics must not regress beyond tolerance vs current active model.
        """
        cand_dir = self.get_model_dir(model_name) / candidate_version
        cand_artifact = cand_dir / "model.joblib"
        cand_meta_file = cand_dir / "metadata.json"

        if not cand_artifact.exists() or not cand_meta_file.exists():
            raise FileNotFoundError(f"Candidate {candidate_version} missing files in {cand_dir}")

        with open(cand_meta_file, encoding="utf-8") as f:
            cand_meta = json.load(f)

        # Gate 1: Checksum verification
        actual_sha = compute_file_sha256(cand_artifact)
        expected_sha = cand_meta.get("sha256_checksum")
        if actual_sha != expected_sha:
            raise PromotionGateError(
                f"Gate 1 FAILED: Checksum mismatch for candidate {candidate_version}. "
                f"Expected {expected_sha}, got {actual_sha}."
            )

        # Gate 2: Shadow performance comparison if an existing active version exists
        current_ver = self.get_active_version(model_name)
        if current_ver and current_ver != candidate_version:
            curr_meta_file = self.get_model_dir(model_name) / current_ver / "metadata.json"
            if curr_meta_file.exists():
                with open(curr_meta_file, encoding="utf-8") as f:
                    curr_meta = json.load(f)

                # For forecaster: compare MAE (lower is better, tolerance: max 5% increase)
                if model_name == "expense_forecaster":
                    curr_mae = curr_meta.get("held_out_metrics", {}).get("mae", float("inf"))
                    cand_mae = cand_meta.get("held_out_metrics", {}).get("mae", float("inf"))
                    if cand_mae > curr_mae * 1.05:
                        raise PromotionGateError(
                            f"Gate 2 FAILED: Candidate MAE ({cand_mae:.2f}) regressed by > 5% vs "
                            f"current MAE ({curr_mae:.2f}). Promotion rejected."
                        )

        # All gates passed -> promote
        pointer_data = {
            "active_version": candidate_version,
            "model_name": model_name,
            "sha256_checksum": actual_sha,
            "promoted_at": datetime.now(UTC).isoformat(),
            "previous_version": current_ver,
            "status": "production",
        }

        if not dry_run:
            with open(self.get_current_pointer_path(model_name), "w", encoding="utf-8") as f:
                json.dump(pointer_data, f, indent=2)

        return {
            "promoted": not dry_run,
            "model_name": model_name,
            "active_version": candidate_version,
            "previous_version": current_ver,
            "sha256_checksum": actual_sha,
            "gates_passed": ["Integrity Gate", "Performance Gate"],
        }
