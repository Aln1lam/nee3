"""`backend` package marker.

Implementation is under `backend.server` (e.g. `backend.server.db_models`).
This package intentionally does not perform any compatibility shimming;
imports should use `backend.server.*` directly.
"""

__all__ = []
