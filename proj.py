# Python Imports
import queue
import random
import time

from multiprocessing import Process, Pipe, Queue
from elgamal import ElGamal
from shamir import Shamir
from group import ginv, gadd, gmul, gdiv


class client(Process):
    def __init__(self, thread_name, thread_ID):
        super(client, self).__init__()
        self.thread_name = thread_name
        self.thread_ID = thread_ID

    def run(self):
        print(str(self.thread_name) + ": ID " + str(self.thread_ID))

class party(Process):
    # Hard Coded Values to Start
    cipher = {
        4,
        0,
        7
    }
    secret_share = {
        4,
        5,
        6
    }

    def __init__(self, thread_name, thread_ID):
        super(party, self).__init__()
        self.thread_name = thread_name
        self.thread_ID = thread_ID

    def run(self):
        # Get Encrypted Message & Share
        print(str(self.thread_name) + ": ID " + str(self.thread_ID))


def main():
    # Runtime Code
    print("Start")

    # Set Random Seed
    random.seed(time.time_ns())

    # Client Stuff
    client_prc = client("Client", 0)
    client_prc.start()

    # Party Stuff
    parties = []
    for i in range(3):
        party_thread = party("Party " + str(i), i)
        parties.append(party_thread)

    for i in range(3):
        parties[i].start()

    print("Exit")

if __name__ == "__main__":
    main()
