#!/usr/bin/env python3
"""Probe for APD-DATA-021: would wiring ``DatasetListFilter`` into ``/filter`` change OpenAPI?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-08-25
Status: ad-hoc -- investigation (evidence for the APD-DATA-021 remedy decision)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md (APD-DATA-021), the juniper-data fix PR named in its §5.1 row

``juniper_data.core.models.DatasetListFilter`` is declared and never used, while
``GET /v1/datasets/filter`` re-declares its fields as individual ``Query`` params. The
register asks whether wiring the model in (``Depends(DatasetListFilter)``) would change the
published contract before choosing between "wire it" and "delete it". This script builds
the real app, reads the real route's OpenAPI parameters, builds a throwaway app whose route
takes the model via ``Depends()``, and diffs the two parameter sets by name, schema and
description. Run with the JuniperData interpreter from any cwd::

    /opt/miniforge3/envs/JuniperData/bin/python util/ad-hoc/apd_data_021_openapi_probe.py
"""

from __future__ import annotations

import json

from fastapi import Depends, FastAPI
from juniper_data.api.app import create_app
from juniper_data.api.settings import Settings
from juniper_data.core.models import DatasetListFilter


def _index(params: list[dict]) -> dict[str, dict]:
    return {p["name"]: p for p in params}


def main() -> None:
    real = create_app(settings=Settings(storage_path="/tmp/claude-1000/apd-021-probe")).openapi()
    real_params = _index(real["paths"]["/v1/datasets/filter"]["get"]["parameters"])

    probe = FastAPI()

    @probe.get("/filter")
    def filter_probe(flt: DatasetListFilter = Depends()) -> dict:  # noqa: B008
        return {}

    probe_params = _index(probe.openapi()["paths"]["/filter"]["get"]["parameters"])

    print("real route params    :", sorted(real_params))
    print("Depends(model) params:", sorted(probe_params))
    for name in sorted(set(real_params) & set(probe_params)):
        r, q = real_params[name], probe_params[name]
        if r.get("schema") != q.get("schema") or r.get("description") != q.get("description"):
            print(f"DIFF {name}:")
            print(f"   real    schema={json.dumps(r.get('schema'))} desc={r.get('description')!r}")
            print(f"   depends schema={json.dumps(q.get('schema'))} desc={q.get('description')!r}")
    print("only in real    :", sorted(set(real_params) - set(probe_params)))
    print("only in depends :", sorted(set(probe_params) - set(real_params)))


if __name__ == "__main__":
    main()
