# Python Imports
import random
from multiprocessing import Process, Queue
import time

# Classes
class shamir_sharing():
    def __init__(self, secret, group_size) -> None:
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

class client(Process):
    def __init__(self, thread_name, thread_ID):
        super(client, self).__init__()
        self.thread_name = thread_name
        self.thread_ID = thread_ID

    def run(self):
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

        for i in range(3):
            queues[i].put(cipher[i], secret_share[i])

        vals = []

        for i in range(3):
            vals.append(queues[i].get())

        # Checking what we received is consistent
        temp = vals[0]
        for i in range(1, vals):
            if temp != vals[i]:
                # Wrong Outputs
                print("Incorrect Values: " + str(temp) + " " + str(vals[i]))
                temp = vals[i]
                break
        if temp == vals[0]:
            # Consistent Outputs
            print("Consistent Values")


        print(str(self.thread_name) + ": ID " + str(self.thread_ID))

class party(Process):
    def __init__(self, thread_name, thread_ID):
        super(party, self).__init__()
        self.thread_name = thread_name
        self.thread_ID = thread_ID

    def run(self):
        # Get Cipher & Message

        # Get/Send c1

        # Get/Send c2

        # Multiply

        # Decrypt m & c3

        # Add decrypted m & c3

        # Encrypt again

        # Send Shares to Others
        print(str(self.thread_name) + ": ID " + str(self.thread_ID))

queues = []

P0_ID = 0
P1_ID = 1
P2_ID = 2
C_ID = 3

def main():
    # Runtime Code
    print("Start")

    # Set Random Seed
    random.seed(time.time_ns())

    # Set Up IPC
    queues.append(Queue.queue())
    queues.append(Queue.queue())
    queues.append(Queue.queue())
    queues.append(Queue.queue())

    # Party Stuff
    parties = []
    for i in range(3):
        party_thread = party("Party " + str(i), i)
        parties.append(party_thread)

    for i in range(3):
        parties[i].start()

    for i in range(3):
        parties[i].join()

    # Client Stuff
    client_prc = client("Client", C_ID)
    client_prc.start()

    print("Exit")

if __name__ == "__main__":
    main()
