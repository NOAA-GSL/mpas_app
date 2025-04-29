from ush import retrieve_data


def test_import():
    assert retrieve_data


def test_try_data_store():
    success = try_data_store(
        data_store="disk",
        cycle=dt.now(),
        lead_times=[dt.timedelta(hours=6), dt.timedelta(hours=12)],
    )
    assert success is True
