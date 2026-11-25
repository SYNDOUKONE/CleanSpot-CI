from __future__ import annotations

import os
import tempfile

_TMP = tempfile.mkdtemp(prefix="cleanspot-test-")
os.environ["CLEANSPOT_DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["CLEANSPOT_MEDIA_DIR"] = _TMP

from app.models import init_db  # noqa: E402

init_db()
