import threading
from Server_Cameras import *
from Cameras import *

# For start running the service of the cameras.
# There is thread that listen to restApi requests.
# There is thread that take frames from the cameras and saved them.
def main():
    x = threading.Thread(target=run_server)
    x.start()
    # run_server().run()
    run_cameras()
    x.join()


# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    main()


