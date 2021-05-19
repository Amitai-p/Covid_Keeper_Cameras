import json
import os
import shutil
import time
import cv2
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


NAME_COMPONENT = 'Camera'
PORT_COMPONENT = '5000'
b = Database()
b.set_ip_by_table_name(NAME_COMPONENT)
b.set_port_by_table_name(NAME_COMPONENT, PORT_COMPONENT)


def init_config():
    config = {}
    config["PATH_TO_IMAGES"] = 'Images/'
    config["THRESOLD_MSE"] = 30
    config["THRESOLD_SIMILARITY"] = 0.8
    config["TIME_TO_SLEEP"] = 5
    return config


config = init_config()


# Get path to image and delete.
def delete_image(path_to_image):
    try:
        os.remove(path_to_image)
        print("remove ", path_to_image)
    except:
        print("The image doesn't exist")


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


def mse(imageA, imageB):
    # the 'Mean Squared Error' between the two images is the
    # sum of the squared difference between the two images;
    # NOTE: the two images must have the same dimension
    err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
    err /= float(imageA.shape[0] * imageA.shape[1])
    # return the MSE, the lower the error, the more "similar"
    # the two images are
    return err


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
        print("Res:  ", result, " m: ", m, "S: ", s)
        return result
    except:
        return False


def convert_image_to_varbinary(filename):
    image = open(filename, 'rb')
    image_read = image.read()
    image_64_encode = base64.encodebytes(image_read)
    image.close()
    return image_64_encode


def copy_image_in_last_image(path_to_folder):
    name_of_last_file = '/last_img.jpg'
    name_of_new_file = '/img_new.jpg'
    delete_image(path_to_folder + name_of_last_file)
    im1 = cv2.imread(path_to_folder + name_of_new_file)
    im2 = im1.copy()
    path_to_copy = path_to_folder + name_of_last_file
    cv2.imwrite(path_to_copy, im2)


def get_images():
    print("get images")
    ####
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


def delete_folder_images():
    path_to_images = 'Images'
    if os.path.exists(path_to_images):
        # removing the file using the os.remove() method
        shutil.rmtree(path_to_images)
    else:
        # file not found message
        print("The directory already delete")


def update_config_ip_port(config):
    dict = b.get_ip_port_config(NAME_COMPONENT)
    for conf in dict:
        config[conf] = dict[conf]
    return config


def run_cameras_iterate():
    # counter = 0
    search_new_cameras = True
    list_cameras = []
    # list_cameras = get_list_of_cameras()

    while True:
        # if flag == 0:
        flag = b.start_or_close_threads()
        print(flag)
        if int(flag) == 0:
            import time
            search_new_cameras = True
            time.sleep(config["TIME_TO_SLEEP"])
            continue
        if search_new_cameras:
            try:
                delete_folder_images()
            except:
                pass
            list_cameras = get_list_of_cameras(list_cameras)
            search_new_cameras = False
        index = 0
        try:
            for vid0 in list_cameras:
                # In case of close
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


def run_cameras():
    delete_folder_images()
    list_cameras = get_list_of_cameras()
    while True:
        index = 0
        for vid0 in list_cameras:
            # In case of close
            # Capture the video frame
            ret, frame = vid0.read()
            if not ret:
                print("There is no frame to read")
                continue
            save_image_in_folder(frame, index)
            # save_image(frame)
            # print(q)
            time.sleep(1)
            index += 1
