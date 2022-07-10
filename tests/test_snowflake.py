import pytest
import subprocess

from mara_db import shell, sqlalchemy_engine
from tests.local_config import SNOWFLAKE_DB


if not SNOWFLAKE_DB:
    pytest.skip("skipping SnowflakeDB tests: variable SNOWFLAKE_DB not set", allow_module_level=True)


def test_snowflake_query_command():
    command = 'echo "SELECT 1" \\\n'
    command += '  | ' + shell.query_command(SNOWFLAKE_DB)
    assert command

    print(command)
    (exitcode, _) = subprocess.getstatusoutput(command)
    assert exitcode == 0


def test_snowflake_copy_to_stdout():
    command = 'echo "SELECT 1 AS Col1, \'FOO\' AS Col2 UNION ALL SELECT 2, \'BAR\'" \\\n'
    command += '  | ' + shell.copy_to_stdout_command(SNOWFLAKE_DB,
        csv_format=True,
        header=True,
        delimiter_char=',')
    assert command

    print(command)
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0
    print(pstdout)
    assert pstdout == '''"COL1","COL2"
"1","FOO"
"2","BAR"'''


def test_snowflake_sqlalchemy():
    from sqlalchemy import text
    engine = sqlalchemy_engine.engine(SNOWFLAKE_DB)
    with engine.connect() as con:
        con.execute(statement = text("SELECT 1"))
