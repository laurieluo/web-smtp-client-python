from colorama import Fore, init
from datetime import datetime
import json
init(autoreset=True)

def show_http_info(message, connectionSocket, isserver=True):

    if isserver:
        first_line = message[0].decode()
        header_dict = message[1]
        # Message type is server response
        print(Fore.GREEN + '[Server]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', 
              ':'.join([str(x) for x in connectionSocket.getsockname()]))
        # Print status line
        print('\t Status Line:')
        print(Fore.YELLOW + '\t HTTP version:', Fore.MAGENTA + first_line.split()[0])
        print(Fore.YELLOW + '\t Status Code:', Fore.MAGENTA + first_line.split()[1])
        print(Fore.YELLOW + '\t Phrase:', Fore.MAGENTA + first_line.split()[2])
        # Print header line
        print('\t Header Line:')
        print(Fore.YELLOW + '\t Server:', Fore.MAGENTA + header_dict['Server'])
        print(Fore.YELLOW + '\t Content-Type:', Fore.MAGENTA + header_dict['Content-Type'])
        print(Fore.YELLOW + '\t Content-Length:', Fore.MAGENTA + header_dict['Content-Length'])
        
    else: 
        b_lst = message.split(b'\r\n')
        b_lst = [x for x in b_lst if x != b'']
        first_line = b_lst[0].decode()
        # Message type is client request.
        method = first_line.split()[0]
        if method == 'GET':
            header_line = [x.decode() for x in b_lst[1:]]
        else:
            header_line = [x.decode() for x in b_lst[1:-1]] 
        header_dict = {elem.split(': ')[0]: elem.split(': ')[1] for elem in header_line}
        print(Fore.CYAN + '[Client]', Fore.LIGHTBLUE_EX + '['+str(datetime.now())+']', 
              ':'.join(str(x) for x in connectionSocket.getpeername()))
        # Print request line
        print('\t Request Line:')
        print(Fore.YELLOW + '\t Method:', Fore.MAGENTA + method)
        print(Fore.YELLOW + '\t Requested file:', Fore.MAGENTA + first_line.split()[1])
        print(Fore.YELLOW + '\t HTTP version:', Fore.MAGENTA + first_line.split()[2])
        # Print header lines
        print('\t Header Line:')
        print(Fore.YELLOW + '\t Host:', Fore.MAGENTA + header_dict['Host'])
        print(Fore.YELLOW + '\t Connection:', Fore.MAGENTA + header_dict['Connection'])
        if method == 'POST':
            print(Fore.YELLOW + '\t Content-Type:', Fore.MAGENTA + header_dict['Content-Type'])
            print(Fore.YELLOW + '\t Content-Length:', Fore.MAGENTA + header_dict['Content-Length'])
        if 'sec-ch-ua' in header_dict.keys():
            print(Fore.YELLOW + '\t Broswer:', Fore.MAGENTA + header_dict['sec-ch-ua'])
        if 'sec-ch-ua-platform' in header_dict.keys():
            print(Fore.YELLOW + '\t Platform:', Fore.MAGENTA + header_dict['sec-ch-ua-platform'])
        print(Fore.YELLOW + '\t Accept:', Fore.MAGENTA + header_dict['Accept'])
        print(Fore.YELLOW + '\t Accept-Language:', Fore.MAGENTA + header_dict['Accept-Language'])
        print(Fore.YELLOW + '\t Accept-Encoding:', Fore.MAGENTA + header_dict['Accept-Encoding'])
        # Print Bodylines
        if method == 'POST':
            print('\t Body:')
            mail_dict = json.loads(b_lst[-1].decode())
            mail_list = [x[:-1] for x in mail_dict['email']]
            print(Fore.YELLOW + '\t Mail-To:', Fore.MAGENTA + str(mail_list))
            print(Fore.YELLOW + '\t Subject:', Fore.MAGENTA + mail_dict['subject'])
            print(Fore.YELLOW + '\t Message:', Fore.MAGENTA + mail_dict['message'])
