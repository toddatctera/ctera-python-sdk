from cterasdk.edge import config
from tests.ut import base_edge


class TestEdgeConfig(base_edge.BaseEdgeTest):

    def setUp(self):
        super().setUp()
        self._hostname = 'vGateway-01dc'
        self._location = '205 E. 42nd St. New York, NY. 10017'

    def test_get_hostname(self):
        self._init_filer(get_response=self._hostname)
        ret = config.Config(self._filer).get_hostname()
        self._filer.get.assert_called_once_with('/config/device/hostname')
        self.assertEqual(ret, self._hostname)

    def test_set_hostname(self):
        self._init_filer(put_response=self._hostname)
        ret = config.Config(self._filer).set_hostname(self._hostname)
        self._filer.put.assert_called_once_with('/config/device/hostname', self._hostname)
        self.assertEqual(ret, self._hostname)

    def test_get_location(self):
        self._init_filer(get_response=self._location)
        ret = config.Config(self._filer).get_location()
        self._filer.get.assert_called_once_with('/config/device/location')
        self.assertEqual(ret, self._location)

    def test_set_location(self):
        self._init_filer(put_response=self._location)
        ret = config.Config(self._filer).set_location(self._location)
        self._filer.put.assert_called_once_with('/config/device/location', self._location)
        self.assertEqual(ret, self._location)

    def test_is_wizard_enabled(self):
        get_response = True
        self._init_filer(get_response=get_response)
        ret = config.Config(self._filer).is_wizard_enabled()
        self._filer.get.assert_called_once_with('/config/gui/openFirstTimeWizard')
        self.assertEqual(ret, get_response)

    def test_enable_first_time_wizard(self):
        put_response = 'Success'
        self._init_filer(put_response=put_response)
        ret = config.Config(self._filer).enable_wizard()
        self._filer.put.assert_called_once_with('/config/gui/openFirstTimeWizard', True)
        self.assertEqual(ret, put_response)

    def test_disable_first_time_wizard(self):
        put_response = 'Success'
        self._init_filer(put_response=put_response)
        ret = config.Config(self._filer).disable_wizard()
        self._filer.put.assert_called_once_with('/config/gui/openFirstTimeWizard', False)
        self.assertEqual(ret, put_response)
