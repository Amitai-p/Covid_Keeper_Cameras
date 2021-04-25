import json
import math
import os
import queue
import shutil
import threading
import time
from skimage.measure import compare_ssim
import argparse
import imutils
import cv2
from skimage.metrics import structural_similarity

from azure_sql_server_actual import *


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


print("startttt")
list_c = []
counter = 0
size_n = 2


# Get path to image and delete.
def delete_image(path_to_image):
    try:
        os.remove(path_to_image)
        print("remove ", path_to_image)
    except:
        print("The image doesn't exist")


def get_list_of_cameras():
    index = 0
    list = []
    # cap = cv2.VideoCapture('178.203.161.161:81', cv2.CAP_DSHOW)
    # list.append(cap)
    # print(cap)
    # ret, frame = cap.read()
    # print(ret)
    # import time
    # time.sleep(20)
    # index += 1
    while True:
        vid = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        ret, frame = vid.read()
        if ret:
            list.append(vid)
            index += 1
        else:
            break
    print("num cameras: ", len(list))
    return list


# Get image, save local, return path.
def save_image_in_folder(img, index):
    if not os.path.exists('Images'):
        os.makedirs('Images')
    if not os.path.exists('Images/cam_' + str(index)):
        os.makedirs('Images/cam_' + str(index))
    path_to_save = 'Images/cam_' + str(index) + '/img_new.jpg'
    cv2.imwrite(path_to_save, img)
    return path_to_save


# Get image, save local, return path.
def save_image(img):
    global counter
    if not os.path.exists('Images'):
        os.makedirs('Images')
    path_to_save = "Images/img%s.jpg" % str(counter)
    counter = (counter + 1) % size_n
    cv2.imwrite(path_to_save, img)
    return path_to_save


from skimage.measure import *
import matplotlib.pyplot as plt
import numpy as np
import cv2


def mse(imageA, imageB):
    # the 'Mean Squared Error' between the two images is the
    # sum of the squared difference between the two images;
    # NOTE: the two images must have the same dimension
    err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
    err /= float(imageA.shape[0] * imageA.shape[1])

    # return the MSE, the lower the error, the more "similar"
    # the two images are
    return err


def compare_images(imageA, imageB, title="no title"):
    try:
        imageA = cv2.imread(imageA)
        imageB = cv2.imread(imageB)
        # shopped = cv2.imread("images/jp_gates_photoshopped.png")
        # convert the images to grayscale
        imageA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
        imageB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
        # compute the mean squared error and structural similarity
        # index for the images
        m = mse(imageA, imageB)
        s = structural_similarity(imageA, imageB)
        result = m < 30 and s > 0.8
        print("Res:  ", result, " m: ", m, "S: ", s)
        return result
    except:
        return False
    # # setup the figure
    # fig = plt.figure(title)
    # plt.suptitle("MSE: %.2f, SSIM: %.2f" % (m, s))
    # # show first image
    # ax = fig.add_subplot(1, 2, 1)
    # plt.imshow(imageA, cmap=plt.cm.gray)
    # plt.axis("off")
    # # show the second image
    # ax = fig.add_subplot(1, 2, 2)
    # plt.imshow(imageB, cmap=plt.cm.gray)
    # plt.axis("off")
    # # show the images
    # plt.show()


def convert_image_to_varbinary(filename):
    image = open(filename, 'rb')
    image_read = image.read()
    image_64_encode = base64.encodebytes(image_read)
    image.close()
    return image_64_encode


def copy_image_in_last_image(path_to_folder):
    delete_image(path_to_folder + '/last_img.jpg')
    im1 = cv2.imread(path_to_folder + '/img_new.jpg')
    im2 = im1.copy()
    path_to_copy = path_to_folder + '/last_img.jpg'
    cv2.imwrite(path_to_copy, im2)


def get_images():
    print("get images")
    ####
    list_images = []
    path = 'Images/'
    try:
        arr = os.listdir(path)
    except:
        # In case that there is no images
        print("There is no images")
        return []
    # print("arrrr", arr)
    for dir in arr:
        have_to_send = False
        file_path = path + dir
        if os.path.isfile(file_path + '/img_new.jpg'):
            if os.path.isfile(file_path + '/last_img.jpg'):
                if not compare_images(file_path + '/img_new.jpg', file_path + '/last_img.jpg'):
                    copy_image_in_last_image(file_path)
                    print("copy1")
                    have_to_send = True
            else:
                copy_image_in_last_image(file_path)
                print("copy2")
                have_to_send = True
        if have_to_send:
            var_binary_image = convert_image_to_varbinary(file_path + '/last_img.jpg')
            list_images.append(var_binary_image)
        # list_images(bytes(img))
    print("ok  ", len(list_images))

    # print(list_images)
    return list_images


def get_images_old():
    print("get images")
    ####
    list_images = []
    path = 'Images/'
    arr = os.listdir(path)
    # print("arrrr", arr)
    for img in arr:
        var_binary_image = convert_image_to_varbinary(path + img)
        # print("var: " ,var_binary_image)
        # list_images.append(base64.encodebytes(img).decode('utf-8'))
        list_images.append(var_binary_image)
        # list_images(bytes(img))
    print("ok")

    # print(list_images)
    return list_images


def delete_folder_images():
    path_to_images = 'Images'
    if os.path.exists(path_to_images):
        # removing the file using the os.remove() method
        shutil.rmtree(path_to_images)
    else:
        # file not found message
        print("The directory already delete")


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
            list_c.append(frame)
            save_image_in_folder(frame, index)
            # save_image(frame)
            # print(q)
            time.sleep(1)
            index += 1
