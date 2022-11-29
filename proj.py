# Python Imports
import queue
import random
from multiprocessing import Process, Pipe, Queue
import time

def func(x):

    pass

# Classes
class shamir_sharing():
    def __init__(self, secret, group_size) -> None:
        # Save Function
        self.function = func()

        # Generate Alphas (Evaluation Points)
        self.alpha = {
            random.randint(1, group_size - 1),
            random.randint(1, group_size - 1),
            random.randint(1, group_size - 1),
        }
        # How to ensure no duplicate evaluation points?

        # Save Secret
        self.secret = secret

    # Shamir Function
    def func(self, x):
        return self.x + self.secret

    # Get evaluation point using party number
    def get_alpha(self, num):
        return self.alpha[num]

    # Get a share, based on party number
    def get_share(self, num):
        return self.func(self.get_alpha(num))

class group_math():
    def __init__(self, group_size) -> None:
        self.group_size = group_size

    def group_mod(self, x):
        return x % self.group_size

    def group_inv(self, x):
        return pow(x, (self.group_size - 2), self.group_size)

    def group_add(self, x, y):
        return (x + y) % self.group_size

    def group_mul(self, x, y):
        return (x * y) % self.group_size

    def group_div(self, x, y):
        return (x * self.group_inv(self, y)) % self.group_size

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
