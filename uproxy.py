from socket import *     # to open sockets
import select       # to handle multiple requests
import signal

connectionsToHandle = [] # list of tuples of sockets to handle (client, server)

# add a handler for the SIGINT signal (Ctrl+C) to stop the program
def signal_handler(sig, frame):
    #try to close all the sockets
    for connectionSocket, destSocket in connectionsToHandle:
        try:
            connectionSocket.close()
        except:
            pass
        try:
            destSocket.close()
        except:
            pass
    try:
        serverSocket.close()
    except:
        pass
    print('µSOCKS5 server has been stopped.')
    exit(0)
signal.signal(signal.SIGINT, signal_handler)

# This method verifies that the client accepts the authentication method 0 (no authentication)
def validateAuthentication(connectionSocket, addr):
    # This function handles the request of a given socket-pair, i.e., a given client
    # Read the SOCKS version and the number of methods supported by the client
    greetingFromClient = connectionSocket.recv(2)
    if greetingFromClient[0] == 5: # the protocol is SOCKS5, let's proceed
        supportedMethods = connectionSocket.recv(greetingFromClient[1])
        if 0 in supportedMethods: # the "no authentication" method is supported by the client
            # Respond to the client confirming that the connection without authentication has been accepted
            response = [5, 0] # SOCKS version: 5; chosen method: 0
            connectionSocket.send(bytearray(response))
            return True
        else:
            print('The client', addr, 'does not support connections without authentication! Unable to proceed.')
    else:
        print('The client', addr, 'indicates a protocol different from SOCKS5! Unable to proceed.')
    connectionSocket.close()
    return False

def readRequest(connectionSocket, addr):
    try:
        connectionDetails = connectionSocket.recv(4)
        # The first 4 bytes read are:
        # SOCKS version number: 5
        # Command code: 1=connect; 2=bind; 3=UDP associate (this script only implements 1)
        # Reserved byte set to zero
        # Address type: 1=IPv4 address; 3=domain name; 4=IPv6 address
        if connectionDetails[0] == 5: # the protocol is SOCKS5, let's proceed
            if connectionDetails[1] == 1: # the command code is CONNECT
                serverDestHost = 0
                if connectionDetails[3] != 3: # the address type is not a domain name, so it's an IP
                    # read 4 or 16 bytes, depending on whether the request indicates an IPv4 or IPv6
                    ip = connectionSocket.recv(4 if (connectionDetails[3] == 1) else 16)
                    #serverDestHost = str(ipaddress.ip_address(ip))
                    if connectionDetails[3] == 1:
                        serverDestHost = str(ip[0]) + '.' + str(ip[1]) + '.' + str(ip[2]) + '.' + str(ip[3])
                    else:
                        # ipv6 canonical representation
                        serverDestHost = ':'.join([format(ip[i] * 256 + ip[i+1], 'x') for i in range(0, 16, 2)])
                else: # a domain name has been provided
                    addrLen = connectionSocket.recv(1) # length of the string for the domain name
                    serverDestHost = connectionSocket.recv(addrLen).decode() # interpret the read bytes as a string
                serverDestPort = connectionSocket.recv(2) # the next two bytes identify the port
                serverDestPort = serverDestPort[0] * 256 + serverDestPort[1] # convert the value to an integer
            
                response = [5, 0, 0, 1, 0, 0, 0, 0, 0, 0] # default response
                # SOCKS version, received request, 0 (reserved byte), address type (IPv4), IPv4 and port
                # the last values are set to 0 as they are not relevant to the client for communication purposes
            
                connectionSocket.send(bytearray(response))
                return True, serverDestHost, serverDestPort
            else:
                print('The client', addr, 'indicates an unsupported or non-existent command! Unable to proceed.')
        else:
            print('The client', addr, 'indicates a protocol different from SOCKS5! Unable to proceed.')
        connectionSocket.close()
    except:
        pass
    return False, False, False

# MAIN
print('µSOCKS5 v1.0 - Ciro Ciampaglia')

serverPort = 1080 # Standard port for the protocol
serverSocket = socket(AF_INET,SOCK_STREAM)
serverSocket.bind(('',serverPort))
serverSocket.listen(10) # listen for connections (max. 10 incoming connections waiting before refusing new ones)
print('µSOCKS5 server is listening on port', serverPort, 'and is ready to receive connections...')

while True:
    readSockets, _, _ = select.select([serverSocket], [], [], 0)
    for sock in readSockets:
        if sock == serverSocket:
            try:
                connectionSocket, addr = serverSocket.accept() # establish a connection with the client
                #th = threading.Thread(target=handleRequest, args=(connectionSocket, addr))
                #th.start()
                if validateAuthentication(connectionSocket, addr):
                    success, serverDestHost, serverDestPort = readRequest(connectionSocket, addr)
                    if success: # the reading of the connection information from the client was successful
                        # now the proxy will act as a client towards the remote server
                        destSocket = socket(AF_INET, SOCK_STREAM)
                        destSocket.connect((serverDestHost,serverDestPort)) # open a socket to the remote server
                        #set non-blocking mode for both sockets
                        connectionSocket.setblocking(0)
                        destSocket.setblocking(0)

                        # add the tuple of sockets to the list of sockets to handle
                        connectionsToHandle.append((connectionSocket, destSocket))
            except:
                pass
            
    # for each tuple of sockets in the list of connections to handle
    for connectionSocket, destSocket in connectionsToHandle:
        connectionEnded = False
        try:
            # non blocking check if the sender socket has data to read
            data = connectionSocket.recv(1024)
            if not data:
                connectionEnded = True
            destSocket.send(data)
        except:
            pass
        try:
            # non blocking check if the receiver socket has data to read
            data = destSocket.recv(1024)
            if not data:
                connectionEnded = True
            connectionSocket.send(data)
        except:
            pass
        if connectionEnded:
            try:
                connectionSocket.close()
            except:
                pass
            try:
                destSocket.close()
            except:
                pass
            connectionsToHandle.remove((connectionSocket, destSocket))