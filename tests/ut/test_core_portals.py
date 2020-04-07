from unittest import mock

from cterasdk.common import Object
from cterasdk.core import portals
from tests.ut import base_core


class TestCorePortals(base_core.BaseCoreTest):

    _tenants_first_page = ['a', 'b', 'c', 'd']
    _tenants_second_page = ['e', 'f', 'g', 'h']

    def setUp(self):
        super().setUp()
        self._name = 'acme'
        self._display_name = 'Acme Corp.'
        self._billing_id = 'billing-id'
        self._company = 'The Acme Corporation'

    @staticmethod
    def _get_query_portals_response(execute_path, execute_name, execute_param):
        # pylint: disable=unused-argument
        query_response = Object()
        tenants = None
        if execute_param.startFrom == 0:
            query_response.hasMore = True
            tenants = TestCorePortals._tenants_first_page
        else:
            query_response.hasMore = False
            tenants = TestCorePortals._tenants_second_page
        query_response.objects = []
        for tenant in tenants:
            tenant_param = Object()
            tenant_param.name = tenant
            query_response.objects.append(tenant_param)
        return query_response

    def test_get_active_tenants(self):
        self._global_admin.execute = mock.MagicMock(side_effect=TestCorePortals._get_query_portals_response)
        tenant_objects = portals.Portals(self._global_admin).tenants()

        tenant_names = TestCorePortals._tenants_first_page + TestCorePortals._tenants_second_page
        counter = 0
        for tenant_object in tenant_objects:
            self.assertEqual(tenant_names[counter], tenant_object.name)
            counter = counter + 1

        self._global_admin.execute.assert_has_calls(
            [
                mock.call('', 'getPortalsDisplayInfo', mock.ANY),
                mock.call('', 'getPortalsDisplayInfo', mock.ANY)
            ]
        )

    def test_add_tenant_default_args(self):
        add_response = 'Success'
        self._init_global_admin(add_response=add_response)
        ret = portals.Portals(self._global_admin).add(self._name)
        self._global_admin.add.assert_called_once_with('/teamPortals', mock.ANY)
        expected_param = self._get_portal_param()
        actual_param = self._global_admin.add.call_args[0][1]
        self._assert_equal_objects(actual_param, expected_param)
        self.assertEqual(ret, add_response)

    def test_add_tenant_with_display_name_with_billing_id_with_company(self):
        add_response = 'Success'
        self._init_global_admin(add_response=add_response)
        ret = portals.Portals(self._global_admin).add(self._name, self._display_name, self._billing_id, self._company)
        self._global_admin.add.assert_called_once_with('/teamPortals', mock.ANY)
        expected_param = self._get_portal_param(self._display_name, self._billing_id, self._company)
        actual_param = self._global_admin.add.call_args[0][1]
        self._assert_equal_objects(actual_param, expected_param)
        self.assertEqual(ret, add_response)

    def test_delete_portal(self):
        execute_response = 'Success'
        self._init_global_admin(execute_response=execute_response)
        ret = portals.Portals(self._global_admin).delete(self._name)
        self._global_admin.execute.assert_called_once_with('/teamPortals/' + self._name, 'delete')
        self.assertEqual(ret, execute_response)

    def test_undelete_portal(self):
        execute_response = 'Success'
        self._init_global_admin(execute_response=execute_response)
        ret = portals.Portals(self._global_admin).undelete(self._name)
        self._global_admin.execute.assert_called_once_with('/teamPortals/' + self._name, 'moveFromTrashcan')
        self.assertEqual(ret, execute_response)

    def test_browse_tenant(self):
        self._init_global_admin()
        portals.Portals(self._global_admin).browse(self._name)
        self._global_admin.put.assert_called_once_with('/currentPortal', self._name)

    def test_browse_global_admin(self):
        self._init_global_admin()
        portals.Portals(self._global_admin).browse_global_admin()
        self._global_admin.put.assert_called_once_with('/currentPortal', '')

    def _get_portal_param(self, display_name=None, billing_id=None, company=None):
        param = Object()
        param._classname = 'TeamPortal'  # pylint: disable=protected-access
        param.name = self._name
        param.displayName = display_name
        param.externalPortalId = billing_id
        param.companyName = company
        return param
