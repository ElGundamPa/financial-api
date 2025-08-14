#!/usr/bin/env python3
"""
Test mínimo para verificar que pytest funciona en CI
"""

import pytest


def test_basic():
    """Test básico que siempre pasa"""
    assert True


def test_math():
    """Test de matemáticas básicas"""
    assert 1 + 1 == 2
    assert 2 * 3 == 6


def test_string():
    """Test de strings"""
    assert "hello" + " world" == "hello world"


if __name__ == "__main__":
    pytest.main([__file__])
