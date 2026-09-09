from django.db import DatabaseError, connection
from django.http import JsonResponse


def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return JsonResponse(
            {"error": {"status": 503, "details": "Database unavailable."}}, status=503
        )
    return JsonResponse({"status": "ok"})
