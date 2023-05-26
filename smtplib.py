import base64
import re
import ssl
from socket import *
from colorama import Fore, init
from datetime import datetime
from warnings import filterwarnings
import dns.resolver
import threading
init(autoreset=True)

#创建字典，存储不同邮件服务器的sslsmtp端口和地址

serverbase={'qq.com':'smtp.qq.com','outlook.com':'smtp.live.com','gmail.com':'smtp.gmail.com',
           '163.com':'smtp.163.com','foxmail.com':'smtp.163.com','126.com':'smtp.126.com'}
smtpbase={'qq.com':587,'outlook.com':587,'gmail.com':587,
           '163.com':465,'foxmail.com':465,'126.com':465}

#作为客户端，用SMTP发送邮件给邮件服务器
def send_email(username, password, email, safe):
    #初始化
    existence = {}
    send = {}
    sendDomain = username.split('@')[1]
    auth_error = False

    for i in range(len(email['email'])):
        print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', Fore.YELLOW + 'Prepare to send to', Fore.YELLOW + email['email'][i])
        #检查接收邮件的地址有效性
        receiveDomain = email['email'][i].split('@')[1]
        if not check(receiveDomain, username, email['email'][i]):
            existence.update({email['email'][i]: False})
            continue

        existence.update({email['email'][i]: True})
        if sendDomain in serverbase.keys():
            mailServer = serverbase[sendDomain]
        else:
            mailServer = sendDomain

        if safe and sendDomain in smtpbase.keys():
            serverPort = smtpbase[sendDomain]  # ssl SMTP各邮件服务器有所差别
        else:
            serverPort = 25   # 普通SMTP都使用25号端口

        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.connect((mailServer, serverPort)) # 初始化TCP服务器连接
        print (Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[C] Try to connect to SMTP server...')
        recvShake = clientSocket.recv(1024).decode()
        print (Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[S] Connected to:', recvShake.rstrip())
        if recvShake[:3] != '220':
            print (Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[S] 220 reply not received from server.')

        clientSocket.sendall('HELO Client\r\n'.encode()) #\r\n是SMTP等传输协议中固定的格式
        print (Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[C] Saying Hello to SMTP server...')
        recvHelo = clientSocket.recv(1024).decode()
        print (Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[S] Received:', recvHelo.rstrip())
        if recvHelo[:3] != '250':
            print (Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[S] 250 reply not received from server.')

        if safe:
            #ssl加密
            clientSocket.send('STARTTLS\r\n'.encode())
            print (Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[C] Try to establish ssl connection...')
            recvCmd=clientSocket.recv(1024).decode()
            print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[S]',Fore.GREEN + 'SSL enabled', recvCmd.rstrip())

            filterwarnings('ignore')
            sslClientSocket=ssl.wrap_socket(clientSocket)
            send_status, auth_error = socket_send(sslClientSocket, username, password, email, i)
        else:
            send_status, auth_error = socket_send(clientSocket, username, password, email, i)

        if send_status and not auth_error:
            send.update({email['email'][i]: True})
        elif not send_status and not auth_error:
            send.update({email['email'][i]: False})
        else:
            return existence, send, auth_error


    return existence, send, auth_error


def socket_send(socket, username, password, email, i):
    send_situation = False
    auth_error = False

    # AUTH LOGIN
    socket.send('AUTH LOGIN\r\n'.encode())
    print (Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[C] Try to login...')
    recvLogin = socket.recv(1024).decode()
    print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[S] Please enter username:', recvLogin.rstrip())
    if recvLogin[:3] != '334':
        print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[S] Fail: 334 reply not received from server.')

    # Username
    socket.send(base64.b64encode(username.encode()) + '\r\n'.encode()) 
    print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[C] Send Username...')
    recvName = socket.recv(1024).decode()
    print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[S] Please enter password:', recvName.rstrip())
    if '334' != recvName[:3]:
        print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[S] Fail: 334 reply not received from server')
        auth_error = True
        return send_situation, auth_error

    # Password
    socket.send(base64.b64encode(password.encode()) + '\r\n'.encode())  
    print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[C] Send Password...')
    recvPass = socket.recv(1024).decode()
    print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[S]', recvPass.rstrip())
    if '235' != recvPass[:3]:
        print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[S] Fail: 235 reply not received from server')
        auth_error = True
        return send_situation, auth_error

    # MAIL FROM
    socket.sendall(('MAIL FROM:<' + format(username) + '>\r\n').encode())  
    print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[C] Send MAIL FROM...')
    MailFromMessage = socket.recv(1024).decode()
    print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[S] ' + MailFromMessage.rstrip())

    # RCPT TO
    socket.sendall(('RCPT TO:<' + format(email['email'][i]) + '>\r\n').encode())  
    print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[C] Send RCPT TO...')
    RCPTMessage = socket.recv(1024).decode()
    print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[S] ' + RCPTMessage.rstrip())

    # DATA
    socket.send('DATA\r\n'.encode())  
    DATAMessage = socket.recv(1024).decode()
    print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[C] Prepare to send MAIL CONTENT...')
    print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[S] ' + DATAMessage.rstrip())

    # Send message
    subject = email['subject']
    contentType = "text/plain"
    msg = email['message']
    message = 'from:' + username + '\r\n'
    message += 'to:' + email['email'][i] + '\r\n'
    message += 'subject:' + subject + '\r\n'
    message += 'Content-Type:' + contentType + '\t\n'
    message += msg + '\r\n'
    socket.sendall(message.encode())
    print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[C] Send MAIL CONTENT...')

    # End of message
    endMsg = '\r\n.\r\n'
    socket.send(endMsg.encode())
    print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[C] End of MAIL CONTENT...')
    endRECV = socket.recv(1024).decode()
    print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[S] ' + endRECV.rstrip())
    code = 0
    match = re.match(r'\d+', endRECV)
    if match:
        code = int(match.group())
    if code == 250:
        send_situation=True
    else:
        send_situation=False

    # QUIT
    socket.sendall('QUIT\r\n'.encode())
    print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[C] End connection...')
    quitMessage = socket.recv(1024).decode()
    print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', '[S] ' + quitMessage.rstrip())

    # Close connection
    socket.close()
    return send_situation, auth_error

def check(domain, username, addressToVerify):
    print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', Fore.YELLOW + 'Checking the email is valid or not...')
    username = 'corn@bt.com'
    code = 0
    try:
        records = dns.resolver.resolve(domain, 'MX')
        mxRecord = records[0].exchange
        mxRecord = str(mxRecord)
    except:
        print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', Fore.CYAN + 'Email address is unknown, try to send!')
        return True


    def wait_with_timeout():
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.connect((mxRecord, 25))
        recvShake = clientSocket.recv(1024).decode()

        clientSocket.sendall('HELO Client\r\n'.encode())
        recvHelo = clientSocket.recv(1024).decode()

        clientSocket.sendall(('MAIL FROM:<' + format(username) + '>\r\n').encode())
        MailFromMessage = clientSocket.recv(1024).decode()

        clientSocket.sendall(('RCPT TO:<' + format(addressToVerify) + '>\r\n').encode())
        RCPTMessage = clientSocket.recv(1024).decode()
        match = re.match(r'\d+', RCPTMessage)

        if match:
            nonlocal code
            code = int(match.group())

    thread = threading.Thread(target=wait_with_timeout)
    thread.start()
    thread.join(8)
    
    if code == 250:
        print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', Fore.GREEN + 'Email address is valid!')
        return True
    elif thread.is_alive():
        print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', Fore.CYAN + 'Email address is unknown, try to send!')
        return True
    else:
        print(Fore.MAGENTA + '[SMTP Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', Fore.RED + 'Email address is invalid! Skipped.')
        return False


