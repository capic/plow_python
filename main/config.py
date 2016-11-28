__author__ = 'Vincent'
from bean.applicationConfigurationBean import ApplicationConfiguration
from bean.downloadDirectoryBean import DownloadDirectory

LOG_FORMAT = '[%(levelname)8s]  %(asctime)s <%(to_ihm)4s>     (%(file_name)s) {%(function_name)s} "%(message)s"'
DATE_FORMAT = '%d/%m/%Y %H:%M:%S'

# CONFIG_FILE = '/var/www/plow_solution/config.cfg'
CONFIG_FILE = '/var/www/plow_solution_dev/config_python.cfg'

RESCUE_MODE = False


def init():
    global application_configuration
    application_configuration = ApplicationConfiguration()

    application_configuration.id_application = 1
    application_configuration.download_activated = True
    # application_configuration.rest_address = 'http://192.168.1.101:3001/'
    application_configuration.rest_address = 'http://192.168.1.101:3000/'
    application_configuration.notification_address = 'ws://capic.hd.free.fr:8181/ws'
    application_configuration.python_log_level = 4
    application_configuration.python_log_format = LOG_FORMAT
    application_configuration.python_log_console_level = 4
    application_configuration.python_log_directory = DownloadDirectory()
    application_configuration.python_log_directory.path = '/var/www/plow_solution/log/'
    application_configuration.python_directory_download_temp = DownloadDirectory()
    application_configuration.python_directory_download_temp.path = '/mnt/HD/HD_a2/telechargement/temp_plowdown/'
    application_configuration.python_directory_download = DownloadDirectory()
    application_configuration.python_directory_download.path = '/mnt/HD/HD_a2/telechargement/'
