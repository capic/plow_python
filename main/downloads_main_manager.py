import sys
import config
import log

from threading import Event
from objects.downloads_list import DownloadsList
from file_treatments_manager_thread import FileTreatmentsManagerThread
from downloads_manager_thread import DownloadsManagerThread


class DownloadsMainManager(object):
    def __init__(self):
        self.event_check_downloads_to_start = Event()
        self.file_treatments_manager_thread = FileTreatmentsManagerThread(self.event_check_downloads_to_start)
        self.downloads_manager_thread = DownloadsManagerThread(self.event_check_downloads_to_start)

    def start(self):
        self.file_treatments_manager_thread.start()
        self.downloads_manager_thread.start()

        self.file_treatments_manager_thread.join()
        self.downloads_manager_thread.join()


