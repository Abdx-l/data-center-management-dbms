import argparse
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import sys

SCHEMA = Path(__file__).with_name("schema.sql")


@contextmanager
def database(path):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def initialize(con):
    con.executescript(SCHEMA.read_text(encoding="utf-8"))


def add_rack(con, code, capacity):
    con.execute("INSERT INTO rack(code, capacity_units) VALUES(?,?)", (code, capacity))


def add_server(con, hostname, rack_code, units, watts, start_unit=None):
    rack = con.execute("SELECT id, capacity_units FROM rack WHERE code=?", (rack_code,)).fetchone()
    if rack is None:
        raise ValueError("unknown rack")
    occupied = set()
    for server in con.execute("SELECT start_unit, units FROM server WHERE rack_id=?", (rack["id"],)):
        occupied.update(range(server["start_unit"], server["start_unit"] + server["units"]))
    if units <= 0 or watts < 0:
        raise ValueError("units must be positive and watts nonnegative")
    candidates = [start_unit] if start_unit is not None else range(1, rack["capacity_units"] - units + 2)
    start = next((slot for slot in candidates if slot is not None and slot > 0 and slot + units - 1 <= rack["capacity_units"] and not occupied.intersection(range(slot, slot + units))), None)
    if start is None:
        raise ValueError("no contiguous free rack units")
    con.execute("INSERT INTO server(hostname,rack_id,start_unit,units,watts) VALUES(?,?,?,?,?)",
                (hostname, rack["id"], start, units, watts))
    return start


def add_service(con, name, hostname, owner):
    con.execute("INSERT INTO service(name,server_id,owner) SELECT ?,id,? FROM server WHERE hostname=?",
                (name, owner, hostname))
    if con.execute("SELECT changes()").fetchone()[0] != 1:
        raise ValueError("unknown server")


def incident(con, hostname, summary, severity):
    con.execute("INSERT INTO incident(server_id,summary,severity) SELECT id,?,? FROM server WHERE hostname=?",
                (summary, severity, hostname))
    if con.execute("SELECT changes()").fetchone()[0] != 1:
        raise ValueError("unknown server")


def report(con):
    return [dict(row) for row in con.execute("""
        SELECT r.code AS rack, r.capacity_units, COALESCE(SUM(s.units),0) AS used_units,
               r.capacity_units - COALESCE(SUM(s.units),0) AS free_units,
               COALESCE(SUM(s.watts),0) AS watts,
               (SELECT COUNT(*) FROM service v JOIN server x ON v.server_id=x.id WHERE x.rack_id=r.id) AS services,
               (SELECT COUNT(*) FROM incident i JOIN server x ON i.server_id=x.id
                WHERE x.rack_id=r.id AND i.closed_at IS NULL) AS open_incidents
        FROM rack r LEFT JOIN server s ON s.rack_id=r.id
        GROUP BY r.id ORDER BY r.code
    """)]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Data center inventory")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "report", "check"):
        command = sub.add_parser(name)
        command.add_argument("database")
    rack = sub.add_parser("add-rack")
    rack.add_argument("database"); rack.add_argument("code"); rack.add_argument("--capacity", type=int, required=True)
    server = sub.add_parser("add-server")
    server.add_argument("database"); server.add_argument("hostname"); server.add_argument("rack")
    server.add_argument("--units", type=int, required=True); server.add_argument("--watts", type=int, required=True)
    server.add_argument("--start-unit", type=int)
    service = sub.add_parser("add-service")
    service.add_argument("database"); service.add_argument("name"); service.add_argument("hostname")
    service.add_argument("--owner", required=True)
    issue = sub.add_parser("incident")
    issue.add_argument("database"); issue.add_argument("hostname"); issue.add_argument("summary")
    issue.add_argument("--severity", choices=("low", "medium", "high"), required=True)
    backup = sub.add_parser("backup")
    backup.add_argument("database"); backup.add_argument("destination")
    args = parser.parse_args(argv)
    try:
        if args.command == "backup":
            with database(args.database) as con, sqlite3.connect(args.destination) as target:
                con.backup(target)
            print(args.destination)
            return 0
        with database(args.database) as con:
            if args.command == "init": initialize(con)
            elif args.command == "add-rack": add_rack(con, args.code, args.capacity)
            elif args.command == "add-server": print(f"U{add_server(con, args.hostname, args.rack, args.units, args.watts, args.start_unit)}")
            elif args.command == "add-service": add_service(con, args.name, args.hostname, args.owner)
            elif args.command == "incident": incident(con, args.hostname, args.summary, args.severity)
            elif args.command == "report":
                for row in report(con): print(row)
            elif args.command == "check":
                result = con.execute("PRAGMA integrity_check").fetchone()[0]
                print(result)
                return 0 if result == "ok" else 1
        return 0
    except (sqlite3.Error, ValueError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    sys.exit(main())

