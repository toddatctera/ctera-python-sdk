import logging

from .enum import Mode
from .types import TCPConnectResult
from ..lib.task_manager_base import TaskError
from . import taskmgr as TaskManager
from ..common import Object
from .base_command import BaseCommand


class Network(BaseCommand):
    """ Gateway Network configuration APIs """

    def get_status(self):
        """
        Retrieve the network interface status
        """
        return self._gateway.get('/status/network/ports/0')

    def ifconfig(self):
        """
        Retrieve the ip configuration
        """
        return self.ipconfig()

    def ipconfig(self):
        """
        Retrieve the ip configuration
        """
        return self._gateway.get('/config/network/ports/0')

    def set_static_ipaddr(self, address, subnet, gateway, primary_dns_server, secondary_dns_server=None):
        """
        Set a Static IP Address

        :param str address: The static address
        :param str subnet: The subnet for the static address
        :param str gateway: The default gateway
        :param str primary_dns_server: The primary DNS server
        :param str,optinal secondary_dns_server: The secondary DNS server, defaults to None
        """
        ip = self._gateway.get('/config/network/ports/0/ip')
        ip.DHCPMode = Mode.Disabled
        ip.address = address
        ip.netmask = subnet
        ip.gateway = gateway
        ip.autoObtainDNS = False
        ip.DNSServer1 = primary_dns_server

        if secondary_dns_server is not None:
            ip.DNSServer2 = secondary_dns_server

        logging.getLogger().info('Configuring a static ip address.')

        self._gateway.put('/config/network/ports/0/ip', ip)

        logging.getLogger().info(
            'Network settings updated. %s',
            {'address': address, 'subnet': subnet, 'gateway': gateway, 'DNS1': primary_dns_server, 'DNS2': secondary_dns_server}
        )

    def set_static_nameserver(self, primary_dns_server, secondary_dns_server=None):
        """
        Set the DNS Server addresses statically

        :param str primary_dns_server: The primary DNS server
        :param str,optinal secondary_dns_server: The secondary DNS server, defaults to None
        """
        ip = self._gateway.get('/config/network/ports/0/ip')
        ip.autoObtainDNS = False
        ip.DNSServer1 = primary_dns_server

        if secondary_dns_server is not None:
            ip.DNSServer2 = secondary_dns_server

        logging.getLogger().info('Configuring nameserver settings.')

        self._gateway.put('/config/network/ports/0/ip', ip)

        logging.getLogger().info('Nameserver settings updated. %s', {'DNS1': primary_dns_server, 'DNS2': secondary_dns_server})

    def enable_dhcp(self):
        """
        Enable DHCP
        """
        ip = self._gateway.get('/config/network/ports/0/ip')
        ip.DHCPMode = Mode.Enabled
        ip.autoObtainDNS = True

        logging.getLogger().info('Enabling DHCP.')

        self._gateway.put('/config/network/ports/0/ip', ip)

        logging.getLogger().info('Network settings updated. Enabled DHCP.')

    def diagnose(self, services):
        """
        Test a TCP connection to a host over a designated port

        :param list[cterasdk.edge.types.TCPService] services: List of services, identified by a host and a port
        :returns: A list of named-tuples including the host, port and a boolean value indicating whether TCP connection can be established
        :rtype: list[cterasdk.edge.types.TCPConnectResult]
        """
        return [self.tcp_connect(service) for service in services]

    def tcp_connect(self, service):
        """
        Test a TCP connection between the Gateway and the provided host address

        :param cterasdk.edge.types.TCPService service: A service, identified by a host and a port
        :returns: A named-tuple including the host, port and a boolean value indicating whether TCP connection can be established
        :rtype: cterasdk.edge.types.TCPConnectResult
        """
        param = Object()
        param.address = service.host
        param.port = service.port

        logging.getLogger().info("Testing connection. %s", {'host': service.host, 'port': service.port})

        task = self._gateway.execute("/status/network", "tcpconnect", param)
        try:
            task = TaskManager.wait(self._gateway, task)
            logging.getLogger().debug("Obtained connection status. %s", {'status': task.result.rc})
            if task.result.rc == "Open":
                return TCPConnectResult(service.host, service.port, True)
        except TaskError:
            pass

        logging.getLogger().warning("Couldn't establish TCP connection. %s", {'address': service.host, 'port': service.port})

        return TCPConnectResult(service.host, service.port, False)
