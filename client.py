import socket
import threading
import time
import collections  # for deque
import heapq    # priority-queue
import re
import sys

def incrementClk():
    global myClk
    with clkLock:
        myClk += 1
    return myClk

def handleStdIn():
    # Handle std input
    while True:
        stdin = input()

        if stdin == "exit":
            print("Exiting...")
            sys.exit()

        elif re.match("write [a-z ]+", stdin):
            sentence = stdin[6:]
            sentenceQueue.append(sentence)
            print(f"The sentence {sentence} has been pushed to the queue")

        else:
            print("Invalid command.")

def handleClientRequests(clientConn):
    while True:
        msg = clientConn.recv(1024).decode()
        print(f"Received {msg} from client with port {clientConn.getsockname()[1]}")
        incrementClk()
        if re.match("request-<[0-9]+,[0-9]+>", msg): # Request format is "request-<clientClk,clientPID>"
            # [TODO] Parse & Push (clientClk, clientPID) to the reqQueue
            incrementClk()
            simPropDelay()
            clientConn.send("reply".encode() )
            print(f"Sent reply to client with port {clientConn.getsockname()[1]}")

        #elif [TODO] Handle "release" from client:
            # Print received release
            # Pop head of reqQueue?

        else:
            print(f"Error: Received a non-request from client at port {clientConn.getsockname()[1]}. The message was {msg}.")

def handleClientConnections():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientSocketIn:
        clientSocketIn.bind( (socket.gethostname(), 9000 + myPID) )  # Bind to port 9000 + myPID
        clientSocketIn.listen()
        print(f"Bound client in-port to port {clientSocketIn.getsockname()[1]}")

        # Poll client connections in
        while True:
            clientConn, clientAddr = clientSocketIn.accept()
            threading.Thread(target=handleClientRequests, args=[clientConn], daemon=True).start()
            print(f"Received connection from client at port {clientAddr[1]}")

def simPropDelay():
    time.sleep(2)

# def broadcastRequests():
#     # [TODO] Send requests to every client with our Logical lamport time and PID piggybacked

# def waitForReplies():
#     # [TODO] Wait until numClients-1 replies have been received

# def waitForTurn():
#     # [TODO] Wait until we are at the top of the request queue

def writeSentencesToServer():
    # [TODO] Finally, we have access to the shared resource, so send it the queued sentences
    pass


if len(sys.argv) != 3:
    print(f"Usage: python {sys.argv[0]} <PID> <server_port>")
    sys.exit()

# Initialize cmdline-arg constants
myPID = int(sys.argv[1])
fileServerAddr = (socket.gethostname(), int(sys.argv[2]) )

# Initialize global vars
myClk = 1                               # Lamport logical clock
sentenceQueue = collections.deque([])   # (Synchronous) Queue storing sentences to write to the file server
reqQueue = []                           # Min-heap storing requests for Lamport's Distr. Soln. protocol
clkLock = threading.RLock()             # RLock for the clock
reqQueueLock = threading.RLock()        # [TODO] Not sure if this is needed

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
numClients = 2
for i in range(numClients - 1):
    clientPort = 9001 + ( (myPID + i) % numClients)
    clientSocketOut = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocketOut.connect( (socket.gethostname(), clientPort) )
    print("Connected to client with port", clientPort, "at hostname", socket.gethostname() )
    clientSocketOutList.append(clientSocketOut)

print("List of client sockets out:")
print(clientSocketOutList)

# Start a thread to concurrently handle std input
threading.Thread(target=handleStdIn, daemon=True).start()

# End of setup
# Now, the main thread handles accessing the shared resource

while True:
    if len(sentenceQueue):  # Sentence queue not empty
        # Broadcast request to other clients
        heapq.heappush(reqQueue, (myClk, myPID) )   # Push my own request to the queue first
        incrementClk()
        simPropDelay()
        for clientSocketOut in clientSocketOutList:
            clientSocketOut.send(f"request-<{myClk},{myPID}>".encode() )
            print(f"Sent request-<{myClk},{myPID}> to client at port {clientSocketOut.getsockname()[1]}")

        # Wait for numClients-1 replies
        for clientSocketOut in clientSocketOutList:
            msg = clientSocketOut.recv(1024).decode()
            if msg == "reply":
                print(f"Received reply from client at port {clientSocketOut.getsockname()[1]}")
                continue
            else:
                print(f"Error: received non-reply from client at port {clientSocketOut.getsockname()[1]}")
                print("Exiting...")
                sys.exit()

        # Wait for our turn in the request queue
        while not(myPID == reqQueue[0][1]):
            pass

        # Access the shared resource
        writeSentencesToServer()

        # Broadcast release to other clients
        for clientSocketOut in clientSocketOutList:
            incrementClk()  # [TODO] Not sure if supposed to increment for a sending release
            simPropDelay()
            clientSocketOut.send("release".encode() )
            print(f"Sent release to client at port {clientSocketOut.getsockname()[1]}")
