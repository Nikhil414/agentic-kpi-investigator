from pathlib import Path
import duckdb


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "processed" / "finance.duckdb"


def run() -> None:
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB))
    for sql_file in sorted((ROOT / "sql").glob("0*.sql")):
        con.execute(sql_file.read_text(encoding="utf-8"))
    print(con.execute("SELECT COUNT(*) AS days, ROUND(SUM(net_revenue), 2) AS revenue FROM daily_kpis").fetchdf().to_string(index=False))
    con.close()


if __name__ == "__main__":
    run()

