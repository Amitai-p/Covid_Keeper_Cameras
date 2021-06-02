import json
import os
import shutil
from threading import Lock
from skimage.metrics import structural_similarity
from azure_sql_server import *


class list_images_class:
    def __init__(self, list_images):
        self.list_images = list_images

    def to_json(self):
        '''
        convert the instance of this class to json
        '''
        return json.dumps(self, indent=4, default=lambda o: o.__dict__)

    def get_buffer(self):
        print("rteurn bytes")
        return bytes(self)


mutex = Lock()

NAME_COMPONENT = 'Camera'
PORT_COMPONENT = '5000'
b = Database()
b.set_ip_by_table_name(NAME_COMPONENT)
b.set_port_by_table_name(NAME_COMPONENT, PORT_COMPONENT)
b.set_port_by_table_name(NAME_COMPONENT, PORT_COMPONENT)


def init_config():
    config = {}
    config["PATH_TO_IMAGES"] = 'Images/'
    config["THRESOLD_MSE"] = 30
    config["THRESOLD_SIMILARITY"] = 0.8
    config["TIME_TO_SLEEP"] = 5
    config["PASSWORD_MANAGER"] = '3f1c400a02cc171a39fd05da325d7863afb2e3728d6448cc79c4e96f4de6eeac'
    return config


# Insert the config into json file.
def inset_dict_json(path_to_file, config):
    config_json = json.dumps(config)
    with open(path_to_file, 'w') as json_file:
        json.dump(config_json, json_file)


# Read the json file of the config.
def read_json(path_to_file):
    with open(path_to_file) as f:
        # From file to string.
        data = json.load(f)
        # From string to dictionary.
        data = json.loads(data)
    return data


PATH_TO_CONFIG = 'config_json.txt'
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
    name_folder_camera = '/cam_'
    name_file = '/img_new.jpg'
    if not os.path.exists(config["PATH_TO_IMAGES"]):
        os.makedirs(config["PATH_TO_IMAGES"])
    if not os.path.exists(config["PATH_TO_IMAGES"] + name_folder_camera + str(index)):
        os.makedirs(config["PATH_TO_IMAGES"] + name_folder_camera + str(index))
    path_to_save = config["PATH_TO_IMAGES"] + name_folder_camera + str(index) + name_file
    cv2.imwrite(path_to_save, img)
    return path_to_save


# Check the 'Mean Squared Error' between two images.
def mse(image1, image2):
    # the 'Mean Squared Error' between the two images is the
    # sum of the squared difference between the two images;
    # NOTE: the two images must have the same dimension
    err = np.sum((image1.astype("float") - image2.astype("float")) ** 2)
    err /= float(image1.shape[0] * image1.shape[1])
    # return the MSE, the lower the error, the more "similar"
    # the two images are
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
        result = m < config["THRESOLD_MSE"] and s > config["THRESOLD_SIMILARITY"]
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
    name_of_last_file = '/last_img.jpg'
    name_of_new_file = '/img_new.jpg'
    delete_image(path_to_folder + name_of_last_file)
    im1 = cv2.imread(path_to_folder + name_of_new_file)
    im2 = im1.copy()
    path_to_copy = path_to_folder + name_of_last_file
    cv2.imwrite(path_to_copy, im2)


# After that the Manager call the get methood we give him list of images from all the cameras.
def get_images():
    print("get images")
    list_images = []
    path = config["PATH_TO_IMAGES"]
    try:
        arr = os.listdir(path)
    except:
        # In case that there is no images
        print("There is no images")
        return []
    for dir in arr:
        have_to_send = False
        name_of_last_file = '/last_img.jpg'
        name_of_new_file = '/img_new.jpg'
        file_path = path + dir
        if os.path.isfile(file_path + name_of_new_file):
            if os.path.isfile(file_path + name_of_last_file):
                if not compare_images(file_path + name_of_new_file, file_path + name_of_last_file):
                    copy_image_in_last_image(file_path)
                    have_to_send = True
            else:
                copy_image_in_last_image(file_path)
                have_to_send = True
        if have_to_send:
            var_binary_image = convert_image_to_varbinary(file_path + name_of_last_file)
            list_images.append(var_binary_image)
    print("length of list images  ", len(list_images))
    return list_images


# When we start run this service, we want that all of the images will be nwe and update.
def delete_folder_images():
    try:
        path_to_images = 'Images'
        if os.path.exists(path_to_images):
            # removing the file using the os.remove() method
            shutil.rmtree(path_to_images)
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


def generate_key():
    """
    Generates a key and save it into a file
    """
    from cryptography.fernet import Fernet
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
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
            time.sleep(config["TIME_TO_SLEEP"])
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

