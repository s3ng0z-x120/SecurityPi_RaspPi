# -*- encoding:utf-8 -*-
from core.Controller import Controller
from models.Connection import Connection
from config import APP_PATH
import gc
import os
import io
import struct
import time
import cv2
import sys
import zipfile
import numpy as np
import tensorflow as tf
from threading import Thread, Event
import multiprocessing
from multiprocessing import Manager
#from PIL import Image
import PIL

"""
    Main controller. It will be responsible for program's main screen behavior.
"""
class HomeController(Controller):

    #-----------------------------------------------------------------------
    #        Constructor
    #-----------------------------------------------------------------------
    def __init__(self):
        self.homeView = self.loadView("Home")
        self.homeModel = self.loadModel("Home")
        self.homeModel.openLogging()
    
    
    #-----------------------------------------------------------------------
    #        Methods
    #-----------------------------------------------------------------------
    """
        @description
    """
    def main(self):
        self.homeModel.log('INIT SESSION')
        self.homeModel.log('INIT Update System')
        #self.homeView.loadingUpdates()
        self.homeModel.loadUpdates()
        #self.homeView.completedUpgrades()
        self.homeModel.log('END Update System')
        #self.homeView.welcome()
        self.executeThreads()
        self.homeModel.log('END SESSION')
        #self.homeView.close()

    """
        @description Handler that is called by the thread so that the application uses the OpenCV library for face detection.
    """
    def handlerVideoOpenCV(self):
        clientSocket = self.homeModel.connectSocket()
        print('clientSocket: ' + str(clientSocket))
        cap = self.homeModel.openVideo()

        pathHaarcascade = APP_PATH + '/lib/haarcascade_frontalface_default.xml'
        faceCascade = cv2.CascadeClassifier(pathHaarcascade)

        #video.start_preview()
        time.sleep(2)

        # used to record the time when we processed last frame
        prev_frame_time = 0
        
        # used to record the time at which we processed current frame
        new_frame_time = 0

        # font which we will be using to display FPS
        font = cv2.FONT_HERSHEY_SIMPLEX

        stream = io.BytesIO()
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        cont = 0
        while(cap.isOpened()):
            # Construct a numpy array from the stream
            ret, image = cap.read()
            #image = cv2.resize(frame, (1280, 720))
            # time when we finish processing for this frame
            new_frame_time = time.time()

            # Calculating the fps
 
            # fps will be number of frame processed in given time frame
            # since their will be most of time error of 0.001 second
            # we will be subtracting it to get more accurate result
            fps = 1/(new_frame_time-prev_frame_time)
            prev_frame_time = new_frame_time
        
            # converting the fps into integer
            fps = float(fps)
        
            # converting the fps to string so that we can display it on frame
            # by using putText function
            fps = str(fps)
        
            # putting the FPS count on the frame
            cv2.putText(image, fps, (7, 70), font, 3, (100, 255, 0), 3, cv2.LINE_AA)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            if(cont % 5 == 0):
                cont = 0
                image = self.homeModel.processImage(image, faceCascade)
                imageToEncode = self.homeModel.encodeImage(image, encode_param)

                size = len(imageToEncode)
                stream.seek(0)
                stream.truncate()

                clientSocket.sendall(struct.pack(">L", size) + imageToEncode)
            cont += 1

            #Waits for a user input to quit the application
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        clientSocket.close()

    """
        @description Handler that is called by the thread so that the application uses the OpenCV library for face detection.
    """
    def handlerCAMOpenCV(self):
        clientSocket = self.homeModel.connectSocket()
        print('clientSocket: ' + str(clientSocket))
        camera = self.homeModel.connectCamera()

        pathHaarcascade = APP_PATH + '/lib/haarcascade_frontalface_default.xml'
        faceCascade = cv2.CascadeClassifier(pathHaarcascade)

        camera.start_preview()
        time.sleep(2)

        # used to record the time when we processed last frame
        prev_frame_time = 0
        
        # used to record the time at which we processed current frame
        new_frame_time = 0

        # font which we will be using to display FPS
        font = cv2.FONT_HERSHEY_SIMPLEX

        stream = io.BytesIO()
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        for frame in camera.capture_continuous(stream, 'jpeg'):
            # Construct a numpy array from the stream
            data = np.fromstring(stream.getvalue(), dtype=np.uint8)
            # "Decode" the image from the array, preserving colour
            image = cv2.imdecode(data, 1)
            image = cv2.resize(image, (1280, 720))
            # time when we finish processing for this frame
            new_frame_time = time.time()

            # Calculating the fps
 
            # fps will be number of frame processed in given time frame
            # since their will be most of time error of 0.001 second
            # we will be subtracting it to get more accurate result
            fps = 1/(new_frame_time-prev_frame_time)
            prev_frame_time = new_frame_time
        
            # converting the fps into integer
            fps = float(fps)
        
            # converting the fps to string so that we can display it on frame
            # by using putText function
            fps = str(fps)
        
            # putting the FPS count on the frame
            cv2.putText(image, fps, (7, 70), font, 3, (100, 255, 0), 3, cv2.LINE_AA)

            imageFaceDetected = self.homeModel.processImage(image, faceCascade)
            imageToEncode = self.homeModel.encodeImage(imageFaceDetected, encode_param)

            size = len(imageToEncode)
            stream.seek(0)
            stream.truncate()

            clientSocket.sendall(struct.pack(">L", size) + imageToEncode)

            #Waits for a user input to quit the application
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        camera.release()
        clientSocket.close()
    
    """
        @description Handler that is called by the thread so that the application uses the TensorFlow library for face detection.
    """
    def handlerCAMTensorFlow(self):
        clientSocket = self.homeModel.connectSocket()
        camera = self.homeModel.connectCamera()
        

        camera.start_preview()
        time.sleep(2)
        
        # Load a (frozen) Tensorflow model into memory.
        detection_graph = tf.Graph()
        with detection_graph.as_default():
            od_graph_def = tf.compat.v1.GraphDef()
            with tf.io.gfile.GFile(self.homeModel.getPathToCKPT(), 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')
        
        #detection of video
        with detection_graph.as_default():
            with tf.compat.v1.Session(graph=detection_graph) as sess:
                stream = io.BytesIO()
                #while True:
                for frame in camera.capture_continuous(stream, 'jpeg'):
                    # Construct a numpy array from the stream
                    data = np.fromstring(stream.getvalue(), dtype=np.uint8)
                    # "Decode" the image from the array, preserving colour
                    image = cv2.imdecode(data, 1)
                    # Resize image
                    imS = cv2.resize(image, (720, 680))

                    imageFaceDetected = self.homeModel.processImagenTF(detection_graph, imS, sess)
                    imageToEncode = self.homeModel.encodeImage(imageFaceDetected)

                    size = len(imageToEncode)
                    stream.seek(0)
                    stream.truncate()

                    clientSocket.sendall(struct.pack(">L", size) + imageToEncode)

                    #Waits for a user input to quit the application
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                camera.release()
                clientSocket.close()

    def sendScreenShoot(self):
        clientSocket = self.homeModel.connectSocketSendScreenShoot()
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        if not os.path.isdir(APP_PATH+'/frame_container'):
            os.mkdir(APP_PATH+'/frame_container')

        while True:
            path, dirs, files = next(os.walk(APP_PATH+'/frame_container'))
            file_count = len(files)
            #zip_name = APP_PATH + '/main.zip'

            if(file_count > 0):
                for filename in os.listdir('./frame_container'):
                    img = None
                    if filename.endswith(".jpg") or filename.endswith(".png"):
                        #image = cv2.imread(APP_PATH + '/frame_container/' + filename)
                        with open(APP_PATH + '/frame_container/' + filename, 'rb') as img_bin:
                            '''
                            buff = io.BytesIO()
                            buff.write(img_bin.read())
                            buff.seek(0)
                            '''
                            '''
                            # This portion is part of my test code
                            byteImgIO = io.BytesIO()
                            byteImg = img_bin
                            #byteImg.save(byteImgIO, "JPG")
                            byteImgIO.seek(0)
                            byteImg = byteImgIO.read()

                            # Non test code
                            dataBytesIO = io.BytesIO(byteImg)
                            
                            temp_img = np.array(img_bin, dtype=np.uint8)
                            #img = cv2.cvtColor(temp_img, cv2.COLOR_BGR2GRAY)
                            print('./frame_container/' + filename)
                            '''

                            if not temp_img is None:
                                imageToEncode = self.homeModel.encodeImage(img_bin, encode_param)
                                size = len(imageToEncode)
                                print('len(imageToEncode): '+str(len(imageToEncode))+' escribiendo...')
                                clientSocket.sendall(struct.pack(">L", size) + imageToEncode)
                                print('Enviado...')
                        os.remove(APP_PATH + '/frame_container/' + filename)
                        '''
                        #client_socket.send(filename)
                        file_name = open(APP_PATH + '/frame_container/' + filename ,'rb')
                        print('./frame_container/' + filename)
                        #image = file_name.read()
                        image_size = os.path.getsize(APP_PATH + '/frame_container/' + filename)
                        print('image_size: ' + str(image_size))
                        clientSocket.sendall(struct.pack(">L", image_size))
                        data = b""
                        count = 0
                        while len(data) < image_size:
                            data += file_name.readline()
                            if not data:
                                print('A pasado algo')
                                break
                            else:
                                print('len(data): '+str(len(data))+' escribiendo...')
                        if data:
                            #clientSocket.send(data)
                            clientSocket.sendall(struct.pack(">I", image_size))
                            print('Enviandoo...')
                        file_name.close()
                        #os.remove(APP_PATH + '/frame_container/' + filename)
                        '''
                '''
                with zipfile.ZipFile(zip_name, 'w') as file:
                    for filename in os.listdir('./frame_container'):
                        if filename.endswith(".jpg") or filename.endswith(".png"):
                                file.write(APP_PATH + '/frame_container/' + filename)
                                os.remove(APP_PATH + '/frame_container/' + filename)
            
                    #clientSocket.send(zip_name.encode())
                    with open(zip_name,"rb") as f:
                        data=f.read()
                        clientSocket.sendall(data)
                        f.close()
                    os.remove(zip_name)
                '''
            '''
            f = open(zip_name, 'rb')
            l = f.read()
            clientSocket.sendall(l)
            f.close()
            clientSocket.close()
            os.remove(zip_name)
            '''
            
            
        
            '''
            if(file_count > 0):
                for filename in os.listdir('./frame_container'):
                    if filename.endswith(".jpg") or filename.endswith(".png"):
                        # open image
                        myfile = open(APP_PATH+'/frame_container/'+filename, 'rb')
                        image = myfile.read()
                        if image is None:
                            os.remove(APP_PATH + '/frame_container/' + filename)     # always check for None
                            break
                        #clientSocket.send(image)
                        size = len(image)
                        clientSocket.sendall(struct.pack(">L", size) + image)
                        myfile.close()
                        #image = cv2.imread(APP_PATH+'/frame_container/'+filename)
                        #image = cv2.imdecode(np.fromfile(APP_PATH+'/frame_container/'+filename, dtype=np.uint8), -1)
                        
                        #image = cv2.imread(APP_PATH+'/frame_container/'+filename, cv2.IMREAD_COLOR)

                        #clientSocket.send(image)
                        #image = cv2.imread(APP_PATH+'/frame_container/'+filename, cv2.IMREAD_GRAYSCALE)
                        ---
                        if image is None:
                            os.remove(APP_PATH + '/frame_container/' + filename)     # always check for None
                            break
                        
                        print(APP_PATH+'/frame_container/'+filename)
                        imageToEncode = self.homeModel.encodeImage(image, encode_param)
                        size = len(imageToEncode)
                        clientSocket.sendall(struct.pack(">L", size) + imageToEncode)
                        myfile.close()
                        os.remove(APP_PATH + '/frame_container/' + filename)
                        print('img: ' + filename + ' send')
                        ---
                        image = image.tobytes()
                        size = len(image)
                        clientSocket.sendall(struct.pack(">L", size) + image)
                        '''
        clientSocket.close()
            

    """
        @description Method that will allow the user to interact with the system
    """
    def executeThreads(self):

        threads = []


        cam = Thread(target=self.handlerVideoOpenCV, args=())
        threads.append(cam)

        sendScreenShoot = Thread(target=self.sendScreenShoot, args=())
        threads.append(sendScreenShoot)

        #camTF = Thread(target=self.handlerCAMTensorFlow, args=(killAll,))
        #threads.append(camTF)

         # starting processes
        for thd in threads:
            thd.start()
    
        # wait until processes are finished
        for thd in threads:#
            thd.join()
        
        gc.collect()
 

    """
        @description Method that will allow the user to interact with the system
        @author Andrés Gómez
    """
    def loop2(self):
        processes = []
        gc.collect()
        with Manager() as manager:
            # creating a list in server process memory
            #parameters = manager.list([('killAll', 1)])
            #lproxy = manager.list()
            #lproxy.append({'killAll':0})
            lproxy = manager.dict()
            lproxy['killAll'] = 1

            # printing main program process id
            print("ID of main process: {}".format(os.getpid()))
            # creating processes
            '''
            reviewScreenshots = multiprocessing.Process(target=self.homeModel.workerReviewScreenshots, args=(lproxy,))
            processes.append(reviewScreenshots)

            sendScreenShoot = multiprocessing.Process(target=self.homeModel.workerSendScreenshots, args=(lproxy,))
            processes.append(sendScreenShoot)
            '''
            cam = multiprocessing.Process(target=self.homeModel.workerCAM, args=(lproxy,))
            processes.append(cam)

            

            # starting processes
            for process in processes:
                process.start()
        
            # wait until processes are finished
            for process in processes:
                process.join()

            print(lproxy)
            
            gc.collect()