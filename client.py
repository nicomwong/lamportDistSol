import socket
import threading
import sys

def handleClientRequests(clientConn):
    while True:
        msg = clientConn.recv(1024)
        # Process message

def handleClientConnections():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientSocketIn:
        clientSocketIn.bind( (socket.gethostname(), 9000 + myPID) )  # Bind to port 9000 + myPID
        clientSocketIn.listen()
        print(f"Bound client in-port to port {clientSocketIn.getsockname()[1]}")

        # Poll client connections in
        while True:
            clientConn, clientAddr = clientSocketIn.accept()
            threading.Thread(target=handleClientRequests, args=[clientConn])
            print(f"Client {myPID} received connection from client at port {clientAddr[1]}")

if len(sys.argv) != 3:
    print(f"Usage: python {sys.argv[0]} <PID> <server_port>")
    sys.exit()

myPID = int(sys.argv[1])
fileServerAddr = (socket.gethostname(), int(sys.argv[2]) )

# # Connect to file server
# fileServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# fileServerSocket.connect(fileServerAddr)

# Open socket to listen to other clients
threading.Thread(target=handleClientConnections, daemon=True).start()

# Wait until "connect" has been input to stdin
msg = ""
while msg != "connect":
    msg = input()
    if msg != "connect":
        print("Wrong message. The first message must be \"connect\"")

# Connect to other clients and store the connections in a list
# for numClients = 3:
# other client is 9001 + (myPID % 3)
# another client is 9001 + ((myPID + 1) % 3)
clientSocketOutList = []
numClients = 3
for i in range(numClients - 1):
    clientSocketOut = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("attempting to connect to client with port", 9001 + ( (myPID + i) % numClients), "at hostname", socket.gethostname() )
    clientSocketOut.connect( (socket.gethostname(), 9001 + ( (myPID + i) % numClients) ) )
    clientSocketOutList.append(clientSocketOut)

print("List of client sockets out:")
print(clientSocketOutList)