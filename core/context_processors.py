"""Context processors for Logistic365."""

from transport.models import Vehicle


def global_stats(request):
    """Добавляет счётчик ТС в контекст каждого запроса."""
    return {
        "total_vehicles_count": Vehicle.objects.count(),
    }
