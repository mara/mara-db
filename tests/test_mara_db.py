
import unittest

from mara_app.app import MaraApp

# Mara mount every object which is a blueprint, so these imports are not pointless

import mara_db
from mara_db import views


app = MaraApp(__name__)


class BluePrintTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_health(self):
        rv = self.app.get('/db/dwh_real_etl/os_dim')
        print(rv)


if __name__ == '__main__':
    unittest.main()

