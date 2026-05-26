#!/usr/bin/env python3
"""Smoke-test the LIMINA conda environment."""

from __future__ import annotations

import importlib
import json


def check_import(module_name: str) -> dict[str, str]:
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, "__version__", "installed")
        return {"module": module_name, "status": "ok", "version": str(version)}
    except Exception as exc:
        return {
            "module": module_name,
            "status": "fail",
            "error": f"{type(exc).__name__}: {exc}",
        }


def rdkit_smoke() -> dict[str, object]:
    from rdkit import Chem
    from rdkit.Chem import Descriptors

    molecule = Chem.MolFromSmiles("O")
    return {
        "name": "rdkit_water_descriptor",
        "mol_wt": round(float(Descriptors.MolWt(molecule)), 4),
        "atoms": molecule.GetNumAtoms(),
    }


def openmm_smoke() -> dict[str, object]:
    import openmm

    platforms = [
        openmm.Platform.getPlatform(index).getName()
        for index in range(openmm.Platform.getNumPlatforms())
    ]
    return {"name": "openmm_platforms", "platforms": platforms}


def duckdb_smoke() -> dict[str, object]:
    import duckdb

    value = duckdb.sql("select 2 + 2").fetchone()[0]
    return {"name": "duckdb_query", "value": value}


def main() -> int:
    modules = [
        "rdkit",
        "ase",
        "openmm",
        "pymatgen",
        "xtb",
        "duckdb",
        "pandas",
        "numpy",
        "scipy",
        "matplotlib",
        "optuna",
        "sklearn",
        "Bio",
        "pyzotero",
    ]
    result = {
        "imports": [check_import(module_name) for module_name in modules],
        "smoke_tests": [rdkit_smoke(), openmm_smoke(), duckdb_smoke()],
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    failures = [item for item in result["imports"] if item["status"] != "ok"]
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
