import pytest
import typing as t
import subprocess
import pathlib

from mara_db import shell, formats

from ..command_helper import *
from ..db_test_helper import db_is_responsive, db_replace_placeholders
from ..local_config import DUCKDB_DB


if not DUCKDB_DB:
    pytest.skip("skipping DuckDB tests: variable DUCKDB_DB not set", allow_module_level=True)


@pytest.mark.dependency()
def test_duckdb_shell_query_command(duckdb_db):
    command = execute_sql_statement_command(duckdb_db, "SELECT 1")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0


@pytest.mark.dependency()
def test_duckdb_shell_copy_to_stout(duckdb_db):
    command = execute_sql_statement_to_stdout_csv_command(duckdb_db, "SELECT 1 AS Col1, 'FOO' AS Col2 UNION ALL SELECT 2, 'BAR'")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0
    assert pstdout == '''1,FOO
2,BAR'''


@pytest.mark.dependency()
def test_duckdb_ddl(duckdb_db):
    """Creates DDL scripts required for other tests"""
    # run 'test_duckdb_ddl.sql'
    ddl_file_path = str((pathlib.Path(__file__).parent / 'test_duckdb_ddl.sql').absolute())
    command = execute_sql_file_command(duckdb_db, ddl_file_path)
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0


@pytest.mark.dependency(depends=["test_duckdb_shell_query_command", "test_duckdb_shell_copy_to_stout", "test_duckdb_ddl"])
@pytest.mark.parametrize(
    "seed_file",
    [
        "names_crlf_lastrow.csv",
        "names_crlf_quoted_lastrow.csv",
        "names_crlf_quoted.csv",
        "names_crlf.csv",
        "names_lf_lastrow.csv",
        "names_lf_quoted_lastrow.csv",
        "names_lf_quoted.csv",
        "names_lf.csv",
    ]
)
def test_duckdb_shell_copy_from_stdin_csv_noheader(duckdb_db, seed_file):
    # delete rows from table, make sure that the last matrix test does not mess up this test
    command = execute_sql_statement_command(duckdb_db, "DELETE FROM names")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0

    # reading csv file...
    file_path = str((pathlib.Path(__file__).parent / f'../seed/{seed_file}').absolute())
    command = f'cat {file_path} \\\n'
    command += '  | ' + shell.copy_from_stdin_command(duckdb_db,target_table='names',
                            pipe_format=formats.CsvFormat(header=False, delimiter_char=','))
    print(command)

    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0

    # check if writing was successful

    command = execute_sql_statement_to_stdout_csv_command(duckdb_db, "SELECT COUNT(*) FROM names")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0
    assert pstdout == "10"

    command = execute_sql_statement_to_stdout_csv_command(duckdb_db, "SELECT name FROM names WHERE id = 1")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0
    assert pstdout == "Elinor Meklit"


@pytest.mark.dependency(depends=["test_duckdb_shell_query_command", "test_duckdb_shell_copy_to_stout", "test_duckdb_ddl"])
@pytest.mark.parametrize(
    "seed_file",
    [
        "names_crlf_lastrow_header.csv",
        "names_crlf_quoted_lastrow_header.csv",
        "names_crlf_quoted_header.csv",
        "names_crlf_header.csv",
        "names_lf_lastrow_header.csv",
        "names_lf_quoted_lastrow_header.csv",
        "names_lf_quoted_header.csv",
        "names_lf_header.csv",
    ]
)
def test_duckdb_shell_copy_from_stdin_csv_skipheader(duckdb_db, seed_file):
    # delete rows from table, make sure that the last matrix test does not mess up this test
    command = execute_sql_statement_command(duckdb_db, "DELETE FROM names_with_header")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0

    # reading csv file...
    file_path = str((pathlib.Path(__file__).parent / f'../seed/{seed_file}').absolute())
    command = f'cat {file_path} \\\n'
    command += '  | ' + shell.copy_from_stdin_command(duckdb_db,
                            target_table='names_with_header',
                            pipe_format=formats.CsvFormat(header=True, delimiter_char=','))
    print(command)

    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0

    # check if writing was successful

    command = execute_sql_statement_to_stdout_csv_command(duckdb_db, "SELECT COUNT(*) FROM names_with_header")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0
    assert pstdout == "10"

    command = execute_sql_statement_to_stdout_csv_command(duckdb_db, "SELECT name FROM names_with_header WHERE id = 1")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0
    assert pstdout == "Elinor Meklit"


@pytest.mark.dependency(depends=["test_duckdb_shell_query_command", "test_duckdb_shell_copy_to_stout", "test_duckdb_ddl"])
@pytest.mark.parametrize(
    "seed_file",
    [
        "accounts_crlf_lastrow.jsonl",
        "accounts_crlf.jsonl",
        "accounts_lf_lastrow.jsonl",
        "accounts_lf.jsonl",
    ]
)
def test_duckdb_shell_copy_from_stdin_jsonl(duckdb_db, seed_file):
    # delete rows from table, make sure that the last matrix test does not mess up this test
    command = execute_sql_statement_command(duckdb_db, "DELETE FROM accounts_json")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0

    # reading csv file...
    file_path = str((pathlib.Path(__file__).parent / f'../seed/{seed_file}').absolute())
    command = f'cat {file_path} \\\n'
    command += '  | ' + shell.copy_from_stdin_command(duckdb_db,
                            target_table='accounts_json',
                            pipe_format=formats.JsonlFormat())
    print(command)

    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0

    # check if writing was successful

    command = execute_sql_statement_to_stdout_csv_command(duckdb_db, "SELECT COUNT(*) FROM accounts_json")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0
    assert pstdout == "6"

    command = execute_sql_statement_to_stdout_csv_command(duckdb_db, "SELECT COUNT(*) FROM accounts_json WHERE data IS NOT NULL")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0
    assert pstdout == "6"


def test_duckdb_sqlalchemy(duckdb_db):
    """
    A simple test to check if the SQLAlchemy connection works
    """
    from ..db_test_helper import _test_sqlalchemy
    _test_sqlalchemy(duckdb_db)


def test_duckdb_connect(duckdb_db):
    """
    A simple test to check if the connect API works.
    """
    from ..db_test_helper import _test_connect
    _test_connect(duckdb_db)


def test_duckdb_cursor_context(duckdb_db):
    """
    A simple test to check if the cursor context of the db works.
    """
    from ..db_test_helper import _test_cursor_context
    _test_cursor_context(duckdb_db)
