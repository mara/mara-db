import shlex
from time import sleep
import pytest
import typing as t
import subprocess
import pathlib

from mara_db import dbs, shell

from .command_helper import *


# the configured parameters in docker
POSTGRES_USER = "mara"
POSTGRES_DATABASE = "mara"
POSTGRES_PASSWORD = "mara"


def postgres_is_responsive(host, port) -> bool:
    """Returns True when Postgres is available on the given port, otherwise False"""
    import socket
    a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    location = (host, port)
    result_of_check = a_socket.connect_ex(location)
    if result_of_check == 0:
        a_socket.close()
        return True
    else:
        return False


@pytest.fixture(scope="session")
def postgres_db(docker_ip, docker_services) -> t.Tuple[str, int]:
    """Ensures that PostgreSQL server is running on docker."""

    port = docker_services.port_for("postgres", 5432)

    # here we need to wait until the PostgreSQL port is available.
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: postgres_is_responsive(docker_ip, port)
    )
    # I don't why but the port check above seems not to work, so I just added a simple sleep
    # of 7 seconds hoping that then everything is fine.
    sleep(7)

    return dbs.PostgreSQLDB(host=docker_ip, port=port, user=POSTGRES_USER, password=POSTGRES_PASSWORD, database=POSTGRES_DATABASE)


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