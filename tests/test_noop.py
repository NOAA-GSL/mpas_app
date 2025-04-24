import scripts
import ush
from pytest import fixture

@fixture
def n():
    return 42


def test_n(n):
    assert n == 42


def test_regtest_n(n):
    assert n == 42
