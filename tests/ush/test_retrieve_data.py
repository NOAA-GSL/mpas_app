import datetime as dt
import sys
from io import StringIO
from pathlib import Path

from uwtools.api.template import render

from ush import retrieve_data


def test_import():
    assert retrieve_data


def test_try_data_store_disk(tmp_path):
    file_path = tmp_path / "{{ cycle.strftime('%Y%m%d%H') }}"
    output_path = tmp_path / "output"
    output_path.mkdir()
    tmp_file = "tmp.f{{ lead_time.seconds / 3600 }}"
    existing_file_template = file_path / tmp_file
    cycle = dt.datetime.now(tz=dt.timezone.utc)
    lead_times = [dt.timedelta(hours=6), dt.timedelta(hours=12)]

    for lead_time in lead_times:
        input_stream = StringIO(str(existing_file_template))
        sys.stdin = input_stream
        values = {
            "cycle": cycle,
            "lead_time": lead_time,
        }
        new_file = Path(render(values_src=values, stdin_ok=True))
        new_file.parent.mkdir(parents=True, exist_ok=True)
        new_file.touch()

    success = retrieve_data.try_data_store(
        cycle=cycle,
        data_store="disk",
        file_path=file_path,
        file_templates=[tmp_file],
        lead_times=lead_times,
        members=[0],
        output_path=output_path,
    )
    assert (output_path / new_file.name).is_file()
