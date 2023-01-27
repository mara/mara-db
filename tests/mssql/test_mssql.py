import pathlib
import pytest
import subprocess
import typing as t

from mara_db import dbs

from ..command_helper import *
from ..db_test_helper import db_is_responsive, db_replace_placeholders
from ..local_config import MSSQL_DB, MSSQL_SQSH_DB, MSSQL_SQLCMD_DB


if not MSSQL_DB:
    pytest.skip("skipping SQLServerDB tests: variable MSSQL_DB not set", allow_module_level=True)


@pytest.fixture(scope="session")
def mssql_db(docker_ip, docker_services) -> t.Tuple[str, int]:
    """Ensures that SQL Server server is running on docker."""

    docker_port = docker_services.port_for("mssql", 1433)
    db = db_replace_placeholders(MSSQL_DB, docker_ip, docker_port)

    # here we need to wait until the SQL Server port is available.
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: db_is_responsive(db)
    )

    return db


@pytest.mark.dependency()
def test_mssql_shell_query_command(mssql_db):
    command = execute_sql_statement_command(mssql_db, "SELECT 1")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0


@pytest.mark.dependency(depends=['test_mssql_shell_query_command'])
def test_mssql_ddl(mssql_db):
    """Creates DDL scripts required for other tests"""
    # run 'test_mssql_ddl.sql'
    ddl_file_path = str((pathlib.Path(__file__).parent / 'test_mssql_ddl.sql').absolute())
    command = execute_sql_file_command(mssql_db, ddl_file_path)
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0


def test_mssql_sqlalchemy(mssql_db):
    """
    A simple test to check if the SQLAlchemy connection works
    """
    from ..db_test_helper import _test_sqlalchemy
    _test_sqlalchemy(mssql_db)


def test_mssql_connect(mssql_db):
    """
    A simple test to check if the connect API works.
    """
    from ..db_test_helper import _test_connect
    _test_connect(mssql_db)



"""
#################################################################################################################################
# Tests specific to sqsh
"""

@pytest.fixture(scope="session")
def mssql_sqsh_db(docker_ip, docker_services) -> t.Tuple[str, int]:
    """Ensures that SQL Server server is running on docker."""

    docker_port = docker_services.port_for("mssql", 1433)
    db = db_replace_placeholders(MSSQL_SQSH_DB, docker_ip, docker_port)

    # here we need to wait until the SQL Server port is available.
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: db_is_responsive(db)
    )

    return db


@pytest.mark.dependency()
def test_mssql_sqsh_shell_query_command(mssql_sqsh_db):
    command = execute_sql_statement_command(mssql_sqsh_db, "SELECT 1")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0


@pytest.mark.dependency()
def test_mssql_sqsh_shell_copy_to_stout(mssql_sqsh_db):
    command = execute_sql_statement_to_stdout_csv_command(mssql_sqsh_db, "SELECT 1 AS Col1, 'FOO' AS Col2 UNION ALL SELECT 2, 'BAR'")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0
    assert pstdout == '''Col1,Col2
1,"FOO"
2,"BAR"'''



"""
#################################################################################################################################
# Tests specific to sqlcmd
"""

@pytest.fixture(scope="session")
def mssql_sqlcmd_db(docker_ip, docker_services) -> t.Tuple[str, int]:
    """Ensures that SQL Server server is running on docker."""

    docker_port = docker_services.port_for("mssql", 1433)
    db = db_replace_placeholders(MSSQL_SQLCMD_DB, docker_ip, docker_port)

    # here we need to wait until the SQL Server port is available.
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: db_is_responsive(db)
    )

    return db


@pytest.mark.dependency()
def test_mssql_sqlcmd_shell_query_command(mssql_sqlcmd_db):
    command = execute_sql_statement_command(mssql_sqlcmd_db, "SELECT 1")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0


@pytest.mark.dependency()
def test_mssql_sqlcmd_shell_copy_to_stout(mssql_sqlcmd_db):
    command = execute_sql_statement_to_stdout_csv_command(mssql_sqlcmd_db, "SELECT 1 AS Col1, 'FOO' AS Col2 UNION ALL SELECT 2, 'BAR'")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0
    assert pstdout == '''1,FOO
2,BAR'''


@pytest.mark.dependency(depends=["test_mssql_sqlcmd_shell_query_command", "test_mssql_sqlcmd_shell_copy_to_stout", "test_mssql_ddl"])
@pytest.mark.parametrize(
    "seed_file",
    [
        "names_lf_lastrow.csv",
        "names_crlf_lastrow.csv",
        # BCP only supports unquited, last row ending files
    ]
)
def test_mssql_sqlcmd_shell_copy_from_stdin_csv_noheader(mssql_sqlcmd_db, seed_file):
    # delete rows from table, make sure that the last matrix test does not mess up this test
    command = execute_sql_statement_command(mssql_sqlcmd_db, "DELETE FROM names")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0

    # reading csv file...
    names_csv_file_path = str((pathlib.Path(__file__).parent / f'../seed/{seed_file}').absolute())
    command = f'cat {names_csv_file_path} \\\n'
    command += '  | ' + shell.copy_from_stdin_command(mssql_sqlcmd_db,target_table='names',csv_format=True,skip_header=False,delimiter_char=',')
    print(command)

    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0

    # check if writing was successful

    command = execute_sql_statement_to_stdout_csv_command(mssql_sqlcmd_db, "SELECT COUNT(*) FROM names")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0
    assert pstdout == "10"

    command = execute_sql_statement_to_stdout_csv_command(mssql_sqlcmd_db, "SELECT name FROM names WHERE id = 1")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0
    assert pstdout == "Elinor Meklit"


@pytest.mark.dependency(depends=["test_mssql_sqlcmd_shell_query_command", "test_mssql_sqlcmd_shell_copy_to_stout", "test_mssql_ddl"])
@pytest.mark.parametrize(
    "seed_file",
    [
        "names_lf_lastrow_header.csv",
        "names_crlf_lastrow_header.csv",
        # BCP only supports unquited, last row ending files
    ]
)
def test_mssql_sqlcmd_shell_copy_from_stdin_csv_skipheader(mssql_sqlcmd_db, seed_file):
    # delete rows from table, make sure that the last matrix test does not mess up this test
    command = execute_sql_statement_command(mssql_sqlcmd_db, "DELETE FROM names_with_header")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0

    # reading csv file...
    names_csv_file_path = str((pathlib.Path(__file__).parent / f'../seed/{seed_file}').absolute())
    command = f'cat {names_csv_file_path} \\\n'
    command += '  | ' + shell.copy_from_stdin_command(mssql_sqlcmd_db,target_table='names_with_header',csv_format=True,skip_header=True,delimiter_char=',')
    print(command)

    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    print(pstdout)
    assert exitcode == 0

    # check if writing was successful

    command = execute_sql_statement_to_stdout_csv_command(mssql_sqlcmd_db, "SELECT COUNT(*) FROM names_with_header")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0
    assert pstdout == "10"

    command = execute_sql_statement_to_stdout_csv_command(mssql_sqlcmd_db, "SELECT name FROM names_with_header WHERE id = 1")
    (exitcode, pstdout) = subprocess.getstatusoutput(command)
    assert exitcode == 0
    assert pstdout == "Elinor Meklit"
