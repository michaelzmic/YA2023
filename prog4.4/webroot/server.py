import os
import socket, threading

exts_txt = ['.js', '.txt', '.css']
exts_bin = ['.html', '.jpg', '.gif', '.ico']

moved_302 = {'A/dog.jpg': 'B/dog.jpg', 'B/dog.jpg': 'B/dog2.jpg'}

exit_all = False

PROTOCOL = 'HTTP1.1'

DEBUG_HTTP = True


def http_send(s, reply_header, reply_body):
    reply = reply_header.encode()
    if reply_body != b'':
        try:
            body_length = len(reply_body)
            reply_header += 'Content-Length: ' + str(body_length) + '\r\n' + '\r\n'
            reply = reply_header.encode() + reply_body
        except Exception as e:
            print(e)
    else:
        reply += b'\r\n'
    s.send(reply)
    print('SENT:', reply[:min(100, len(reply))])


def http_recv(sock, BLOCK_SIZE=8192):

    data = b''
    rnrn_pos = -1
    while rnrn_pos == -1:
        _d = sock.recv(BLOCK_SIZE)
        print ("len d", len(_d))
        if _d == b'':
            return b'', None
        data += _d
        rnrn_pos = data.find(b'\r\n\r\n')

    rnrn_pos +=4
    body = b''
    print("data ", data)
    if b'Content-Length: ' in data[:rnrn_pos]:

        print("1")
        len_pos = data[:rnrn_pos].find(b'Content-Length: ') + 16
        len_pos2  = data[len_pos:rnrn_pos].find(b'\r\n') + len_pos
        body_size = int(data[len_pos:len_pos2])
        print("2")
        if len(body)> body_size:
            body = data[rnrn_pos:]
        print("3")
        while len(body) < body_size:
            _d = sock.recv(min(BLOCK_SIZE,body_size - len(body)))
            if _d==b'':
                return b'',None
            body += _d
        print("4")
    if DEBUG_HTTP:

        print('\nRECV-' + str(len(data[:rnrn_pos]) + len(body)) + '<<<',data[:rnrn_pos], '\tBody(first100):',body[:100] )
    return data[:rnrn_pos],body


def build_ERR_answer(err_code,file_name):
    answer = 'HTTP/1.1 ' + err_code + ' not ok\r\n'
    body = b'<html> <body> <b>michael</b> said that file: '+ file_name.encode() \
           +b' wasn\'t found </body></html>'
    return answer , body

def get_file_data(requested_file):
    if not os.path.isfile(requested_file):
        return build_ERR_answer('404',requested_file)
    with open(requested_file,'rb') as f:
        data = f.read()
    headers = 'HTTP/1.1 200 OK\r\n'
    return headers,data


def get_default_file():
    if not os.path.isfile('index.html'):
        return build_ERR_answer('404','index.html')
    with open('index.html','rb') as f:
        data = f.read()
    headers = 'HTTP/1.1 200 OK\r\n'
    return headers,data

def handle_request(request_header, body):
    request_header =request_header.decode()
    lines = request_header.split('\r\n')
    first_line = lines[0]
    parts = first_line.split(' ')
    url = parts[1]
    if url=='/':
        reply_header,replt_body = get_default_file()
    else:
        resource = url[1:]
        print ('----------------------------------------')
        print (resource)
        print ('----------------------------------------')
        if resource[:14] == 'calculate-next':
            num = int(resource[19:] ) +1
            num = str(num)
            return 'HTTP/1.1 200 OK\r\n', num.encode()
        elif resource[:14] == 'calculate-area':
            parts = resource[15:].split('&')
            h = parts[0][7]
            b = parts[1][6]
            print ('height:'+h)
            area = float(h)*float(b)/2
            area = str(area)
            print(area +'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            return 'HTTP/1.1 200 OK\r\n', area.encode()
        reply_header, replt_body = get_file_data(resource)
    return reply_header,replt_body



def handle_client(s_clint_sock, tid, addr):
    global exit_all
    print('new client arrive', tid, addr)
    while not exit_all:
        request_header, body = http_recv(s_clint_sock)
        if request_header == b'':
            print('seems client disconected, client socket will be close')
            break
        else:
            reply_header, reply_body = handle_request(request_header, body)
            if PROTOCOL == "HTTP1.0":
                reply_header += "Connection': close\r\n"
            else:
                reply_header += "Connection: keep-alive\r\n"
            http_send(s_clint_sock, reply_header, reply_body)
            if PROTOCOL == "HTTP1.0":
                break
    print("Client", tid, "Closing")
    s_clint_sock.close()


def main():
    global exit_all
    server_socket = socket.socket()
    server_socket.bind(('0.0.0.0', 80))
    server_socket.listen(5)
    threads = []
    tid = 1
    while True:
        try:
            print('\nbefore accept')
            client_socket, addr = server_socket.accept()
            t = threading.Thread(target=handle_client, args=(client_socket, tid, addr))
            t.start()
            threads.append(t)
            tid += 1

        except socket.error as err:
            print('socket error', err)
            break
    exit_all = True
    for t in threads:
        t.join()

    server_socket.close()
    print('server will die now')


if __name__ == "__main__":
    main()


