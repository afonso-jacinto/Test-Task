import os
import shutil
import time
import hashlib
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(filename='sync.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def sync_folders(source, replica):
    for root, dirs, files in os.walk(source):
        relative_path = os.path.relpath(root, source)
        replica_root = os.path.join(replica, relative_path)

        if not os.path.exists(replica_root):
            os.makedirs(replica_root)

        for file in files:
            source_file = os.path.join(root, file)
            replica_file = os.path.join(replica_root, file)

            if not os.path.exists(replica_file) or calculate_md5(source_file) != calculate_md5(replica_file):
                shutil.copy2(source_file, replica_file)
                logging.info(f'Copied: {source_file} to {replica_file}')

    for root, dirs, files in os.walk(replica):
        relative_path = os.path.relpath(root, replica)
        source_root = os.path.join(source, relative_path)

        for file in files:
            replica_file = os.path.join(root, file)
            source_file = os.path.join(source_root, file)

            if not os.path.exists(source_file):
                os.remove(replica_file)
                logging.info(f'Removed: {replica_file}')

class SyncHandler(FileSystemEventHandler):
    def __init__(self, source, replica):
        self.source = source
        self.replica = replica

    def on_modified(self, event):
        sync_folders(self.source, self.replica)

    def on_created(self, event):
        sync_folders(self.source, self.replica)

    def on_deleted(self, event):
        sync_folders(self.source, self.replica)

if __name__ == "__main__":
    source_folder = 'source'
    replica_folder = 'replica'
    sync_interval = 10  # seconds

    sync_folders(source_folder, replica_folder)

    event_handler = SyncHandler(source_folder, replica_folder)
    observer = Observer()
    observer.schedule(event_handler, path=source_folder, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(sync_interval)
            sync_folders(source_folder, replica_folder)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
