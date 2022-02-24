import socket


class Connection:

    URL = '192.168.0.22'
    PORT = 8000

    def __init__(self):
        pass

    """
        @description Method that establishes the communication channel with the socket.
    """
    def connect():
        #clientSocket = socket.socket()
        #clientSocket.connect((self.URL, self.PORT))
        #clientSocket.connect(('192.168.228.31', 8000))
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #clientSocket.connect(('192.168.1.33', 8000))
        clientSocket.connect(('192.168.0.105', 8000))
        clientSocket.makefile('wb')
        print('clientSocket: ' + str(clientSocket))
        return clientSocket

    def connectSendScreenShoot():
        #clientSocket = socket.socket()
        #clientSocket.connect((self.URL, self.PORT))
        #clientSocket.connect(('192.168.228.31', 8000))
        clientSocket = socket.socket()
        clientSocket.connect(('192.168.0.105', 8080))
        clientSocket.makefile('wb')
        print('clientSocket: ' + str(clientSocket))
        return clientSocket

    """
        @description Method that closes the socket communication channel.
    """
    def closeConn(clientSocket):
        clientSocket.close()