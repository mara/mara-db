"""Helper functions to generate commands for testings"""
import shlex

from mara_db import shell


def execute_sql_statement_command(db, sql_statement):
    command = f'echo {shlex.quote(sql_statement)} \\\n'
    command += '  | ' + shell.query_command(db)
    assert command
    print(command)
    return command

def execute_sql_file_command(db, file_path):
    command = f'cat {file_path} \\\n'
    command += '  | ' + shell.query_command(db)
    assert command
    print(command)
    return command

def execute_sql_statement_to_stdout_csv_command(db, sql_statement):
    command = f'echo {shlex.quote(sql_statement)} \\\n'
    command += '  | ' + shell.copy_to_stdout_command(db, delimiter_char=',')
    assert command
    print(command)
    return command
