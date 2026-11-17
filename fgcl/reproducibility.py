"""Portable CPU experiment metadata; no network, checkpoint or training access."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import platform
from pathlib import Path
import sys
import time
import numpy as np
from . import __version__


def array_sha256(array):
    """Hash dtype, shape and C-order contents, rejecting object arrays."""
    array = np.asarray(array)
    if array.dtype.hasobject:
        raise ValueError('object arrays cannot be reproducibly hashed')
    digest = hashlib.sha256()
    digest.update(json.dumps({'dtype': array.dtype.str, 'shape': array.shape},
                             sort_keys=True).encode('utf-8'))
    digest.update(np.ascontiguousarray(array).tobytes())
    return digest.hexdigest()


@contextmanager
def experiment_record(path, *, seed, config, inputs, sources=()):
    """Yield a mutable metrics dict; write JSON on success or failure.

    Inputs is a mapping of names to arrays. Seed is recorded, not globally set;
    use np.random.default_rng(seed). Config/metrics must be JSON serializable.
    Failure is recorded and the original exception is propagated. Output is
    atomically replaced via a sibling .tmp file; use unique paths per run.
    """
    config = json.loads(json.dumps(config, allow_nan=False))
    record = {'schema_version': 1, 'started_utc': datetime.now(timezone.utc).isoformat(),
              'seed': int(seed), 'config': config, 'sources': list(sources),
              'input_sha256': {str(k): array_sha256(v) for k, v in inputs.items()},
              'versions': {'fgcl': __version__, 'numpy': np.__version__,
                           'python': sys.version},
              'hardware': {'platform': platform.platform(), 'machine': platform.machine(),
                           'processor': platform.processor(), 'backend': 'numpy-cpu'},
              'metrics': {}, 'status': 'running'}
    start = time.perf_counter()
    try:
        yield record['metrics']
        record['status'] = 'completed'
    except BaseException as error:
        record['status'] = 'failed'
        record['error_type'] = type(error).__name__
        raise
    finally:
        record['elapsed_seconds'] = time.perf_counter() - start
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + '.tmp')
        temporary.write_text(json.dumps(record, indent=2, allow_nan=False), encoding='utf-8')
        temporary.replace(path)
