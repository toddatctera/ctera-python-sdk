import copy
import logging
import re

from . import query
from ..common import Object
from ..exception import CTERAException


class Zones:

    def __init__(self, Portal):
        self._CTERAHost = Portal

    def get(self, name):
        return get(self._CTERAHost, name)

    def add(self, name, policy_type='Select', description=None):
        return add(self._CTERAHost, name, policy_type, description)

    def delete(self, name):
        return delete(self._CTERAHost, name)

    def add_devices(self, name, devices):
        return add_devices(self._CTERAHost, name, devices)

    def add_folders(self, name, tuples):
        return add_folders(self._CTERAHost, name, tuples)


def get(CTERAHost, name):
    query_filter = query.FilterBuilder('name').eq(name)
    param = query.QueryParamBuilder().include_classname().startFrom(0).countLimit(1).addFilter(query_filter).orFilter(False).build()

    logging.getLogger().info('Retrieving zone. %s', {'name' : name})

    response = CTERAHost.execute('', 'getZonesDisplayInfo', param)

    objects = response.objects
    if len(objects) < 1:
        logging.getLogger().error('Zone not found. %s', {'name' : name})
        raise CTERAException('Zone not found', None, name=name)

    zone = objects[0]

    logging.getLogger().info('Zone found. %s', {'name' : name, 'id' : zone.zoneId})

    return zone


def zone_info(CTERAHost, zid):
    logging.getLogger().debug('Obtaining zone info. %s', {'id' : zid})

    response = CTERAHost.execute('', 'getZoneBasicInfo', zid)

    logging.getLogger().debug('Obtained zone info. %s', {'id' : zid})

    return response


def add_devices(CTERAHost, zone_name, device_names):
    zone = get(CTERAHost, zone_name)
    devices = CTERAHost.devices_by_name(include=['uid'], names=device_names)
    info = zone_info(CTERAHost, zone.zoneId)
    description = (info.description if hasattr(info, 'description') else None)

    param = zone_param(info.name, info.policyType, description, info.zoneId)
    for device in devices:
        param.delta.devicesDelta.added.append(device.uid)

    logging.getLogger().info('Adding devices to zone. %s', {'zone' : info.name})

    try:
        save(CTERAHost, param)
    except CTERAException as error:
        logging.getLogger().error('Failed adding devices to zone.')
        raise error


def add_folders(CTERAHost, zone_name, tuples):
    zone = get(CTERAHost, zone_name)
    folders = find_folders(CTERAHost, tuples)
    info = zone_info(CTERAHost, zone.zoneId)
    description = info.description if hasattr(info, 'description') else None
    param = zone_param(info.name, info.policyType, description, info.zoneId)
    param.delta.policyDelta = []

    for owner_id, folder_ids in folders.items():
        policyDelta = Object()
        policyDelta._classname = 'ZonePolicyDelta'  # pylint: disable=protected-access
        policyDelta.userUid = owner_id
        policyDelta.foldersDelta = Object()
        policyDelta.foldersDelta._classname = 'ZoneFolderDelta'  # pylint: disable=protected-access
        policyDelta.foldersDelta.added = copy.deepcopy(folder_ids)
        policyDelta.foldersDelta.removed = []

        param.delta.policyDelta.append(policyDelta)

    try:
        save(CTERAHost, param)
    except CTERAException as error:
        logging.getLogger().error('Failed adding folders to zone.')
        raise error


def find_folders(CTERAHost, tuples):
    cloudfs = CTERAHost.cloudfs()

    folders = {}
    for name, owner in tuples:
        cloud_folder = cloudfs.find(name, owner, include=['uid', 'owner'])
        folder_id = cloud_folder.uid
        owner_id = re.search("[1-9][0-9]*", cloud_folder.owner).group(0)

        if folders.get(owner_id) is None:
            folders[owner_id] = [folder_id]
        else:
            folders.get(owner_id).append(folder_id)

    return folders


def save(CTERAHost, param):
    zone_name = param.basicInfo.name

    logging.getLogger().debug('Applying changes to zone. %s', {'zone' : param.basicInfo.name})

    response = CTERAHost.execute('', 'saveZone', param)
    try:
        process_response(response)
    except CTERAException as error:
        logging.getLogger().error('Failed applying changes to zone. %s', {'zone' : zone_name, 'rc' : response.rc})
        raise error

    logging.getLogger().debug('Zone changes applied successfully. %s', {'zone' : zone_name})


def add(CTERAHost, name, policy_type, description):
    policy_type = {
        'All' : 'allFolders',
        'Select' : 'selectedFolders',
        'None' : 'noFolders'
    }.get(policy_type)

    param = zone_param(name, policy_type, description)

    logging.getLogger().info('Adding zone. %s', {'name' : name})

    response = CTERAHost.execute('', 'addZone', param)
    try:
        process_response(response)
    except CTERAException as error:
        logging.getLogger().error('Zone creation failed. %s', {'rc' : response.rc})
        raise error

    logging.getLogger().info('Zone added. %s', {'name' : name})


def process_response(response):
    if response.rc != 'OK':
        raise CTERAException('Zone creation failed', response)


def zone_param(name, policy_type, description=None, zid=None):
    param = Object()
    param._classname = "SaveZoneParam"  # pylint: disable=protected-access
    param.basicInfo = Object()
    param.basicInfo._classname = 'ZoneBasicInfo'  # pylint: disable=protected-access
    param.basicInfo.name = name
    param.basicInfo.policyType = policy_type
    param.basicInfo.description = description
    param.basicInfo.zoneId = zid
    param.delta = Object()
    param.delta._classname = 'ZoneDelta'  # pylint: disable=protected-access
    param.delta.devicesDelta = Object()
    param.delta.devicesDelta._classname = 'ZoneDeviceDelta'  # pylint: disable=protected-access
    param.delta.devicesDelta.added = []
    param.delta.devicesDelta.removed = []

    return param


def delete(CTERAHost, name):
    zone = get(CTERAHost, name)

    logging.getLogger().info('Deleting zone. %s', {'zone' : name})

    response = CTERAHost.execute('', 'deleteZones', [zone.zoneId])
    if response == 'ok':
        logging.getLogger().info('Zone deleted. %s', {'zone' : name})
