import socket
import select

HEADER_LENGTH = 10
IP = ip_address
PORT = 1234

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)