import pytest
import subprocess

from mara_db import shell, sqlalchemy_engine
from tests.local_config import DATABRICKS_DB


if not DATABRICKS_DB:
    pytest.skip("skipping DatabricksDB tests: variable DATABRICKS_DB not set", allow_module_level=True)


def test_databricks_query_command():
    command = 'echo "SELECT 1" \\\n'
    command += '  | ' + shell.query_command(DATABRICKS_DB)
    assert command

    print(command)
    (exitcode, _) = subprocess.getstatusoutput(command)
    assert exitcode == 0


def test_databricks_copy_to_stdout():
    command = 'echo "SELECT 1 AS Col1, \'FOO\' AS Col2 UNION ALL SELECT 2, \'BAR\'" \\\n'
    command += '  | ' + shell.copy_to_stdout_command(DATABRICKS_DB,
        csv_format=True,
        header=True,
        delimiter_char=',')
    assert command

    print(command)
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0
    print(pstdout)
    assert pstdout == '''Col1,Col2
1,FOO
2,BAR'''


def test_databricks_sqlalchemy():
    from sqlalchemy import text
    engine = sqlalchemy_engine.engine(DATABRICKS_DB)
    with engine.connect() as con:
        con.execute(statement = text("SELECT 1"))


def test_databricks_connect():
    """
    A simple test to check if the connect API works.
    """
    from .db_test_helper import _test_connect
    _test_connect(DATABRICKS_DB)


def test_databricks_cursor_context():
    """
    A simple test to check if the cursor context of the db works.
    """
    from .db_test_helper import _test_cursor_context
    _test_cursor_context(DATABRICKS_DB)
