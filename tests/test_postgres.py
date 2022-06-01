import pytest
import typing as t
import sqlalchemy
import subprocess
import pathlib

from mara_db import dbs, shell

from .command_helper import *


# the configured parameters in docker
POSTGRES_USER = "mara"
POSTGRES_DATABASE = "mara"
POSTGRES_PASSWORD = "mara"


def db_is_responsive(db: dbs.DB) -> bool:
    """Returns True when Postgres is available on the given port, otherwise False"""
    engine = sqlalchemy.create_engine(db.sqlalchemy_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            return True
    except:
        return False


@pytest.fixture(scope="session")
def postgres_db(docker_ip, docker_services) -> t.Tuple[str, int]:
    """Ensures that PostgreSQL server is running on docker."""

    docker_port = docker_services.port_for("postgres", 5432)
    db = dbs.PostgreSQLDB(host=docker_ip, port=docker_port, user=POSTGRES_USER, password=POSTGRES_PASSWORD, database=POSTGRES_DATABASE)

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
    test_postgres_ddl_file_path = str((pathlib.Path(__file__).parent / 'test_postgres_ddl.sql').absolute())
    command = execute_sql_file_command(postgres_db, test_postgres_ddl_file_path)
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0

@pytest.mark.dependency(depends=["test_postgres_shell_query_command", "test_postgres_shell_copy_to_stout", "test_postgres_ddl"])
def test_postgres_shell_copy_from_stdin_csv_noheader(postgres_db):
    # reading csv file...
    names_csv_file_path = str((pathlib.Path(__file__).parent / 'names.csv').absolute())
    command = f'cat {names_csv_file_path} \\\n'
    command += '  | ' + shell.copy_from_stdin_command(postgres_db,target_table='names',csv_format=True,skip_header=False,delimiter_char=',')
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
def test_postgres_shell_copy_from_stdin_csv_skipheader(postgres_db):
    # reading csv file...
    names_csv_file_path = str((pathlib.Path(__file__).parent / 'names_header.csv').absolute())
    command = f'cat {names_csv_file_path} \\\n'
    command += '  | ' + shell.copy_from_stdin_command(postgres_db,target_table='names_with_header',csv_format=True,skip_header=True,delimiter_char=',')
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


def test_postgres_sqlalchemy(postgres_db):
    """
    A simple test to check if the SQLAlchemy connection works
    """
    from mara_db.sqlalchemy_engine import engine
    from sqlalchemy import select

    eng = engine(postgres_db)

    with eng.connect() as conn:
        # run a SELECT 1.   use a core select() so that
        # the SELECT of a scalar value without a table is
        # appropriately formatted for the backend
        assert conn.scalar(select([1])) == 1
