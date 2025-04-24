from pytest import fixture
from scripts import mpas_init, mpas, ungrib, upp
from ush import experiment_gen, retrieve_data

@fixture
def n():
    return 42


def test_n(n):
    assert n == 42


def test_regtest_n(n):
    assert n == 42
