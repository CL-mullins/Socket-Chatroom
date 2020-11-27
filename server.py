import socket
import select


HEADER_LENGTH = 10
IP = "127.0.0.1"
PORT = 1234

#Create a socket
#socket.AF_INET means address family, IPv4
#socket.SOCK_STREAM - TCP, connection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP Packets
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#SO_ - socket option
#SOL_ - socket option level
#Sets REUSEADDR (as a socket option) to 1 on socket
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind, so server informs operating system that it's going to use given IP and port
# For a server using 0.0.0.0 means to listen on all available interfaces, useful to connect locally to 127.0.0.1 and remotely to LAN interface IP
server_socket.bind((IP, PORT))

#Makes server listen to new connections
server_socket.listen()

#list of sockets for select.select()
sockets_list = [server_socket]

# List of connected clients - socket as a key, user header and name as data
clients = {}

#Handles message receiving
def recieve_message(client_socket):
    try:
        #Receive our "header" containing message length, it's size is defined and constant
        message_header = client_socket.recv(HEADER_LENGTH)

        # If we received no data, client closed a connection, for example using socket.close() or socket.shutdown(socket.shut(RDWR)
        if not len(message_header):
            return False

        #Convert header to int value
        message_length = int(message_header.decode('utf-8').strip())
        
        #Return an object of message header and message data
        return {'header': message_header, 'data': client_socket.recv(message_length)}

    except:
        #If we are here, client closed connection violently
        #or just lost it's connection
        #socket.close() also invokes socket.shutdown(socket.shut(RDWR) which sends information about closing the socket (shutdown read/write)
        return False


while True:
    #Calls Unix select() system call or Windows select() WinSock call with three parameters:
    # -rlist - sockets to be monitored for incoming data
    # -wlist - sockets for data to be sent to (checks if for example buffers are not full and socket is ready to send some data)
    # -xlist - sockets to be monitored for exceptions (we want to monitor all sockets for errors, so we can use rlist)
    #Return lists:
    # - reading - sockets we received some data on (that way we don't have to check sockets manually)
    # - writing - sockets ready for data to be sent thru them
    # - errors - sockets with some exceptions
    # This is a blocking call, code execution will "wait" here and "get" notified in case any action should be taken
    read_sockets, _, exception_sockets = select.select(
        sockets_list, [], sockets_list)

    #Iterate over notified sockets
    for notified_socket in read_sockets:

        #If notified socket is a server socket - new connection, accept it
        if notified_socket == server_socket:

            #Accept new connection
            #That gives us new socket - client socket, connected to this given client only, it's unique for that client
            #The other returned object is ip/port set
            client_socket, client_address = server_socket.accept()

            # Client should send his name right away, receive it
            user = recieve_message(client_socket)
            # If False - client disconnected before he sent his name
            if user is False:
                continue

            #Add accepted socket to select.select() list
            sockets_list.append(client_socket)

            #Also save username and username header
            clients[client_socket] = user

            print(
                f"Accepted new connection from {client_address[0]}:{client_address[1]} username={user['data'].decode('utf-8')}")

        #Else existing socket is sending a message
        else:

            #Receive message
            message = recieve_message(notified_socket)

            # If False, client disconnected, cleanup
            if message is False:
               print(
                   "Closed connection from {client[notified_socket]['data'].decode('utf-8')}")
               #Remove from list for socket.socket()
               sockets_list.remove(notified_socket)
               #Remove from our list of users
               del clients[notified_socket]
               continue

            #Get user by notified socket, so we will know who sent the message
            user = clients[notified_socket]
            print(print(f'Received message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}'))

            #Iterate over connected clients and broadcast message
            for client_socket in clients:

                #But don't send it to sender
                if client_socket != notified_socket:

                    #Send user and message (both with their headers)
                    #We are reusing here message header sent by sender, and saved username header send by user when he connected
                    client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])

        #It's not really necessary to have this, but will handle exceptions just in case
        for notified_socket in exception_sockets:

            #remove from list for socket.socket()
            sockets_list.remove(notified_socket)

            #Remove from our list of users
            del clients[notified_socket]







