import socket
import threading
import re
import sys

def incrementClk():
    global myClk
    with clkLock:
        myClk += 1
    return myClk

def handleStdIn():
    # [TODO] Handle std input

def handleClientRequests(clientConn):
    while True:
        msg = clientConn.recv(1024).decode()
        incrementClk()
        if re.match("request-<[0-9]+,[0-9]+>"): # Request format is "request-<clientClk,clientPID>"
            # Process request
            # [TODO] Push (clientClk, clientPID) to the reqQueue
            clientConn.send("reply")
            incrementClk()

        else:
            print(f"Error: Received a non-request from client at port {clientConn.getsockname[1]}. The message was {msg}.")

def handleClientConnections():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientSocketIn:
        clientSocketIn.bind( (socket.gethostname(), 9000 + myPID) )  # Bind to port 9000 + myPID
        clientSocketIn.listen()
        print(f"Bound client in-port to port {clientSocketIn.getsockname()[1]}")

        # Poll client connections in
        while True:
            clientConn, clientAddr = clientSocketIn.accept()
            threading.Thread(target=handleClientRequests, args=[clientConn])
            print(f"Received connection from client at port {clientAddr[1]}")

def broadcastRequests():
    # [TODO] Send requests to every client with our Logical lamport time and PID piggybacked

def waitForReplies():
    # [TODO] Wait until numClients-1 replies have been received

def waitForTurn():
    # [TODO] Wait until we are at the top of the request queue

def writeToFileServer():
    # [TODO] Finally, we have access to the shared resource, so send it the queued sentences


if len(sys.argv) != 3:
    print(f"Usage: python {sys.argv[0]} <PID> <server_port>")
    sys.exit()

# Initialize cmdline-arg constants
myPID = int(sys.argv[1])
fileServerAddr = (socket.gethostname(), int(sys.argv[2]) )

# Initialize global vars
myClk = 1                   # Lamport logical clock
sentenceQueue = []          # (Synchronous) Queue storing sentences to write to the file server
reqQueue = []               # Min-heap storing requests for Lamport's Distr. Soln. protocol
clkLock = threading.RLock() # RLock for the clock
reqQueueLock = threading.RLock()    # [TODO] Not sure if this is needed

# Start a thread to concurrently handle std input
threading.Thread(target=handleStdIn, daemon=True).start()

# # Connect to file server
# fileServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# fileServerSocket.connect(fileServerAddr)

# Start a thread to concurrently accept the other clients' connections
threading.Thread(target=handleClientConnections, daemon=True).start()

# Wait until "connect" has been input to stdin
msg = ""
while msg != "connect":
    msg = input()
    if msg != "connect":
        print("Wrong message. The first message must be \"connect\"")

# Connect to other clients and store the connections in a list
# Client PIDs should be a prefix of the sequence 1, 2, 3, ...
# if numClients = 3:
#   other client is 9001 + (myPID % 3)
#   another client is 9001 + ( (myPID + 1) % 3)
clientSocketOutList = []
numClients = 3
for i in range(numClients - 1):
    clientPort = 9001 + ( (myPID + i) % numClients)
    clientSocketOut = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocketOut.connect( (socket.gethostname(), clientPort) )
    print("Connected to client with port", clientPort, "at hostname", socket.gethostname() )
    clientSocketOutList.append(clientSocketOut)

print("List of client sockets out:")
print(clientSocketOutList)