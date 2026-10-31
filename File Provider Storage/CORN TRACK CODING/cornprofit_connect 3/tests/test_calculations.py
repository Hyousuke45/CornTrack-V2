from decimal import Decimal
import pytest
from calculations import *

def test_expenses_income_profit():
    assert sum_amounts([100, 250, 50]) == Decimal("400.00")
    assert estimated_revenue(2000, 14) == Decimal("28000.00")
    assert profit_loss(28000, 600) == Decimal("27400.00")

def test_budget_and_shortage():
    assert budget_total([1000, 2000, 500]) == Decimal("3500.00")
    assert budget_shortage(3000, 3500) == Decimal("500.00")
    assert capital_remaining(3000, 2500) == Decimal("500.00")

def test_break_even_and_zero():
    assert break_even_price(15000, 3000) == Decimal("5.00")
    assert break_even_price(15000, 0) is None

def test_buyer_net_examples():
    assert buyer_net(2000, 14, transport=600) == Decimal("27400.00")
    assert buyer_net(2000, 13.5, transport=300, fixed_deductions=200) == Decimal("26500.00")

def test_fuel_and_transport():
    assert fuel_cost(100, .1, 60) == Decimal("600.00")
    assert transport_total(600, 100, 50, 25) == Decimal("775.00")
    assert transport_total(600, 100, 50, 25, hired_vehicle_fee=800) == Decimal("800.00")

def test_group_allocation():
    assert group_quantity([800, 1200, 1000]) == Decimal("3000.00")
    alloc = allocate_shared_cost(600, [800, 1200, 1000])
    assert sum(alloc) == Decimal("600.00")
    assert allocate_shared_cost(90, [1, 1, 1], "Equal sharing") == [Decimal("30.00")]*3

def test_invalid_inputs():
    with pytest.raises(ValueError):
        fuel_cost(-1, .1, 60)
    with pytest.raises(ValueError):
        allocate_shared_cost(100, [1, 1], "Custom agreed amounts", [40, 40])
    with pytest.raises(ValueError):
        buyer_net(10, 5, percentage_deduction=101)
