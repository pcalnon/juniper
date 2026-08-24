"""Generic on-disk snapshot store (WS-2 / OUT-11 T2 step 1b).

The de-cascored persistence seam: cascor bundles a model + training state into one HDF5 file
via its cascade-specific ``CascadeHDF5Serializer``. This generic store delegates the *model*
format entirely to an injected :class:`juniper_model_core.serialization.ModelSerializer`
(cascor injects its HDF5 serializer; the conformance kit injects ``ReferenceLinearSerializer``,
an ``.npz`` + JSON one) and keeps only the model-agnostic part itself: one bundle *directory*
per snapshot holding the serialized model plus a JSON sidecar of the lifecycle state
(``LifecycleMonitor`` metric history + metadata).

Pure stdlib + the injected serializer -- no third-party import here, so the module is safe on
the dependency-free import path (it is exposed lazily by :mod:`juniper_service_core`).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from juniper_service_core.exceptions import JuniperServiceCoreError

if TYPE_CHECKING:
    from juniper_model_core.interfaces import TrainableModel
    from juniper_model_core.serialization import ModelSerializer

__all__ = ["SnapshotStore", "SnapshotNotFoundError", "MODEL_STEM", "SIDECAR_NAME"]

#: The model file's stem inside a bundle dir. ``serializer.save(model, <dir>/model)`` -- the
#: serializer owns the actual extension (e.g. ``.npz`` / ``.h5``); ``load`` reverses it.
MODEL_STEM = "model"
#: The lifecycle-state sidecar filename inside a bundle dir.
SIDECAR_NAME = "snapshot.json"


class SnapshotNotFoundError(JuniperServiceCoreError, KeyError):
    """Raised when a snapshot id has no bundle in the store."""


class SnapshotStore:
    """An on-disk store of training snapshots -- one bundle directory per snapshot.

    A bundle is ``<base_dir>/<snapshot_id>/`` containing the serialized model (written by the
    injected :class:`~juniper_model_core.serialization.ModelSerializer`) and a JSON sidecar
    (:data:`SIDECAR_NAME`) of model-agnostic lifecycle state. The model *format* is the
    serializer's concern; the store is format-agnostic.
    """

    def __init__(self, serializer: ModelSerializer, base_dir: str | os.PathLike[str]) -> None:
        self._serializer = serializer
        self._base = Path(base_dir)

    def _bundle(self, snapshot_id: str) -> Path:
        return self._base / snapshot_id

    def exists(self, snapshot_id: str) -> bool:
        """True if a bundle with a sidecar exists for ``snapshot_id``."""
        return (self._bundle(snapshot_id) / SIDECAR_NAME).is_file()

    def save(self, model: TrainableModel, snapshot_id: str, sidecar: dict[str, Any]) -> dict[str, Any]:
        """Persist ``model`` + ``sidecar`` under ``snapshot_id``.

        Returns the stored metadata (the sidecar with ``id`` and resolved ``path`` set).
        """
        bundle = self._bundle(snapshot_id)
        bundle.mkdir(parents=True, exist_ok=True)
        self._serializer.save(model, os.fspath(bundle / MODEL_STEM))
        record = dict(sidecar)
        record["id"] = snapshot_id
        with open(bundle / SIDECAR_NAME, "w", encoding="utf-8") as handle:
            json.dump(record, handle)
        record["path"] = os.fspath(bundle)
        return record

    def load(self, snapshot_id: str) -> tuple[TrainableModel, dict[str, Any]]:
        """Reconstruct ``(model, sidecar)`` for ``snapshot_id``.

        Raises :class:`SnapshotNotFoundError` if no bundle exists.
        """
        bundle = self._bundle(snapshot_id)
        sidecar_path = bundle / SIDECAR_NAME
        if not sidecar_path.is_file():
            raise SnapshotNotFoundError(snapshot_id)
        with open(sidecar_path, encoding="utf-8") as handle:
            sidecar = json.load(handle)
        model = self._serializer.load(os.fspath(bundle / MODEL_STEM))
        return model, sidecar

    def get(self, snapshot_id: str) -> dict[str, Any] | None:
        """Return the sidecar metadata for ``snapshot_id`` (with ``path``), or ``None`` if absent."""
        sidecar_path = self._bundle(snapshot_id) / SIDECAR_NAME
        if not sidecar_path.is_file():
            return None
        with open(sidecar_path, encoding="utf-8") as handle:
            sidecar = json.load(handle)
        sidecar["path"] = os.fspath(self._bundle(snapshot_id))
        return sidecar

    def list(self) -> list[dict[str, Any]]:
        """Return every snapshot's sidecar metadata, sorted by id (cheap -- reads sidecars only)."""
        if not self._base.is_dir():
            return []
        out: list[dict[str, Any]] = []
        for child in sorted(self._base.iterdir()):
            if (child / SIDECAR_NAME).is_file():
                meta = self.get(child.name)
                if meta is not None:
                    out.append(meta)
        return out
