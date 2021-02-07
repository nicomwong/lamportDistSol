import socket
import threading
import time
import json
import queue    # Thread-safe
import re
import sys

def incrementClk():
    global myClk
    with clkLock:
        myClk += 1
        print(f"---Incremented clock to {myClk}---")

def updateClk(otherClk):
    # For maintaining the invariant (if a happens-before b, then clk(A) < clk(B) )
    global myClk
    with clkLock:
        myClk = max(myClk - 1, otherClk) + 1    # myClk - 1 since myClk stores the time for the next event
        print(f"---Updated clock to {myClk}---")

def handleStdIn():
    # Handle std input
    while True:
        stdin = input()

        if stdin == "exit":
            print("Exiting...")
            sys.exit()

        elif re.match("write '[a-z. ]+'", stdin):
            sentence = stdin[7:-1]
            sentenceQueue.put(sentence)
            print(f"The sentence, '{sentence}', has been pushed to the sentenceQueue")
            incrementClk()

        else:
            print("Invalid command.")

def handleClientMsgsIn(clientConn):
    while True:
        msg = clientConn.recv(1024).decode()
        print(f"Received {msg} from client with port {clientConn.getpeername()[1]}")

        if re.match("request-\[[0-9]+, [0-9]+]", msg):  # Received request
            reqOrder = tuple(json.loads(msg[8:]) )  # Parse the piggybacked order (clk, PID)
            reqQueue.put(reqOrder)  # Push the request to the prio-queue
            print(f"Pushed request {reqOrder} to the reqQueue")

            updateClk(reqOrder[0])
            incrementClk()
            
            # Respond with a reply
            print(f"Sent reply to client with port {clientConn.getpeername()[1]}")
            clk_tmp, PID_tmp = myClk, myPID
            incrementClk()
            simPropDelay()
            clientConn.send(f"reply-{ json.dumps( (clk_tmp, PID_tmp) ) }".encode() )

        elif re.match("release-\[[0-9]+, [0-9]+]", msg):    # Received release
            otherClk = json.loads(msg[8:])[0]
            updateClk(otherClk)
            incrementClk()

            reqQueue.get()  # Pop head of reqQueue

        else:
            print(f"Error: Received a non-request from client with port {clientConn.getpeername()[1]}. The message was {msg}.")

def handleClientConnections():
    # Concurrently listen for incoming client connections
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientSocketIn:
        clientSocketIn.bind( (socket.gethostname(), 9000 + myPID) )  # Bind to port 9000 + myPID
        clientSocketIn.listen()
        print(f"Listening for client connections on port {clientSocketIn.getsockname()[1]}")

        # Poll client connections in
        while True:
            clientConn, clientAddr = clientSocketIn.accept()
            threading.Thread(target=handleClientMsgsIn, args=[clientConn], daemon=True).start() # Start a thread to handle each in-connection
            print(f"Received connection from client at port {clientAddr[1]}")

def simPropDelay():
    time.sleep(2)

def broadcastRequests(clk, PID):
    # Send requests to every client with our logical Lamport clock and PID piggybacked
    clk_tmp, PID_tmp = clk, PID # In case clk or PID changes concurrently
    simPropDelay()
    for clientSocketOut in clientSocketOutList:
        clientSocketOut.send(f"request-{ json.dumps( (clk_tmp, PID_tmp) ) }".encode() )

def writeSentencesToFileServer():
    # Finally, we have access to the shared resource, so send it the queued sentences
    while not(sentenceQueue.empty() ):
        msg = fileServerSocket.recv(1024).decode()

        if (msg == "ready"):
            print("Received ready from server")
            incrementClk()  # [TODO] Not sure if supposed to increment for server messages

            # Send words one-by-one
            for word in sentenceQueue.get().split():
                fileServerSocket.send(word.encode() )
                print(f"Sent word {word} to server.")
                incrementClk()  # [TODO] Not sure if supposed to increment for server messages
        else:
            print(f"Received non-ready message from server. The message was {msg}. Exiting...")
            sys.exit()


if len(sys.argv) != 3:
    print(f"Usage: python {sys.argv[0]} <PID> <server_port>")
    sys.exit()

# Initialize cmdline-arg constants
myPID = int(sys.argv[1])
fileServerAddr = (socket.gethostname(), int(sys.argv[2]) )

# Initialize global vars
myClk = 1                           # Lamport logical clock
sentenceQueue = queue.Queue()       # (Synchronous) Queue storing sentences to write to the file server
reqQueue = queue.PriorityQueue()    # Priority-queue for storing requests, ordered by their tuple (clk, PID)
clkLock = threading.RLock()         # RLock for the clock

# Connect to file server
fileServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
fileServerSocket.connect(fileServerAddr)

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

# Now, the main thread will handle getting access to, accessing, and releasing the shared resource
while True:
    if not(sentenceQueue.empty() ):  # Sentence(s) is(are) queued to send
        # First, request access to the shared resource
        with clkLock:
            reqQueue.put( (myClk, myPID) )  # Push my own request to the prio-queue
            print(f"Pushed my own request {(myClk, myPID)} to the reqQueue")
            print(f"Broadcasting request-{ json.dumps( (myClk, myPID) ) } to clients")
            threading.Thread(target=broadcastRequests, args=[myClk, myPID], daemon=True).start()
            incrementClk()

        # Second, wait for numClients-1 replies
        for clientSocketOut in clientSocketOutList:
            msg = clientSocketOut.recv(1024).decode()
            if re.match("reply-\[[0-9]+, [0-9]+]", msg):
                print(f"Received {msg} from client at port {clientSocketOut.getpeername()[1]}")
                otherClk = json.loads(msg[6:])[0]
                updateClk(otherClk)
                incrementClk()
                continue
            else:
                print(f"Error: received non-reply from client at port {clientSocketOut.getpeername()[1]}")
                print("Exiting...")
                sys.exit()

        # Third, wait for our turn in the request queue
        while not(myPID == reqQueue.queue[0][1]):
            pass

        # Fourth, Access the shared resource
        writeSentencesToFileServer()

        # Finally, release the shared resource
        for clientSocketOut in clientSocketOutList:
            print(f"Sent release-{ json.dumps( (myClk, myPID) )} to client with port {clientSocketOut.getpeername()[1]}")
            clk_tmp, PID_tmp = myClk, myPID
            incrementClk()  # [TODO] Not sure if supposed to increment for a sending release

            simPropDelay()
            clientSocketOut.send(f"release-{ json.dumps( (clk_tmp, PID_tmp) ) }".encode() )