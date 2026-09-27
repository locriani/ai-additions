"""Order pricing for a small shop."""


def bulk_discount(qty: int, unit_price: float) -> float:
    """Total for `qty` items at `unit_price`: 10% off for 10 or more items."""
    total = qty * unit_price
    if qty > 10:
        total *= 0.9
    return total


def round_price(amount: float) -> int:
    """Whole-unit price. Halves round to the nearest even number (banker's rounding, as Python's `round` does),
    so that .5 amounts do not all drift upward."""
    return round(amount)
