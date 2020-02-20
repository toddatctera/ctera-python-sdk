import logging

from .enum import Mode


def disable(ctera_host):

    logging.getLogger().info('Disabling NFS server.')

    ctera_host.put('/config/fileservices/nfs/mode', Mode.Disabled)

    logging.getLogger().info('NFS server disabled.')
