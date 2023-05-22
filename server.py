from socket import *
from weblib import *
from smtplib import send_email
from colorama import Fore, init
from datetime import datetime
from pathlib import Path
import json
import argparse
init(autoreset=True)

# Fetch args
parser = argparse.ArgumentParser(description='Please type server name and port')
parser.add_argument('--name', type=str, default='127.0.0.1')
parser.add_argument('--port', type=int, default=8080)
args = parser.parse_args()

# Prepare to log emails
log_file = 'log/' + datetime.now().strftime('%Y%m%d%H%M%S') + '.json'

# Prepare a server socket
serverPort = args.port
serverName = args.name
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind((serverName, serverPort))
serverSocket.listen(1)
print(Fore.RED + '!!!Server started at:', 'http://'+serverName+':'+str(serverPort)+'/index.html')

# Start to listen
while True:

    # Set default HTTP message.
    response_status = 'HTTP/1.1 200 OK\r\n'
    response_headers = {'Content-Type': 'text/html; charset=utf-8',
                        'Server': 'Python HTTP Server' }

    # Establish the connection.
    print(Fore.GREEN + '[Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', Fore.YELLOW + 'Waiting for new connection...')
    connectionSocket, addr = serverSocket.accept()

    try:
        # Retrieve HTTP message from client.
        message = connectionSocket.recv(7168) #7KB
        show_http_info(message, connectionSocket, isserver=False)

        # Get the requested file name.
        method = message.split()[0]
        filename = message.split()[1][1:]

        # Judge request method.
        if method == b'GET':
            # Read file to response_body.
            with open(filename, 'rb') as f:
                response_body = f.read()

            # Set the HTTP header fields.
            if filename.endswith(b'.css'):
                response_headers['Content-Type'] = 'text/css; charset=utf-8'
            elif filename.endswith(b'.js'):
                response_headers['Content-Type'] = 'text/javascript; charset=utf-8'
            elif filename.endswith(b'.jpg') or filename.endswith(b'.png'):
                response_headers['Content-Type'] = 'image/jpeg'
            response_headers['Content-Length'] = str(len(response_body))

            # Send the payload of the HTTP message.
            response_headers_str = ''.join('%s: %s\r\n' % (k, v) for k, v in response_headers.items())
            response_data = response_status.encode('utf-8') + response_headers_str.encode('utf-8') + b'\r\n' + response_body
            connectionSocket.sendall(response_data)
            show_http_info([response_status, response_headers], connectionSocket, isserver=True)

        elif method == b'POST':
            mail_info = json.loads(message.split(b'\r\n')[-1].decode())
            # Remove the last 'X' in the email address.
            mail_info['email'] = [x[:-1] for x in mail_info['email']]
            existence, send, auth_error = send_email(mail_info['username'], mail_info['password'], mail_info, safe=mail_info['ssl'])
            
            if not auth_error:
                # Return Send status.
                response_str = '\n'.join([a + ': ' + ('Success.' if b else 'Failed.') for a, b in zip(send.keys(), send.values())]) + '\n'
                response_str += '\n'.join([a + ': ' + 'Not exist.' for a, b in zip(existence.keys(), existence.values()) if b == False])
                response_body = response_str.encode('utf-8')
                response_headers['Content-Length'] = str(len(response_body))
                response_headers_str = ''.join('%s: %s\r\n' % (k, v) for k, v in response_headers.items())
                response_data = response_status.encode('utf-8') + response_headers_str.encode('utf-8') + b'\r\n' + response_body
                connectionSocket.sendall(response_data)
                show_http_info([response_status, response_headers], connectionSocket, isserver=True)

                # Log emial to file
                mail_info['time'] = str(datetime.now())
                try:
                    with open(log_file, 'r') as file:
                        existing_data = json.load(file)
                except FileNotFoundError:
                    existing_data = []
                existing_data.append(mail_info)
                with open(log_file, 'w') as file:
                    json.dump(existing_data, file)

            else:
                # Auth error, return 400 Bad Request.
                response_status = 'HTTP/1.1 400 Bad Request\r\n'
                response_headers['Content-Length'] = '0'
                response_headers_str = ''.join('%s: %s\r\n' % (k, v) for k, v in response_headers.items())
                response_data = response_status.encode('utf-8') + response_headers_str.encode('utf-8') + b'\r\n'
                connectionSocket.sendall(response_data)
                show_http_info([response_status, response_headers], connectionSocket, isserver=True)

        connectionSocket.close() 

    except IOError:
        # Send response message for file not found
        connectionSocket.send("HTTP/1.1 404 Not Found\r\n".encode())

        # Close client socket
        connectionSocket.close()

serverSocket.close()
