import socket
import sys
import time

print("Starting")

if len(sys.argv) != 3:
    print(f"Usage: python {sys.argv[0]} <PID> <server_port>")
    sys.exit()

myPID = sys.argv[1]
fileServerAddr = (socket.gethostname(), int(sys.argv[2]) )

# Connect to file server
fileServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
fileServerSocket.connect(fileServerAddr)

for count in range(5):
    print(f"Sleeping... {count}")
    time.sleep(1)

print("Done sleeping")

print("Is there anything in the file server socket?")
print(fileServerSocket.recv(1024).decode() )