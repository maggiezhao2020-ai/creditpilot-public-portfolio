"""Read-only complete-bundle loader. No runtime, database or network imports."""
from __future__ import annotations

import copy
from pathlib import Path
from types import MappingProxyType

from .contracts import (ArtifactError, SCENARIOS, HASH, file_digest, parse, require,
                        validate_artifact, validate_manifest, validate_shape)


def _read(root, name):
    path = root / name
    require(not path.is_symlink() and path.is_file() and path.stat().st_size <= 1_000_000)
    return path.read_bytes()


def load_bundle(directory: Path, *, expected_manifest_sha256: str):
    """The required pin comes from reviewed release configuration, never the bundle.

    Return fresh objects only after every file validates. No partial results,
    API fallback, downloads, automatic regeneration or cache mutation.
    """
    try:
        validate_shape(expected_manifest_sha256, HASH)
        root = Path(directory)
        require(not root.is_symlink() and root.is_dir())
        require({p.name for p in root.iterdir()} == {'manifest.json', *(x.lower()+'.json' for x in SCENARIOS)})
        manifest = validate_manifest(parse(_read(root, 'manifest.json')))
        require(manifest['integrity']['payload_sha256'] == expected_manifest_sha256)
        results = {}
        for item in manifest['artifacts']:
            raw = _read(root, item['filename'])
            require(file_digest(raw) == item['file_sha256'])
            value = validate_artifact(parse(raw))
            require(value['scenario']['id'] == item['scenario_id'])
            require(value['schema_version'] == item['schema_version'])
            require(value['integrity']['payload_sha256'] == item['payload_sha256'])
            require(value['artifact_version'] == manifest['artifact_version'])
            require(value['provenance']['generated_at_utc'] == manifest['generated_at_utc'])
            require(value['provenance']['exporter_version'] == manifest['exporter_version'])
            results[item['scenario_id']] = value
        require(len({v['provenance']['source_execution_id'] for v in results.values()}) == 3)
        for key in ('source_release_commit','execution_code_commit','exporter_code_commit',
                    'model_artifact_sha256','policy_corpus_sha256','decision_policy_sha256','execution_environment_sha256'):
            require(len({v['provenance'][key] for v in results.values()}) == 1)
        return MappingProxyType(copy.deepcopy(results))
    except Exception:
        raise ArtifactError() from None
