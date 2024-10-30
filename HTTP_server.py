import argparse
import socket 
import threading
from pathlib import *

buffer = 1024
encoding = "utf-8"
content_type = "text/plain"


def POST_response(file_path, message, path, body):
    file_path = Path(file_path)

    try:
        with file_path.open('w', encoding=encoding) as f:
            f.write(body)
        return (f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: {content_type}\r\n"
                f"Content-Length: {len(body)}\r\n\r\n"
                f"File written successfully to {file_path}")
    except Exception as e:
        return (f"HTTP/1.1 500 Internal Server Error\r\n"
                f"Content-Type: text/plain\r\n"
                f"Content-Length: {len(str(e))}\r\n\r\n"
                f"Error writing file: {str(e)}")


def file_response(file_content, content_type):
    print(file_content)

    return (f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(file_content)}\r\n\r\n"
            f"{file_content}")


def user_agent_response(path, message):
    user_agent = ""

    for line in message.split("\r\n"):
        if line.startswith("User-Agent:"):
            user_agent = line.split(": ", 1)[1]
            break
    # print(user_agent)
    return f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length:{len(user_agent)}\r\n\r\n{user_agent}"


def echo_response(path):
    if path.startswith("/echo"):
        echo = '/'.join(path.split('/')[2:])
        return f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(echo)}\r\n\r\n{echo}"

    return "HTTP/1.1 404 Not Found\r\n\r\n"


def solution(client_socket, address, directory):
    print(f"connection has been established with {address}")

    data = client_socket.recv(buffer)
    message = data.decode(encoding)

    print(f"receive from client : {message}")

    path = message.split("\r\n")[0].split(' ')[1]
    req_type = message.split("\r\n")[0].split(' ')[0]
    req_lines = message.split("\r\n")

    for line in req_lines:
        if line.startswith("User-agent:"):
            user_agent = line.split(' ')[1]
            break

    if req_type == "POST":
        body = req_lines[-1]
        file_path = Path(directory) / path.split('/')[-1]
        response = POST_response(file_path, message, path, body)
        client_socket.sendall(response.encode(encoding))
        client_socket.close()
        return

    if path.startswith("/files"):
        file_path = Path(directory) / path.split('/')[-1]
        if file_path.is_file():
            response = file_response(file_path.read_text(), "application/octet-stream")
        else:
            response = 'HTTP/1.1 404 Not Found\r\n\r\n'

    elif path.startswith("/echo"):
        response = echo_response(path)

    elif path.startswith("/user-agent"):
        response = user_agent_response(path, message)
        # client_socket.sendall(user_agent_response(path, message).encode(encoding))

    elif path == "/":
        response = 'HTTP/1.1 200 OK\r\n\r\n'

    else:
        response = 'HTTP/1.1 404 Not Found\r\n\r\n'
        # client_socket.sendall(response.encode(encoding))

    client_socket.sendall(response.encode(encoding))
    client_socket.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=str)
    args = parser.parse_args()

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    server_socket.listen()

    try:
        while True:
            client_socket, address = server_socket.accept()
            client_thread = threading.Thread(target=solution, args=(client_socket, address, args.directory))
            client_thread.start()

    except KeyboardInterrupt:
        print("ending process")


if __name__ == "__main__":
    main()
