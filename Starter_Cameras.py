import threading

import psutil as psutil

from Server_Cameras import *
from Cameras import *


# For start running the service of the cameras.
# There is thread that listen to restApi requests.
# There is thread that take frames from the cameras and saved them.
def start_all():
    x = threading.Thread(target=run_server)
    x.start()
    run_cameras_iterate()
    x.join()

import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def stop_all():
    import time
    # Wait for response to http request.
    time.sleep(1)
    os._exit(0)


# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    # change_flag()
    # print(hash_password('Amitai5925'))
    start_all()
