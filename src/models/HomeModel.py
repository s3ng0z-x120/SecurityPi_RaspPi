from datetime import datetime, date
from config import APP_PATH
import os
import time
import io
import struct
import sys
from models.singlemotiondetector import SingleMotionDetector
from picamera.array import PiRGBArray
import picamera
from .Connection import Connection
import cv2
import numpy as np
import gc
import tempfile
import tensorflow as tf
import six.moves.urllib as urllib
import collections
import imutils
from imutils.video import VideoStream
import pickle
import socket
#import git

path = ''
MODEL_NAME = './ssd_mobilenet_v1_coco_2018_01_28'
MODEL_FILE = MODEL_NAME + '.tar.gz'
PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb'

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = 'person_label_map.pbtxt'
NUM_CLASSES = 90
STANDARD_COLORS = [
    'AliceBlue', 'Chartreuse', 'Aqua', 'Aquamarine', 'Azure', 'Beige', 'Bisque',
    'BlanchedAlmond', 'BlueViolet', 'BurlyWood', 'CadetBlue', 'AntiqueWhite',
    'Chocolate', 'Coral', 'CornflowerBlue', 'Cornsilk', 'Crimson', 'Cyan',
    'DarkCyan', 'DarkGoldenRod', 'DarkGrey', 'DarkKhaki', 'DarkOrange',
    'DarkOrchid', 'DarkSalmon', 'DarkSeaGreen', 'DarkTurquoise', 'DarkViolet',
    'DeepPink', 'DeepSkyBlue', 'DodgerBlue', 'FireBrick', 'FloralWhite',
    'ForestGreen', 'Fuchsia', 'Gainsboro', 'GhostWhite', 'Gold', 'GoldenRod',
    'Salmon', 'Tan', 'HoneyDew', 'HotPink', 'IndianRed', 'Ivory', 'Khaki',
    'Lavender', 'LavenderBlush', 'LawnGreen', 'LemonChiffon', 'LightBlue',
    'LightCoral', 'LightCyan', 'LightGoldenRodYellow', 'LightGray', 'LightGrey',
    'LightGreen', 'LightPink', 'LightSalmon', 'LightSeaGreen', 'LightSkyBlue',
    'LightSlateGray', 'LightSlateGrey', 'LightSteelBlue', 'LightYellow', 'Lime',
    'LimeGreen', 'Linen', 'Magenta', 'MediumAquaMarine', 'MediumOrchid',
    'MediumPurple', 'MediumSeaGreen', 'MediumSlateBlue', 'MediumSpringGreen',
    'MediumTurquoise', 'MediumVioletRed', 'MintCream', 'MistyRose', 'Moccasin',
    'NavajoWhite', 'OldLace', 'Olive', 'OliveDrab', 'Orange', 'OrangeRed',
    'Orchid', 'PaleGoldenRod', 'PaleGreen', 'PaleTurquoise', 'PaleVioletRed',
    'PapayaWhip', 'PeachPuff', 'Peru', 'Pink', 'Plum', 'PowderBlue', 'Purple',
    'Red', 'RosyBrown', 'RoyalBlue', 'SaddleBrown', 'Green', 'SandyBrown',
    'SeaGreen', 'SeaShell', 'Sienna', 'Silver', 'SkyBlue', 'SlateBlue',
    'SlateGray', 'SlateGrey', 'Snow', 'SpringGreen', 'SteelBlue', 'GreenYellow',
    'Teal', 'Thistle', 'Tomato', 'Turquoise', 'Violet', 'Wheat', 'White',
    'WhiteSmoke', 'Yellow', 'YellowGreen'
]

"""
    Model description
"""
class HomeModel:
    def __init__(self, controller):
        self.homeController = controller
        pass

    def openLogging(self):
        global path
        
        today = date.today()
        filename = 'logging_'+str(today)+'.txt'
        if not os.path.exists(APP_PATH+"/logs"):
            os.makedirs(APP_PATH+"/logs")
        
        path = os.path.join(APP_PATH + "/logs/", filename)
        open(path, 'a+')

    def log(self, info):
        global path
        
        file = open(path, 'a+')
        now = datetime.now()
        line = str(info) + ' - ' + str(now) + '\n'
        
        file.write(line)
        file.close()
    
    def loadUpdates(self):
        os.system('../scripts/executeUpdates.sh')

    def clearCache(self):
        pass

    def workerCAM(self, lproxy):

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('192.168.228.31', 8485))
        connection = client_socket.makefile('wb')

        cam = cv2.VideoCapture(0)

        cam.set(3, 320);
        cam.set(4, 240);

        img_counter = 0

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

        while True:
            ret, frame = cam.read()
            result, frame = cv2.imencode('.jpg', frame, encode_param)
        #    data = zlib.compress(pickle.dumps(frame, 0))
            data = pickle.dumps(frame, 0)
            size = len(data)

            print("{}: {}".format(img_counter, size))
            client_socket.sendall(struct.pack(">L", size) + data)
            img_counter += 1

        cam.release()
        pass
  
    def workerReviewScreenshots(self, lproxy):
        pathHaarcascade = APP_PATH + '/libs/haarcascade_frontalface_alt2.xml';
        faceCascade = cv2.CascadeClassifier(pathHaarcascade)
        if not os.path.isdir(APP_PATH+'/store'):
            os.mkdir(APP_PATH+'/store')
        
        if not os.path.isdir(APP_PATH+'/sender'):
            os.mkdir(APP_PATH+'/sender')
        
        while lproxy.get('killAll') != 0:
            path, dirs, files = next(os.walk(APP_PATH+'/store'))
            file_count = len(files)
            if(file_count > 0):
                for filename in os.listdir('./store'):
                    if filename.endswith(".jpg") or filename.endswith(".png"):
                        image = cv2.imread(os.path.join('./store', filename))
                        grayScale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                        facesContainer = faceCascade.detectMultiScale(grayScale, scaleFactor = 1.1, minNeighbors = 15, minSize = (70, 70))
                        for(x, y, w, h) in facesContainer:
                            cv2.rectangle(grayScale, (x, y), (x + w, y + h), (0, 255, 0), 2)
                            roiColor = cv2.resize(grayScale[y:(y + h), x:(x + h)], (w, h), interpolation = cv2.INTER_AREA)
                            if not os.path.isdir(APP_PATH+'/store/facesContainer'):
                                os.mkdir(APP_PATH+'/store/facesContainer')
                            
                            tempName = next(tempfile._get_candidate_names())
                            img = cv2.GaussianBlur(roiColor, (3,3), 0)
                            
                            #self.homeModel.log('[INFO] ' + tempName + ' only GB: ' + str(img) + ' GB+LP: ' + str(self.varianceLaplacian(img)) + ' LP: ' + str(self.varianceLaplacian(roiColor)))
                            print('[INFO] ' + tempName + ' LP: ' + str(self.varianceLaplacian(img)) + ' LP: ' + str(self.varianceLaplacian(roiColor)))
                            cv2.imwrite((APP_PATH+'/store/facesContainer/'+str(tempName)+'.jpg'), roiColor)
                    cv2.imwrite((APP_PATH+'/sender/'+str(filename)+'.jpg'), image)
                    os.remove(os.path.join('./store', filename))


    def workerSendScreenshots(self, lproxy):
        pathHaarcascade = APP_PATH + '/libs/haarcascade_frontalface_alt2.xml';
        faceCascade = cv2.CascadeClassifier(pathHaarcascade)
        if not os.path.isdir(APP_PATH+'/store'):
            os.mkdir(APP_PATH+'/store')
        
        while lproxy.get('killAll') != 0:
            path, dirs, files = next(os.walk(APP_PATH+'/store'))
            file_count = len(files)
            if(file_count > 0):
                for filename in os.listdir('./store'):
                    if filename.endswith(".jpg") or filename.endswith(".png"):
                        print('Hola Mundo')
