# lamportDistSol
UCSB CS 171 W '21

3 Clients
1 File Server

Implementation of Lamport's Distributed Solution protocol for Mutual Exclusion (request, reply, release).

The clients try to send sentences to the file server, one word at a time. The output file written to by the server is the shared resource. If the sentences are out-of-order, then mutual exclusion was not maintained.

server.py was provided by the school
