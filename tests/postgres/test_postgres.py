import pytest
import typing as t
import subprocess
import pathlib

from mara_db import shell, formats

from ..command_helper import *
from ..db_test_helper import db_is_responsive, db_replace_placeholders
from ..local_config import POSTGRES_DB


if not POSTGRES_DB:
    pytest.skip("skipping PostgreSQL tests: variable POSTGRES_DB not set", allow_module_level=True)


@pytest.fixture(scope="session")
def postgres_db(docker_ip, docker_services) -> t.Tuple[str, int]:
    """Ensures that PostgreSQL server is running on docker."""

    docker_port = docker_services.port_for("postgres", 5432)
    db = db_replace_placeholders(POSTGRES_DB, docker_ip, docker_port)

    # here we need to wait until the PostgreSQL port is available.
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: db_is_responsive(db)
    )

    return db


@pytest.mark.dependency()
def test_postgres_shell_query_command(postgres_db):
    command = execute_sql_statement_command(postgres_db, "SELECT 1")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0


@pytest.mark.dependency()
def test_postgres_shell_copy_to_stout(postgres_db):
    command = execute_sql_statement_to_stdout_csv_command(postgres_db, "SELECT 1 AS Col1, 'FOO' AS Col2 UNION ALL SELECT 2, 'BAR'")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0
    assert pstdout == '''1,FOO
2,BAR'''


@pytest.mark.dependency()
def test_postgres_ddl(postgres_db):
    """Creates DDL scripts required for other tests"""
    # run 'test_postgres_ddl.sql'
    ddl_file_path = str((pathlib.Path(__file__).parent / 'test_postgres_ddl.sql').absolute())
    command = execute_sql_file_command(postgres_db, ddl_file_path)
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0


@pytest.mark.dependency(depends=["test_postgres_shell_query_command", "test_postgres_shell_copy_to_stout", "test_postgres_ddl"])
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
def test_postgres_shell_copy_from_stdin_csv_noheader(postgres_db, seed_file):
    # delete rows from table, make sure that the last matrix test does not mess up this test
    command = execute_sql_statement_command(postgres_db, "DELETE FROM names")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0

    # reading csv file...
    file_path = str((pathlib.Path(__file__).parent / f'../seed/{seed_file}').absolute())
    command = f'cat {file_path} \\\n'
    command += '  | ' + shell.copy_from_stdin_command(postgres_db,target_table='names',
                            pipe_format=formats.CsvFormat(header=False, delimiter_char=','))
    print(command)

    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0

    # check if writing was successful

    command = execute_sql_statement_to_stdout_csv_command(postgres_db, "SELECT COUNT(*) FROM names")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0
    assert pstdout == "10"

    command = execute_sql_statement_to_stdout_csv_command(postgres_db, "SELECT name FROM names WHERE id = 1")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0
    assert pstdout == "Elinor Meklit"


@pytest.mark.dependency(depends=["test_postgres_shell_query_command", "test_postgres_shell_copy_to_stout", "test_postgres_ddl"])
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
def test_postgres_shell_copy_from_stdin_csv_skipheader(postgres_db, seed_file):
    # delete rows from table, make sure that the last matrix test does not mess up this test
    command = execute_sql_statement_command(postgres_db, "DELETE FROM names_with_header")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0

    # reading csv file...
    file_path = str((pathlib.Path(__file__).parent / f'../seed/{seed_file}').absolute())
    command = f'cat {file_path} \\\n'
    command += '  | ' + shell.copy_from_stdin_command(postgres_db,
                            target_table='names_with_header',
                            pipe_format=formats.CsvFormat(header=True, delimiter_char=','))
    print(command)

    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0

    # check if writing was successful

    command = execute_sql_statement_to_stdout_csv_command(postgres_db, "SELECT COUNT(*) FROM names_with_header")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0
    assert pstdout == "10"

    command = execute_sql_statement_to_stdout_csv_command(postgres_db, "SELECT name FROM names_with_header WHERE id = 1")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0
    assert pstdout == "Elinor Meklit"


@pytest.mark.dependency(depends=["test_postgres_shell_query_command", "test_postgres_shell_copy_to_stout", "test_postgres_ddl"])
@pytest.mark.parametrize(
    "seed_file",
    [
        "accounts_crlf_lastrow.jsonl",
        "accounts_crlf.jsonl",
        "accounts_lf_lastrow.jsonl",
        "accounts_lf.jsonl",
    ]
)
def test_postgres_shell_copy_from_stdin_jsonl(postgres_db, seed_file):
    # delete rows from table, make sure that the last matrix test does not mess up this test
    command = execute_sql_statement_command(postgres_db, "DELETE FROM accounts_json")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0

    # reading csv file...
    file_path = str((pathlib.Path(__file__).parent / f'../seed/{seed_file}').absolute())
    command = f'cat {file_path} \\\n'
    command += '  | ' + shell.copy_from_stdin_command(postgres_db,
                            target_table='accounts_json',
                            format=formats.JsonlFormat())
    print(command)

    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0

    # check if writing was successful

    command = execute_sql_statement_to_stdout_csv_command(postgres_db, "SELECT COUNT(*) FROM accounts_json")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0
    assert pstdout == "6"

    command = execute_sql_statement_to_stdout_csv_command(postgres_db, "SELECT COUNT(*) FROM accounts_json WHERE data IS NOT NULL")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0
    assert pstdout == "6"


def test_postgres_sqlalchemy(postgres_db):
    """
    A simple test to check if the SQLAlchemy connection works
    """
    from ..db_test_helper import _test_sqlalchemy
    _test_sqlalchemy(postgres_db)


def test_postgres_connect(postgres_db):
    """
    A simple test to check if the connect API works.
    """
    from ..db_test_helper import _test_connect
    _test_connect(postgres_db)


def test_postgres_cursor_context(postgres_db):
    """
    A simple test to check if the cursor context of the db works.
    """
    from ..db_test_helper import _test_cursor_context
    _test_cursor_context(postgres_db)


def test_postgres_cursor_context_legacy(postgres_db):
    """
    Legacy call `postgres_cursor_context` test.
    
    Test shall be dropped in version 5.0
    """
    from mara_db.postgresql import postgres_cursor_context

    with postgres_cursor_context(postgres_db) as cursor:
        cursor.execute('SELECT 1')
        row = cursor.fetchone()
        assert row[0] == 1
