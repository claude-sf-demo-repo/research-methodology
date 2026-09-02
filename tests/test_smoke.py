import importlib


def test_package_imports():
    mod = importlib.import_module("research_methodology")
    assert mod is not None
