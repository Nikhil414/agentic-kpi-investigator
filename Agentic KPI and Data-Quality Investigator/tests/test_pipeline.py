from pathlib import Path
import sys

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from generate_data import generate
from run_pipeline import DB, run


def test_pipeline_creates_expected_outputs():
    generate(seed=7, days=10)
    run()
    con = duckdb.connect(str(DB), read_only=True)
    assert con.sql("SELECT COUNT(*) FROM daily_kpis").fetchone()[0] == 10
    assert con.sql("SELECT COUNT(*) FROM quality_issues").fetchone()[0] == 0
    con.close()

