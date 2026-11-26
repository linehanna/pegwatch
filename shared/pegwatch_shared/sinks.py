"""Where bronze records are written. Same records, same paths, different storage.

- LocalSink:  a folder on disk. Also used on Databricks, where a Unity Catalog
              volume is just a path like /Volumes/workspace/pegwatch_bronze/raw
- GcsSink:    a Google Cloud Storage bucket, e.g. gs://pegwatch-bronze-9aa513
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from .http import RawRecord


class Sink(Protocol):
    def write(self, record: RawRecord) -> str: ...


def _serialize(record: RawRecord) -> str:
    return json.dumps(record.to_dict(), ensure_ascii=False)


class LocalSink:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def write(self, record: RawRecord) -> str:
        path = self.root / record.bronze_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_serialize(record), encoding="utf-8")
        return str(path)

    def __repr__(self) -> str:
        return f"LocalSink({self.root})"


class GcsSink:
    def __init__(self, bucket: str, prefix: str = "") -> None:
        from google.cloud import storage  # optional dependency: pip install "pegwatch-shared[gcp]"

        self.bucket_name = bucket
        self.prefix = prefix.strip("/")
        self.bucket = storage.Client().bucket(bucket)

    def write(self, record: RawRecord) -> str:
        name = f"{self.prefix}/{record.bronze_path()}" if self.prefix else record.bronze_path()
        self.bucket.blob(name).upload_from_string(_serialize(record), content_type="application/json")
        return f"gs://{self.bucket_name}/{name}"

    def __repr__(self) -> str:
        return f"GcsSink(gs://{self.bucket_name}/{self.prefix})"


def sink_from_uri(uri: str) -> Sink:
    """gs://bucket[/prefix] -> GcsSink, anything else -> LocalSink."""
    if uri.startswith("gs://"):
        bucket, _, prefix = uri[5:].partition("/")
        return GcsSink(bucket, prefix)
    return LocalSink(uri)
