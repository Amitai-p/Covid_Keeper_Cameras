import json
import os
import shutil
from threading import Lock
from skimage.metrics import structural_similarity
from azure_sql_server import *

mutex = Lock()
NAME_COMPONENT = 'Camera'
PORT_COMPONENT = '5000'
NAME_OF_FOLDER_IMAGES = 'Images'
NAME_OF_LAST_NAME = '/last_img.jpg'
NAME_OF_NEW_FILE = '/img_new.jpg'
PATH_TO_CONFIG = 'config_json.txt'
NAME_FOLDER_CAMERA = '/cam_'
NAME_FILE = '/img_new.jpg'
KEY_OF_PATH_TO_IMAGES = "PATH_TO_IMAGES"
KEY_OF_THRESOLD_MSE = "THRESOLD_MSE"
KEY_OF_THRESOLD_SIMILARITY = "THRESOLD_SIMILARITY"
KEY_OF_TIME_TO_SLEEP = "TIME_TO_SLEEP"
PATH_TO_SECRET_KEY = "secret.key"
b = Database()
b.set_ip_by_table_name(NAME_COMPONENT)
b.set_port_by_table_name(NAME_COMPONENT, PORT_COMPONENT)
b.set_port_by_table_name(NAME_COMPONENT, PORT_COMPONENT)


# Read the json file of the config.
def read_json(path_to_file):
    with open(path_to_file) as f:
        # From file to string.
        data = json.load(f)
        # From string to dictionary.
        data = json.loads(data)
    return data


config = read_json(PATH_TO_CONFIG)


# Get path to image and delete.
def delete_image(path_to_image):
    try:
        os.remove(path_to_image)
        print("remove ", path_to_image)
    except:
        print("The image doesn't exist")


# Try to find all of the cameras that connected to this computer. Return list of the cameras open.
def get_list_of_cameras(list_cameras):
    delete_list_of_cameras(list_cameras)
    index = 0
    list_of_cameras = []
    while True:
        vid = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        ret, frame = vid.read()
        if ret:
            list_of_cameras.append(vid)
            index += 1
        else:
            break
    print("num cameras: ", len(list_of_cameras))
    return list_of_cameras


# Get list of cameras that connected to this computer and free them.
def delete_list_of_cameras(list_of_cameras):
    for vid in list_of_cameras:
        try:
            vid.release()
        except:
            pass


# Get image, save local, return path.
def save_image_in_folder(img, index):
    if not os.path.exists(config[KEY_OF_PATH_TO_IMAGES]):
        os.makedirs(config[KEY_OF_PATH_TO_IMAGES])
    if not os.path.exists(config[KEY_OF_PATH_TO_IMAGES] + NAME_FOLDER_CAMERA + str(index)):
        os.makedirs(config[KEY_OF_PATH_TO_IMAGES] + NAME_FOLDER_CAMERA + str(index))
    path_to_save = config[KEY_OF_PATH_TO_IMAGES] + NAME_FOLDER_CAMERA + str(index) + NAME_FILE
    cv2.imwrite(path_to_save, img)
    return path_to_save


# Check the 'Mean Squared Error' between two images.
def mse(image1, image2):
    # the 'Mean Squared Error' between the two images is the
    # sum of the squared difference between the two images;
    err = np.sum((image1.astype("float") - image2.astype("float")) ** 2)
    err /= float(image1.shape[0] * image1.shape[1])
    # return the MSE.
    return err


# Compare the difference between 2 images to know if this is almost the same image.
def compare_images(image1, image2, title="no title"):
    try:
        image1 = cv2.imread(image1)
        image2 = cv2.imread(image2)
        # convert the images to grayscale
        image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
        image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
        # compute the mean squared error and structural similarity
        # index for the images
        m = mse(image1, image2)
        s = structural_similarity(image1, image2)
        result = m < config[KEY_OF_THRESOLD_MSE] and s > config[KEY_OF_THRESOLD_SIMILARITY]
        return result
    except:
        return False


# Convert image to format that we can send in restApi.
def convert_image_to_varbinary(filename):
    image = open(filename, 'rb')
    image_read = image.read()
    image_64_encode = base64.encodebytes(image_read)
    image.close()
    return image_64_encode


# Get path to folder of camera. Copy the new image to be the last image that we sent.
def copy_image_in_last_image(path_to_folder):
    delete_image(path_to_folder + NAME_OF_LAST_NAME)
    im1 = cv2.imread(path_to_folder + NAME_OF_NEW_FILE)
    im2 = im1.copy()
    path_to_copy = path_to_folder + NAME_OF_LAST_NAME
    cv2.imwrite(path_to_copy, im2)


# After that the Manager call the get methood we give him list of images from all the cameras.
def get_images():
    print("get images")
    list_images = []
    path = config[KEY_OF_PATH_TO_IMAGES]
    try:
        arr = os.listdir(path)
    except:
        # In case that there is no images
        print("There is no images")
        return []
    for dir in arr:
        have_to_send = False
        file_path = path + dir
        if os.path.isfile(file_path + NAME_OF_NEW_FILE):
            if os.path.isfile(file_path + NAME_OF_LAST_NAME):
                if not compare_images(file_path + NAME_OF_NEW_FILE, file_path + NAME_OF_LAST_NAME):
                    copy_image_in_last_image(file_path)
                    have_to_send = True
            else:
                copy_image_in_last_image(file_path)
                have_to_send = True
        if have_to_send:
            var_binary_image = convert_image_to_varbinary(file_path + NAME_OF_LAST_NAME)
            list_images.append(var_binary_image)
    print("length of list images  ", len(list_images))
    return list_images


# When we start run this service, we want that all of the images will be nwe and update.
def delete_folder_images():
    try:
        if os.path.exists(NAME_OF_FOLDER_IMAGES):
            # removing the file using the os.remove() method
            shutil.rmtree(NAME_OF_FOLDER_IMAGES)
        else:
            # file not found message
            print("The directory already delete")
    except:
        pass


# After change the flag of new config, we update the config to our memory.
def update_config_ip_port(config):
    mutex.acquire()
    dict = b.get_ip_port_config(NAME_COMPONENT)
    mutex.release()
    for conf in dict:
        config[conf] = dict[conf]
    return config


# generate secret key for the manager and the cameras.
def generate_key():
    """
    Generates a key and save it into a file
    """
    from cryptography.fernet import Fernet
    key = Fernet.generate_key()
    with open(PATH_TO_SECRET_KEY, "wb") as key_file:
        key_file.write(key)


# This is make the cameras iterate of take one frmae from all of the cameras and check the flag if we need to be
# activate before all of the iterations.
def run_cameras_iterate():
    # Flag to know if we just now wake uo and have to search new cameras.
    search_new_cameras = True
    have_to_delete_cameras = False
    list_cameras = []
    while True:
        mutex.acquire()
        flag = b.start_or_close_threads()
        mutex.release()
        print('The flag of activate cameras:', flag)
        if int(flag) == 0:
            import time
            search_new_cameras = True
            time.sleep(config[KEY_OF_TIME_TO_SLEEP])
            if not have_to_delete_cameras:
                have_to_delete_cameras = True
                delete_list_of_cameras(list_cameras)
            continue
        else:
            have_to_delete_cameras = False
        if search_new_cameras:
            delete_folder_images()
            list_cameras = get_list_of_cameras(list_cameras)
            search_new_cameras = False
        index = 0
        try:
            for vid0 in list_cameras:
                # Capture the video frame
                ret, frame = vid0.read()
                if not ret:
                    print("There is no frame to read")
                    continue
                save_image_in_folder(frame, index)
                index += 1
        except:
            pass
        import time
        time.sleep(1)
