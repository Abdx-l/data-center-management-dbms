import sqlite3
import unittest

from dc import add_rack, add_server, add_service, database, incident, initialize, report


class DataCenterTests(unittest.TestCase):
    def setUp(self):
        self.db = database(":memory:")
        self.con = self.db.__enter__()
        self.addCleanup(lambda: self.db.__exit__(None, None, None))
        initialize(self.con)
        add_rack(self.con, "A1", 5)

    def test_slots_and_report(self):
        self.assertEqual(add_server(self.con, "one", "A1", 2, 300), 1)
        self.assertEqual(add_server(self.con, "two", "A1", 2, 200), 3)
        add_service(self.con, "api", "one", "platform")
        incident(self.con, "one", "replace disk", "high")
        self.assertEqual(report(self.con)[0], dict(rack="A1", capacity_units=5, used_units=4, free_units=1, watts=500, services=1, open_incidents=1))

    def test_capacity_and_collision(self):
        add_server(self.con, "one", "A1", 2, 300, 2)
        with self.assertRaises(ValueError): add_server(self.con, "two", "A1", 2, 300, 3)
        with self.assertRaises(ValueError): add_server(self.con, "two", "A1", 3, 300)

    def test_keys_and_unknown_host(self):
        with self.assertRaises(ValueError): add_service(self.con, "api", "missing", "platform")
        add_server(self.con, "one", "A1", 1, 100)
        with self.assertRaises(sqlite3.IntegrityError): add_server(self.con, "one", "A1", 1, 100)
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute("INSERT INTO incident(server_id,summary,severity) VALUES(999,'x','high')")


if __name__ == "__main__":
    unittest.main()

