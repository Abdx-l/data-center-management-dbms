# Data Center Management DBMS

Relational inventory and operations database for racks, servers, services, and maintenance incidents. The runnable reference implementation uses SQLite so it can be explored without an Oracle installation. `oracle/schema.sql` contains the corresponding Oracle DDL for the principal entities.

## Run

```sh
python dc.py init center.db
python dc.py add-rack center.db R1 --capacity 12
python dc.py add-server center.db srv-01 R1 --units 2 --watts 350
python dc.py add-service center.db api srv-01 --owner platform
python dc.py incident center.db srv-01 "Disk replacement" --severity high
python dc.py report center.db
python -m unittest discover -s tests -v
```

The schema enforces foreign keys, unique physical slots, power and rack-capacity constraints through transactional commands. Report output includes available rack units, server power, service counts, and open incidents. An example Unix shell script performs a daily backup and integrity check. This project does not monitor physical equipment or connect to an external asset system.

