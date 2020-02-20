import logging

from .enum import Mode


def disable(ctera_host):
    logging.getLogger().info('Disabling RSync server.')
    ctera_host.put('/config/fileservices/rsync/server', Mode.Disabled)
    logging.getLogger().info('RSync server disabled.')
