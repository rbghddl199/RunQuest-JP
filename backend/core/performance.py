import logging
import time
from contextlib import contextmanager

from django.conf import settings
from django.db import connection


logger = logging.getLogger('runquest.performance')


def performance_enabled():
    return getattr(settings, 'RUNQUEST_PERFORMANCE_LOGS', False)


@contextmanager
def time_block(name, **metadata):
    started_at = time.perf_counter()
    query_start = len(connection.queries)
    try:
        yield
    finally:
        if not performance_enabled():
            return
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        query_count = len(connection.queries) - query_start
        logger.info(
            '%s elapsed_ms=%.2f queries=%s metadata=%s',
            name,
            elapsed_ms,
            query_count,
            metadata,
        )
