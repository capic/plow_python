# !/usr/bin/env python3.2
from service import actionResource

__author__ = 'Vincent'

import io
import sys
import logging
import os
import subprocess
import time
from datetime import datetime, timedelta
import requests
import utils
import log
import config
from bean.downloadBean import Download
from bean.actionBean import Action
from bean.downloadPackageBean import DownloadPackage
from bean.downloadDirectoryBean import DownloadDirectory
from bean.downloadHostBean import DownloadHost

from service.downloadResource import DownloadResource
from service.actionResource import ActionResource
from service.hostResource import HostResource
from service.packageResource import PackageResource
from service.applicationConfigurationResource import ApplicationConfigurationResource
from service.logResource import LogResource
from service.directoryResource import DirectoryResource

# demarrer le programme en utilisant PYTHONIOENCODING='utf8' python3.2


class ManageDownload:

    COMMAND_DOWNLOAD = "/usr/bin/plowdown -r 10 -x --9kweu=I1QOR00P692PN4Q4669U --temp-rename --temp-directory %s -o %s %s"
    COMMAND_DOWNLOAD_INFOS = "/usr/bin/plowprobe --printf '==>%%f=$=%%s=$=%%m' %s"
    COMMAND_UNRAR = "cd \"%s\" && unrar x -o+ \"%s\""
    MARK_AS_FINISHED = "# FINNISHED "
    MARK_AS_ERROR = "# ERROR"

    # def __init__(self):
    # unirest.timeout(config.DEFAULT_UNIREST_TIMEOUT)
    # self.action_update_in_progress = False

    @staticmethod
    def get_download_by_id(download_id):
        return DownloadResource.get(download_id)

    @staticmethod
    def insert_download(download):
        if download is not None:
            download_package = None

            try:
                # host
                download.host = HostResource.insert(download.host)

                # package
                if utils.package_name_from_download_name(download.name) is not None:
                    download_package = DownloadPackage()
                    download_package.name = utils.package_name_from_download_name(download.name)
                    download_package = PackageResource.insert(download_package)

                download.package = download_package

                download.lifecycle_insert_date = datetime.utcnow().isoformat()
                download.lifecycle_update_date = datetime.utcnow().isoformat()
                download.theorical_start_datetime = datetime.utcnow().isoformat()

                download = DownloadResource.insert(download)

            except Exception:
                import traceback

                log.log(__name__, sys._getframe().f_code.co_name, "Insert download: No database connection => %s" %
                        traceback.format_exc().splitlines()[-1], log.LEVEL_ERROR)
                log.log(__name__, sys._getframe().f_code.co_name, "Traceback: %s" % traceback.format_exc(), log.LEVEL_DEBUG)
        else:
            logging.error(__name__, sys._getframe().f_code.co_name, "Download is none")

        return download

    @staticmethod
    def update_download(download_to_update, to_update_in_database=True, force_update_log=False):
        try:
            DownloadResource.update(download_to_update, to_update_in_database)

        except Exception:
            import traceback

            log.log(__name__, traceback.format_exc().splitlines()[-1], 'Unrar finised but error', log.LEVEL_ALERT, True, download)

    @staticmethod
    def get_application_configuration_by_id(application_configuration_id, download=None):
        return ApplicationConfigurationResource.get(application_configuration_id, download)

    # @staticmethod
    # def update_download_log(download):
    #     log.log(__name__, sys._getframe().f_code.co_name, "+++++++", log.LEVEL_INFO)
    #     return LogResource.insert(download)

    def update_action_callback(self, response):
        log.log(__name__, sys._getframe().f_code.co_name, '*** update_action_callback ***', log.LEVEL_INFO)
        # self.action_update_in_progress = False

    def update_action(self, action):
        log.log(__name__, sys._getframe().f_code.co_name, '*** update_action ***', log.LEVEL_INFO)

        self.action_update_in_progress = True

        action_updated = ActionResource.update(action)

    @staticmethod
    def get_package_by_id(self, package_id):
        return PackageResource.get(package_id)

    @staticmethod
    def get_download_directory_by_id(directory_id):
        return DirectoryResource.get(directory_id)

    @staticmethod
    def get_actions_by_parameters(download_id=None, action_type_id=None):
        params = {}
        if download_id is not None:
            params['download_id'] = download_id
        if action_type_id is not None:
            params['action_type_id'] = action_type_id

        return ActionResource.get_all_by_params(params)

    @staticmethod
    def get_action_by_id(action_id):
        return ActionResource.get(action_id)

    @staticmethod
    def get_download_by_link_file_path(link, file_path):
        download = None

        if link is not None and link != '' and file_path is not None and file_path != '':
            params = {"link": link, "file_path": file_path}

            downloads_list = DownloadResource.get_all_by_params(params)

            if downloads_list is not None:
                if len(downloads_list) == 0:
                    log.log(__name__, sys._getframe().f_code.co_name,
                        'No download found with link %s and file_path %s' % (
                            link, file_path), log.LEVEL_INFO)
                elif len(downloads_list) == 1:
                    download = downloads_list[0]
                    log.log(__name__, sys._getframe().f_code.co_name, 'download : %s' % (download.to_string()),
                            log.LEVEL_DEBUG)
                else:
                    download = downloads_list[0]
                    log.log(__name__, sys._getframe().f_code.co_name,
                        'Too many download found with link %s and file_path %s' % (
                            link, file_path),
                        log.LEVEL_ERROR)

        return download

    @staticmethod
    def get_downloads_by_package(package_id):
        params = {"package_id": package_id}
        return DownloadResource.get_all_by_params(params)

    @staticmethod
    def get_all_downloads_to_start():
        return DownloadResource.get_next_downloads()

    @staticmethod
    def get_download_to_start(download_id, file_path=None):
        download = None

        if download_id is None:
            already_downloaded = True

            while already_downloaded is True:
                already_downloaded = False
                try:
                    params = None
                    if file_path is not None:
                        params = {"file_path": file_path}

                    download = DownloadResource.get_next(params)

                    if download is not None:
                        if '# %s \r\n%s %s' % (download.name, ManageDownload.MARK_AS_FINISHED, download.link) in open(download.file_path).read():
                            log.log(__name__, sys._getframe().f_code.co_name, 'Download got already downloaded in file => update to finish in database', log.LEVEL_INFO, True, download)
                            download.status = Download.STATUS_FINISHED
                            download.size_file_downloaded = download.size_file
                            ManageDownload.update_download(download, True)
                            already_downloaded = True

                    config.RESCUE_MODE = False
                except Exception:
                    import traceback

                    log.log(__name__, sys._getframe().f_code.co_name, traceback.format_exc().splitlines()[-1], log.LEVEL_ALERT, True, download)
                    log.log(__name__, sys._getframe().f_code.co_name, "Traceback: %s" % traceback.format_exc(), log.LEVEL_Alert, True, download)

                    file = open(file_path, 'r', encoding='utf-8')
                    for line in file:
                        # line = line.decode("utf-8")
                        if 'http' in line:
                            log.log(__name__, sys._getframe().f_code.co_name, 'Line %s contains http' % line, log.LEVEL_DEBUG)
                            if not line.startswith('#'):
                                line = line.replace('\n', '')
                                line = line.replace('\r', '')
                                download = Download()
                                download.link = line
                                download.name = "UNKNOWN"
                                download.file_path = file_path
                                break

                    file.close()
                    config.RESCUE_MODE = True
                    log.log(__name__, sys._getframe().f_code.co_name, '===== Rescue Mode Activated =====', log.LEVEL_INFO)
        else:
            download = ManageDownload.get_download_by_id(download_id)

        return download

    @staticmethod
    def get_downloads_in_progress():
        params = {"status": Download.STATUS_IN_PROGRESS}
        return DownloadResource.get_all_by_params(params)

    @staticmethod
    def download_already_exists(link):
        # on considere apr defaut que le download existe pour eviter de telecharger si jamais on a pas acces ?
        exists = True

        if link is not None and link != '':
            params = {"link": link}
            download_list = DownloadResource.get_all_by_params(params)

            if download_list is not None:
                exists = len(download_list) > 0
                log.log(__name__, sys._getframe().f_code.co_name, 'download exists ? %s' % str(exists),
                        log.LEVEL_DEBUG)
        else:
            logging.error('[ManageDownload](download_already_exists) | Link is none')

        return exists

    @staticmethod
    def insert_update_download(link, file_path):
        download = None
        # si la ligne n'est pas marque comme termine avec ce programme
        if not link.startswith(ManageDownload.MARK_AS_FINISHED):
            if not link.startswith(ManageDownload.MARK_AS_ERROR):
                link = link.replace('\n', '')
                link = link.replace('\r', '')

                finished = False
                # si la ligne est marque comme termine par le traitement par liste de plowdown
                if link.startswith('#OK'):
                    finished = True
                    link = link.replace('#OK ', '')

                cmd = (ManageDownload.COMMAND_DOWNLOAD_INFOS % link)
                # exists = self.download_already_exists(link)
                download = ManageDownload.get_download_by_link_file_path(link, file_path)
                # on n'insere pas un lien qui existe deja ou qui est termine
                if config.RESCUE_MODE is False and download is None:
                    log.log(__name__, sys._getframe().f_code.co_name, 'Download finished ? %s' % (str(finished)),
                            log.LEVEL_DEBUG)
                    if not finished:
                        log.log(__name__, sys._getframe().f_code.co_name,
                            'Download %s doesn''t exist -> insert' % link,
                            log.LEVEL_DEBUG)

                        name, size, host = utils.get_infos_plowprobe(cmd)
                        if name is not None:
                            download_host = DownloadHost()
                            download_host.name = host

                            download_directory = DownloadDirectory()
                            download_directory.id = config.application_configuration.python_directory_download.id
                            download_directory.path = config.application_configuration.python_directory_download.path

                            download = Download()
                            download.name = name
                            download.host = download_host
                            download.link = link
                            download.size = size
                            download.status = Download.STATUS_WAITING
                            download.priority = Download.PRIORITY_NORMAL
                            download.file_path = file_path
                            download.directory = download_directory
                            download.application_configuration_id = config.application_configuration.id_application
                            download.lifecycle_insert_date = datetime.utcnow().isoformat()

                            ManageDownload.insert_download(download)
        # lien marqie comme termine dans le fihier
        else:
            link = link.replace('\n', '')
            link = link.replace('\r', '')
            link = link.replace(ManageDownload.MARK_AS_FINISHED + ' ', '')
            log.log(__name__, sys._getframe().f_code.co_name, 'Download already marked as finished in file',
                    log.LEVEL_INFO)
            download = ManageDownload.get_download_by_link_file_path(link, file_path)
            if download is not None:
                if download.status != Download.STATUS_FINISHED:
                    log.log(__name__, sys._getframe().f_code.co_name, 'Download status is not finised => To update',
                            log.LEVEL_DEBUG)

                    if download.name is None or download.name == '':
                        cmd = (ManageDownload.COMMAND_DOWNLOAD_INFOS % link)
                        download.name, download.size = utils.get_infos_plowprobe(cmd)
                        to_update = True

                    action_bool = False
                    # si on a des actions en cours ou des termines on ne change pas le statut
                    actions_list = ManageDownload.get_actions_by_parameters(download.id)
                    for action in actions_list:
                        if action.status != Action.STATUS_WAITING:
                            action_bool = True
                            break

                    if not action_bool:
                        download.status = Download.STATUS_FINISHED
                        download.progress_file = 100
                        to_update = True

                    if to_update:
                        download.logs = 'updated by insert_update_download method\r\n'
                        ManageDownload.update_download(download, True)

        return download

    @staticmethod
    def stop_download(download):
        utils.kill_proc_tree(download.pid_python)
        utils.kill_proc_tree(download.pid_plowdown)

        download.pid_python = 0
        download.pid_plowdown = 0
        download.status = Download.STATUS_WAITING
        download.logs = 'updated by stop_download method\r\n'
        ManageDownload.update_download(download, True)

    @staticmethod
    def start_download(download):
        cmd = (
            ManageDownload.COMMAND_DOWNLOAD % (
                config.application_configuration.python_directory_download_temp.path, config.application_configuration.python_directory_download.path, download.link))
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        download.pid_plowdown = p.pid
        download.pid_python = os.getpid()
        download.status = Download.STATUS_IN_PROGRESS
        log.log(__name__, sys._getframe().f_code.co_name, 'Updated by start_download method', log.LEVEL_DEBUG, True, download)
        if config.RESCUE_MODE is False:
            ManageDownload.update_download(download, True)

        line = ''
        reader = io.TextIOWrapper(p.stdout, encoding='utf8')
        while True:
            try:
                out = reader.read(1)
                if out == '' and p.poll() is not None:
                    break
                if out != '':
                    if out != '\n' and out != '\r':
                        line += out
                    else:
                        line = utils.clean_plowdown_line(line)
                        download = ManageDownload.get_download_values(line, download)
                        line = ''
            except:
                import traceback

                log.log(__name__, sys._getframe().f_code.co_name, "Error during console reading => %s" % traceback.format_exc().splitlines()[-1], log.LEVEL_ALERT, True, download)
                log.log(__name__, sys._getframe().f_code.co_name, "Traceback: %s" % traceback.format_exc(), log.LEVEL_ALERT, True, download)

                ManageDownload.update_download(download)
                break
        return download

    # 0 => pourcentage, 1 => taille totale, 2 => pourcentage recu, 3 => taille recu, 4 pourcentage transfere, 5 => taille transfere,
    # 6 => vitesse moyenne recu, 7 => vitesse moyenne envoye, 8 => temps total, 9 => temps passe, 10 => temps restant, 11 => vitesse courante
    @staticmethod
    def get_download_values(values_line, download):
        download_log = ''

        log.log(__name__, sys._getframe().f_code.co_name, values_line, log.LEVEL_DEBUG)
        values = values_line.split()

        if len(values) > 0:
            to_update_in_database = True
            if values[0].isdigit():
                # progress part
                download.progress_part = int(values[2])

                if download.size_file is None or download.size_file == 0:
                    # size file
                    download.size_file = utils.compute_size(values[1])

                # size part
                download.size_part = utils.compute_size(values[1])

                # size part downloaded
                download.size_part_downloaded = utils.compute_size(values[3])
                # size file downloaded
                download_size_file_downloaded = download.size_part_downloaded
                if download.size_file > 0:
                    download_size_file_downloaded = (
                                                        download.size_file - download.size_part) + download.size_part_downloaded
                download.size_file_downloaded = download_size_file_downloaded

                # average speed
                download.average_speed = utils.compute_size(values[6])

                # current speed
                download.current_speed = utils.compute_size(values[11])

                if '-' not in values[9]:
                    # time spent
                    download.time_spent = utils.hms_to_seconds(values[9])

                if '-' not in values[10]:
                    # time left
                    download.time_left = utils.hms_to_seconds(values[10])

                to_update_in_database = False

                if values[1] == values[3] and values[1] != '0' and download.status == Download.STATUS_IN_PROGRESS:
                    download.status = Download.STATUS_FINISHED
                    download.time_left = 0
                    download.current_speed = 0
                    directory = DownloadDirectory()
                    directory.id = config.application_configuration.python_directory_download.id
                    directory.path = config.application_configuration.python_directory_download.path
                    download.directory = directory
                    download.to_move_directory = None
                    to_update_in_database = True

            elif "Filename" in values[0]:
                tab_name = values_line.split('Filename:')
                download.name = utils.clean_string_console(tab_name[len(tab_name) - 1])
            elif "Waiting" in values[0]:
                download.theorical_start_datetime = (datetime.utcnow() + timedelta(0, int(values[1]))).isoformat()
                # log.log(__name__, sys._getframe().f_code.co_name, 'Theorical start date time %s' % time.strftime('%y/%m/%d %H:%M:%S', download.theorical_start_datetime), log.LEVEL_INFO, True, download)
            elif "Link" in values[0] and "is" in values[1] and "not" in values[2] and "alive" in values[3]:
                download_log += 'Link is not alive'
                download.status = Download.STATUS_ERROR

            log.log(__name__, sys._getframe().f_code.co_name, time.strftime('%d/%m/%y %H:%M:%S', time.localtime()) + ': ' + values_line, log.LEVEL_INFO, True, download)

            # si on est pas en rescue mode
            if config.RESCUE_MODE is False:
                try:
                    ManageDownload.update_download(download, to_update_in_database)
                except Exception:
                    if download.status == Download.STATUS_FINISHED:
                        config.RESCUE_MODE = True

        return download

    @staticmethod
    def check_download_alive(download):
        if not utils.check_pid(download.pid_plowdown):
            # utils.kill_proc_tree(download.pid_python)
            log.log(__name__, sys._getframe().f_code.co_name,
                'Process %s for download %s killed for inactivity ...\r\n' % (
                    str(download.pid_python), download.name), log.LEVEL_DEBUG)

            download.pid_plowdown = 0
            download.pid_python = 0
            download.status = Download.STATUS_WAITING
            download.time_left = 0
            download.average_speed = 0
            download.logs = 'updated by check_download_alive_method\r\nProcess killed by inactivity ...\r\n'

            ManageDownload.update_download(download, True)

    @staticmethod
    def move_file(download_id, action):
        if action is not None:
            download = ManageDownload.get_download_by_id(download_id)

            if download is not None:
                action_directory_src = utils.find_element_by_attribute_in_object_array(action.properties, 'property_id',
                                                                                       Action.PROPERTY_DIRECTORY_SRC)
                src_file_path = os.path.join(action_directory_src.directory.path, download.name)
                action_directory_dst = utils.find_element_by_attribute_in_object_array(action.properties, 'property_id',
                                                                                       Action.PROPERTY_DIRECTORY_DST)
                dst_file_path = os.path.join(action_directory_dst.directory.path, download.name)

                if action_directory_src.directory.id != action_directory_dst.directory.id:
                    if os.path.isfile(src_file_path):
                        download.status = Download.STATUS_MOVING
                        download.logs = 'File %s exists\r\n' % src_file_path
                        download.logs += 'Moving from %s to %s => status %s\r\n' % (
                            src_file_path, dst_file_path, download.status)
                        ManageDownload.update_download(download, True)

                        try:
                            utils.copy_large_file(src_file_path, dst_file_path, action, Action.STATUS_IN_PROGRESS,
                                                  ManageDownload.treatment_update_action)

                            ManageDownload.action_update_in_progress = False
                            ManageDownload.treatment_update_action(action, Action.STATUS_FINISHED, 100, 0, None)
                            download.status = Download.STATUS_MOVED
                            download.directory = action_directory_dst.directory
                            download.logs = 'File moved to %s => status %s\r\n' % (
                                download.directory.path, download.status)
                            ManageDownload.update_download(download, True)
                        except Exception:
                            import traceback

                            log.log(__name__, sys._getframe().f_code.co_name, traceback.format_exc(), log.LEVEL_ERROR)
                            download.status = Download.STATUS_ERROR_MOVING
                            download.logs = 'File moved to %s => status %s\r\n' % (
                                download.directory.path, download.status)
                            ManageDownload.update_download(download, True, force_update_log=True)
                    else:
                        log.log(__name__, 'move_file', 'File %s does not exist' % src_file_path, log.LEVEL_ERROR, True, download)
                else:
                    log.log(__name__, sys._getframe().f_code.co_name, 'Sames source and destination directories', log.LEVEL_ERROR)
            else:
                log.log(__name__, sys._getframe().f_code.co_name, 'Download is none', log.LEVEL_ERROR)
        else:
            log.log(__name__, sys._getframe().f_code.co_name, ' Action is none', log.LEVEL_ERROR)

    @staticmethod
    def treatment_update_action(action, status, percent, time_left, time_elapsed):
        action_returned = None
        if not ManageDownload.action_update_in_progress:
            if percent is not None:
                utils.change_action_property(action, 'property_id', Action.PROPERTY_PERCENTAGE, 'property_value',
                                             percent)

            if time_left is not None:
                utils.change_action_property(action, 'property_id', Action.PROPERTY_TIME_LEFT, 'property_value',
                                             time_left)

            if time_elapsed is not None:
                utils.change_action_property(action, 'property_id', Action.PROPERTY_TIME_ELAPSED, 'property_value',
                                             time_elapsed)

            if status is not None:
                action.action_status_id = status

            ManageDownload.update_action(action)

        return action_returned

    @staticmethod
    def unrar(object_id, action):
        downloads_list = ManageDownload.get_downloads_by_package(object_id)
        if downloads_list is not None and len(downloads_list) > 0:
            def getKey(d):
                return d.name

            downloads_list = sorted(downloads_list, key=getKey)
            download = downloads_list[0]

            filename, file_extension = os.path.splitext(download.name)
            if file_extension == '.rar':
                for down in downloads_list:
                    down.status = Download.STATUS_UNRARING
                    ManageDownload.update_download(down, True)

                log.log(__name__, 'unrar', 'Unrar in progress ...', log.LEVEL_INFO, True, download)
                if not utils.is_this_running("[u]nrar x \"%s\"" % download.name):
                    cmd = (
                        ManageDownload.COMMAND_UNRAR % (
                            download.directory.path, download.name))

                    log.log(__name__, 'unrar', 'Command: %s =>' % cmd, log.LEVEL_DEBUG, True, download)

                    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                    ManageDownload.treatment_update_action(action, Action.STATUS_IN_PROGRESS, 0, None, None)

                    line = ''
                    while True:
                        out = p.stdout.read(1)
                        if out == '' and p.poll() is not None:
                            break
                        if out != '':
                            if out != '%':
                                line += out
                            else:
                                values = line.split()
                                if len(values) > 1:
                                    percent = values[int(len(values) - 1)]
                                    log.log(__name__, sys._getframe().f_code.co_name, 'percent ' + percent, log.LEVEL_DEBUG)
                                    ManageDownload.treatment_update_action(action, None, percent, None, None)
                                    log.log(__name__, 'unrar', line, log.LEVEL_DEBUG, True, download)

                    if 'All OK' in line:
                        ManageDownload.treatment_update_action(action, Action.STATUS_FINISHED, 100, None, None)
                        download_status = Download.STATUS_UNRAR_OK
                        log.log(__name__, 'unrar', 'Unrar finished, all is OK', log.LEVEL_INFO, True, download)
                    else:
                        ManageDownload.treatment_update_action(action, Action.STATUS_ERROR, None, None, None)
                        log.log(__name__, 'unrar', 'Unrar finised but error', log.LEVEL_ERROR, True, download)
                        download_status = Download.STATUS_UNRAR_ERROR

                    for down in downloads_list:
                        down.status = download_status
                        ManageDownload.update_download(down, True)
