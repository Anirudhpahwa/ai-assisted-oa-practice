from .models import CountLine


def record_count(session, product, counted, actor):
    """Record a counted quantity; a recount updates the existing line."""
    line, created = CountLine.objects.get_or_create(
        session=session,
        product=product,
        defaults={
            "expected": product.on_hand,
            "counted": counted,
            "variance": counted - product.on_hand,
            "counted_by": actor,
        },
    )
    if not created:
        line.counted = counted
        line.counted_by = actor
        line.save()
    return line, created
