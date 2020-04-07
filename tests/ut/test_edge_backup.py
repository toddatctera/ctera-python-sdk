from unittest import mock

from cterasdk.edge import backup
from cterasdk.edge import taskmgr
from cterasdk.edge.enum import BackupConfStatusID
from cterasdk.common import Object
from tests.ut import base_edge


class TestEdgeBackup(base_edge.BaseEdgeTest):

    _task_attach_folder = 'attach_folder'
    _task_attach_encrypted_folder = 'attach_encrypted_folder'
    _task_create_folder = 'create_folder'
    _shared_secret = 'shared secret'
    _passphrase_salt = 'salt'

    def test_configure_attach_recoverable_encryption_no_backup_folder(self):
        self._init_filer()
        self._filer.get = mock.MagicMock(side_effect=TestEdgeBackup._mock_get_no_backup_settings)
        self._filer.execute = mock.MagicMock(side_effect=TestEdgeBackup._mock_execute)
        taskmgr.wait = mock.MagicMock(side_effect=TestEdgeBackup._mock_recoverable_encryption_attach_folder_not_found)
        backup.Backup(self._filer).configure()
        taskmgr.wait.assert_has_calls(
            [
                mock.call(self._filer, TestEdgeBackup._task_attach_folder),
                mock.call(self._filer, TestEdgeBackup._task_create_folder)
            ]
        )
        self._filer.execute.assert_has_calls(
            [
                mock.call('/status/services', 'attachFolder'),
                mock.call('/status/services', 'createFolder', mock.ANY)
            ]
        )
        expected_param = self._get_create_folder_param()
        actual_param = self._filer.execute.call_args_list[1][0][2]  # Access attachAndSave call param
        self._assert_equal_objects(actual_param, expected_param)
        self._filer.get.assert_has_calls(
            [
                mock.call('/config/backup'),
                mock.call('/defaults/BackupSettings')
            ]
        )
        self._filer.put.assert_called_once_with('/config/backup', mock.ANY)
        expected_param = self._get_default_backup_settings(backup.EncryptionMode.Recoverable,
                                                           TestEdgeBackup._shared_secret,
                                                           TestEdgeBackup._passphrase_salt)
        actual_param = self._filer.put.call_args[0][1]
        self._assert_equal_objects(actual_param, expected_param)

    @staticmethod
    def _mock_get_no_backup_settings(path):
        if path == '/config/backup':
            return None
        if path == '/defaults/BackupSettings':
            return TestEdgeBackup._get_default_backup_settings()
        return None

    @staticmethod
    def _get_default_backup_settings(encryption_mode=None, shared_secret=None, passphrase_salt=None):
        param = Object()
        param.encryptionMode = encryption_mode
        param.sharedSecret = shared_secret
        param.passPhraseSalt = passphrase_salt
        return param

    @staticmethod
    def _mock_execute(path, name, param=None):
        # pylint: disable=unused-argument
        if name == 'attachFolder':
            return TestEdgeBackup._task_attach_folder
        if name == 'attachEncryptedFolder':
            return TestEdgeBackup._task_attach_encrypted_folder
        if name == 'createFolder':
            return TestEdgeBackup._task_create_folder
        return None

    @staticmethod
    def _mock_recoverable_encryption_attach_folder_not_found(filer, task):
        # pylint: disable=unused-argument
        if task == TestEdgeBackup._task_attach_folder:
            return TestEdgeBackup._get_attach_response(backup.AttachRC.NotFound)
        if task == TestEdgeBackup._task_create_folder:
            return TestEdgeBackup._get_create_folder_response(backup.CreateFolderRC.OK,
                                                              TestEdgeBackup._shared_secret,
                                                              TestEdgeBackup._passphrase_salt)
        return None

    @staticmethod
    def _get_attach_response(rc, encryption_mode=None, shared_secret=None, passphrase_salt=None, encrypted_folder_key=None):
        task = Object()
        task.result = Object()
        task.result.attachFolderRC = rc
        if encryption_mode:
            task.result.encryptionMode = encryption_mode
        if shared_secret:
            task.result.sharedSecret = shared_secret
        if passphrase_salt:
            task.result.passPhraseSalt = passphrase_salt
        if encrypted_folder_key:
            task.result.encryptedFolderKey = encrypted_folder_key
        return task

    @staticmethod
    def _get_create_folder_response(rc, shared_secret=None, passphrase_salt=None):
        task = Object()
        task.result = Object()
        task.result.createFolderRC = rc
        if shared_secret:
            task.result.sharedSecret = shared_secret
        if passphrase_salt:
            task.result.passPhraseSalt = passphrase_salt
        return task

    @staticmethod
    def _get_create_folder_param(passphrase=None):
        param = Object()
        if passphrase:
            param.encryptionMode = backup.EncryptionMode.Secret
            param.sharedSecret = passphrase
        else:
            param.encryptionMode = backup.EncryptionMode.Recoverable
        return param

    def test_is_configured(self):
        self._init_filer(get_response=TestEdgeBackup._get_backup_status_response())
        backup.Backup(self._filer).is_configured()
        self._filer.get.assert_called_once_with('/proc/backup/backupStatus')

    @staticmethod
    def _get_backup_status_response():
        param = Object()
        param.serviceStatus = Object()
        param.serviceStatus.id = BackupConfStatusID.Attached
        return param

    def test_start_backup(self):
        self._init_filer()
        backup.Backup(self._filer).start()
        self._filer.execute.assert_called_once_with('/status/sync', 'start')

    def test_suspend_backup(self):
        self._init_filer()
        backup.Backup(self._filer).suspend()
        self._filer.execute.assert_called_once_with('/status/sync', 'pause')

    def test_unsuspend_backup(self):
        self._init_filer()
        backup.Backup(self._filer).unsuspend()
        self._filer.execute.assert_called_once_with('/status/sync', 'resume')
