from unittest.mock import patch
from django.core.management import call_command
from django.db.utils import OperationalError


class TestCommands:

    def test_wait_for_db_ready(self):
        """Test waiting for db when db is avilable"""
        with patch('django.db.utils.ConnectionHandler.__getitem__') as gi:
            gi.return_value = True
            call_command('wait_for_db')
            gi.assert_called_once()

    @patch('time.sleep', return_value=None)
    def test_wait_for_db(self, ts):
        """Test waiting for db"""
        with patch('django.db.utils.ConnectionHandler.__getitem__') as gi:
            gi.side_effect = [OperationalError] * 5 + [True]
            call_command('wait_for_db')
            assert gi.call_count == 6
