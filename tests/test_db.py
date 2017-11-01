import json
import pytest
import pathlib
import sqlite3
import tempfile
import sys

from sqlalchemy import engine

from mara_app.app import MaraApp
from mara_app import monkey_patch
import mara_db

test_target = str(pathlib.Path(tempfile.mkdtemp()) / 'test_mara_db.db')
conn = sqlite3.connect(test_target)
conn.execute('CREATE TABLE table_one(column_one INTEGER, column_two TEXT)')
conn.execute("""CREATE TABLE table_two(
column_X INTEGER,
column_Y TEXT,
FOREIGN KEY(column_X) REFERENCES table_one(column_one)
)""")

conn.close()

print('DATABASE:', test_target, file=sys.stderr)

@monkey_patch.patch(mara_db.config.databases, 'Replace the default database with a mockup')
def wrapper():
    return {'test_db': engine.create_engine(f'sqlite+pysqlite:////{test_target}')}

class TestApp:
    @pytest.fixture(autouse=True)
    def set_up(self):
        app = MaraApp()
        self.app = app.test_client()

    def test_test_db_page_exists(self):
        response = self.app.get("/db/test_db")
        assert response.status_code == 200

    def test_random_db_page_exists(self):
        response = self.app.get("/db/unexistent")
        print(response.data, file=sys.stderr)
        assert response.status_code == 404

    def test_test_db_content(self):
        response = self.app.get("/db/svg/test_db/main")
        assert response.status_code == 200
        chart = json.loads(response.get_data(as_text=True))
        assert 'relationships' in chart
        assert len(chart['relationships']) == 1
        assert len(chart['relationships'][0]) == 2
        # FK relationship from table two to table one
        assert 'table_two' in chart['relationships'][0][0]
        assert 'table_one' in chart['relationships'][0][1]

        assert 'tables' in chart
        assert len(chart['tables']) == 2
        for name, columns in chart['tables'].items():
            if 'table_one' in name:
                assert set(columns) == set(['column_one', 'column_two'])
            else:
                assert set(columns) == set(['column_X', 'column_Y'])

if __name__ == "__main__":
    pytest.main()
