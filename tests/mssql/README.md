SQL Server Test Matrix
======================

There some notes about which tests failes / are on purpose not implemented:

sqsh
----
* does not support `trust_server_certificate`

sqlcmd
------
All looks fine

bcp
---

Known issues:
* return value is always zero (`0`) even when an import error occurs
* a import file e.g. CSV must have a last empty row (`names_lf_lastrow.csv` is supported, but `names_lf.csv` not)
* db.`trust_server_certificate` is only supported when using mssql tools 18+ and higher
