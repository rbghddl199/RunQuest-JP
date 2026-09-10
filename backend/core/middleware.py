import time

from django.conf import settings
from django.db import connection

from .performance import logger, performance_enabled


class RequestPerformanceLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started_at = time.perf_counter()
        query_start = len(connection.queries)
        response = self.get_response(request)

        if performance_enabled():
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            query_count = len(connection.queries) - query_start
            logger.info(
                'request method=%s path=%s status=%s elapsed_ms=%.2f queries=%s',
                request.method,
                request.path,
                response.status_code,
                elapsed_ms,
                query_count,
            )
            threshold = getattr(settings, 'RUNQUEST_SLOW_REQUEST_MS', 350)
            if elapsed_ms >= threshold:
                logger.warning(
                    'slow_request method=%s path=%s status=%s elapsed_ms=%.2f queries=%s',
                    request.method,
                    request.path,
                    response.status_code,
                    elapsed_ms,
                    query_count,
                )

        return response
