"""Pure calculation helpers for CornProfit Connect."""
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Optional

CENT = Decimal("0.01")

def money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(CENT, rounding=ROUND_HALF_UP)

def sum_amounts(values: Iterable) -> Decimal:
    return money(sum((Decimal(str(v or 0)) for v in values), Decimal("0")))

def profit_loss(income, expenses):
    return money(Decimal(str(income or 0)) - Decimal(str(expenses or 0)))

def budget_total(items):
    return sum_amounts(items)

def budget_shortage(capital, planned_cost):
    return money(max(Decimal("0"), Decimal(str(planned_cost or 0)) - Decimal(str(capital or 0))))

def capital_remaining(capital, planned_cost):
    return money(Decimal(str(capital or 0)) - Decimal(str(planned_cost or 0)))

def break_even_price(total_cost, saleable_kg):
    qty = Decimal(str(saleable_kg or 0))
    if qty <= 0:
        return None
    return money(Decimal(str(total_cost or 0)) / qty)

def estimated_revenue(quantity_kg, price_per_kg):
    return money(Decimal(str(quantity_kg or 0)) * Decimal(str(price_per_kg or 0)))

def fuel_cost(round_trip_km, liters_per_km, fuel_price_per_liter):
    vals = [Decimal(str(x or 0)) for x in (round_trip_km, liters_per_km, fuel_price_per_liter)]
    if any(x < 0 for x in vals):
        raise ValueError("Transportation inputs cannot be negative.")
    return money(vals[0] * vals[1] * vals[2])

def transport_total(fuel, loading=0, tolls=0, other=0, hired_vehicle_fee=None):
    if hired_vehicle_fee is not None:
        if Decimal(str(hired_vehicle_fee)) < 0:
            raise ValueError("Vehicle fee cannot be negative.")
        return money(hired_vehicle_fee)
    vals = [Decimal(str(x or 0)) for x in (fuel, loading, tolls, other)]
    if any(x < 0 for x in vals):
        raise ValueError("Transportation costs cannot be negative.")
    return money(sum(vals, Decimal("0")))

def buyer_gross(quantity_kg, price_per_kg):
    return estimated_revenue(quantity_kg, price_per_kg)

def buyer_net(quantity_kg, price_per_kg, transport=0, fixed_deductions=0, percentage_deduction=0):
    gross = buyer_gross(quantity_kg, price_per_kg)
    pct = Decimal(str(percentage_deduction or 0))
    if pct < 0 or pct > 100:
        raise ValueError("Percentage deduction must be between 0 and 100.")
    deductions = money(Decimal(str(fixed_deductions or 0)) + gross * pct / Decimal("100"))
    return money(gross - Decimal(str(transport or 0)) - deductions)

def group_quantity(quantities):
    vals = [Decimal(str(q or 0)) for q in quantities]
    if any(q < 0 for q in vals):
        raise ValueError("Contributed quantities cannot be negative.")
    return money(sum(vals, Decimal("0")))

def allocate_shared_cost(total_cost, quantities, method="Proportional to quantity", custom_amounts=None):
    """Returns cost allocations. Proportional/equal allocations are rounded to cents; final member absorbs rounding remainder."""
    total = money(total_cost)
    if total < 0:
        raise ValueError("Shared cost cannot be negative.")
    n = len(quantities)
    if n == 0:
        if total != 0:
            raise ValueError("Cannot allocate cost without members.")
        return []
    qs = [Decimal(str(q or 0)) for q in quantities]
    if any(q < 0 for q in qs):
        raise ValueError("Quantities cannot be negative.")
    if method == "Custom agreed amounts":
        if custom_amounts is None or len(custom_amounts) != n:
            raise ValueError("Provide one custom allocation per member.")
        alloc = [money(x) for x in custom_amounts]
        if any(x < 0 for x in alloc) or sum(alloc, Decimal("0")) != total:
            raise ValueError("Custom allocations must be nonnegative and sum exactly to shared cost.")
        return alloc
    if method == "Equal sharing":
        raw = [total / n for _ in range(n)]
    elif method == "Proportional to quantity":
        qsum = sum(qs, Decimal("0"))
        if qsum == 0 and total > 0:
            raise ValueError("Total quantity must be positive for proportional allocation.")
        raw = [total * q / qsum if qsum else Decimal("0") for q in qs]
    else:
        raise ValueError("Unknown cost-sharing method.")
    alloc = [money(x) for x in raw]
    alloc[-1] = money(alloc[-1] + total - sum(alloc, Decimal("0")))
    return alloc
