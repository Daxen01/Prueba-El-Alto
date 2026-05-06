"""Unit tests for the haversine distance formula."""

from app.core.geo import haversine


def test_same_point_is_zero():
    assert haversine(0.0, 0.0, 0.0, 0.0) == 0.0


def test_symmetry():
    d1 = haversine(1.0, 2.0, 3.0, 4.0)
    d2 = haversine(3.0, 4.0, 1.0, 2.0)
    assert abs(d1 - d2) < 1e-9


def test_known_distance_santiago_antofagasta():
    """Santiago → Antofagasta ≈ 1150 km (rough estimate)."""
    d = haversine(-33.45, -70.67, -23.65, -70.40)
    assert 1050 < d < 1250


def test_equator_90_degrees():
    """Quarter of Earth's circumference ≈ 10008 km along the equator."""
    d = haversine(0.0, 0.0, 0.0, 90.0)
    assert 9900 < d < 10100


def test_returns_float():
    result = haversine(-23.65, -70.40, -23.70, -70.45)
    assert isinstance(result, float)
    assert result > 0
