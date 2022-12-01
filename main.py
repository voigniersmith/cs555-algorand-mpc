# Python Imports
import random
import time
import argparse
import os
import sys
import signal

from multiprocessing import Process, Queue, current_process
from elgamal import ElGamal
from conf import party_mnemonic, client_mnemonic
from algo_utils import get_client, mnemonic_to_pk, donation_escrow, compile_smart_signature, payment_transaction, lsig_payment_txn 
from Crypto.Util import number

'''
    TODO:
    - Need to add kill scenario 3, after receiving client payment
'''

PAYMENT = 10000 * 1000000
C_ID = 3

'''
    Functions
'''
def generators(n):
    s = set(range(1, n))
    results = []
    for a in s:
        g = set()
        for x in s:
            g.add((a**x) % n)
        if g == s:
            results.append(a)
    return results

def prepare_elgamal():
    random.seed(time.time_ns())
    q = number.getPrime(10)
    g = generators(q)
    g = g[random.randint(0, len(g))]
    return q, g
    
def prepare_shamir(eg):
    coeffs = eg.coeff(2)
    coeffs = [0]
    eval_points = eg.get_eval_points(3)
    return coeffs, eval_points

def keyboard_int_handler(signum, frame):
    signame = signal.Signals(signum).name
    print("Process {} stopped by {}"
        .format(current_process().pid, signame))
    os.kill(current_process().pid, signal.SIGTERM)

'''
    Client Class
'''
class client(Process):
    def __init__(self, proc_name, proc_ID, queues, shamir, public, algo, messages):
        super(client, self).__init__()
        self.proc_name = proc_name
        self.proc_ID = proc_ID
        self.eg = ElGamal(public[0], public[1])
        self.q0 = queues[0]
        self.q1 = queues[1]
        self.q2 = queues[2]
        self.qc = queues[3]
        self.coeffs = shamir[0]
        self.eval_points = shamir[1]
        self.h = public[2]
        self.q = public[0]
        self.algo = algo
        self.messages = messages
        
    def make_payment(self):
        # get algorand client
        try:
            client = get_client()
            compiled = donation_escrow(mnemonic_to_pk(party_mnemonic))
            res, addr = compile_smart_signature(client, compiled)
            amt = PAYMENT
            result = payment_transaction(client_mnemonic, amt, addr, client)
            # TODO: something with result
            self.q0.put((res, addr))
            self.q1.put((res, addr))
            self.q2.put((res, addr))
        except Exception as e:
            print("Cannot make payment")
            print(e)
            return -1, -1
        return res, addr

    def run(self):
        res = None
        addr = None
        if self.algo:
            # Make smart contract transaction 
            res, addr = self.make_payment()
            if res == -1:
                return
        
        if self.send_stuff() == -1:
            # party died
            time.sleep(3)
            self.q0.put((res, addr))
            self.q1.put((res, addr))
            self.q2.put((res, addr))
            self.send_stuff()
        

    def send_stuff(self):
        # Setup Interrupt Handlers
        signal.signal(signal.SIGINT, keyboard_int_handler)

        # Hard Coded Values to Start
        # messages = [21, 7, 90]
        messages = [random.randint(0, 99), random.randint(0, 99), random.randint(0, 99)]

        if self.messages != None:
            for i in range(len(self.messages)):
                messages[i] = self.messages[i]

        goal = ((messages[0] * messages[1]) + messages[2]) % self.q

        # Generate k, which is private key
        self.k = self.eg.gen_key(self.q)
        # self.k = 9

        # Generate h^k, which is secret
        self.s = self.eg.power(self.h, self.k, self.q)

        # Shamir Share the secret
        s_shares = self.eg.generate_shares(list(self.coeffs), self.s, self.eval_points, self.proc_ID)

        # Encrypt the messages
        cipher = [self.eg.gmul(messages[i], self.s) for i in range(3)]

        # print("\nClient Initialization") 
        # print("\tk: {}\ts: {}".format(self.k, self.s))
        # print("\tmessages[0]: {}\tmessages[1]: {}\tmessages[2]: {}".format(messages[0], messages[1], messages[2]))
        # print("\ts_shares[0]: {}\ts_shares[1]: {}\ts_shares[2]: {}".format(s_shares[0], s_shares[1], s_shares[2]))
        # print("\tcipher[0]: {}\tcipher[1]: {}\tcipher[2]: {}".format(cipher[0], cipher[1], cipher[2]))

        # Send Secret to Each
        self.q0.put((self.proc_ID, cipher[0]))
        self.q0.put((self.proc_ID, s_shares[0]))

        self.q1.put((self.proc_ID, cipher[1]))
        self.q1.put((self.proc_ID, s_shares[1]))

        self.q2.put((self.proc_ID, cipher[2]))
        self.q2.put((self.proc_ID, s_shares[2]))

        vals = []

        for i in range(3):
            try:
                _, val = self.qc.get(timeout=10)
            except:
                pass
            vals.append(val)
            if val == -1:
                break

        if vals[0] == -1:
            # TODO: Remove Money
            return -1
            # os.kill(current_process().pid, signal.SIGTERM)
            

        # print("\nClient Final Check:")
        # for i in range(len(vals)):
        #     print("\tvals[{}]: {}".format(i, vals[i]), end="")
        # print("")

        # Checking what we received is consistent
        temp = vals[0]
        for i in range(1, len(vals)):
            if temp != vals[i]:
                # Wrong Outputs
                print("\n\tIncorrect Values")
                temp = vals[i]
                break
        if temp == vals[0]:
            # Consistent Outputs
            print("\nClient Got:\n\tGoal: {}, Decrypted: {}".format(goal, self.eg.gdiv(vals[0], self.s)))


'''
    Party Class
'''
class party(Process):
    def __init__(self, proc_name, proc_ID, queues, shamir, public_info, algo, adv_values):
        super(party, self).__init__()
        self.proc_name = proc_name
        self.proc_ID = proc_ID
        self.eg = ElGamal(public_info[0], public_info[1])
        self.qlist = [queues[0], queues[1], queues[2], queues[3]]
        self.coeffs = shamir[0]
        self.eval_points = shamir[1]
        self.algo = algo
        self.to_kill = adv_values[0]
        self.stage = adv_values[1]
        self.peek = adv_values[2]

    def fail_func(self):
        self.qlist[3].put((self.proc_ID, -1))
        time.sleep(2)
        os.kill(current_process().pid, signal.SIGTERM)

    def mpc(self):
        # Get Cipher & Share of the Secret
        c = None
        s = None

        try:
            _, temp = self.qlist[self.proc_ID].get(timeout=3)
            if type(temp) == tuple:
                s = temp
                _, c = self.qlist[self.proc_ID].get(timeout=3)
            else:
                c = temp
                _, s = self.qlist[self.proc_ID].get(timeout=3)
            s = s[1]

        except Exception as e:
            self.fail_func()

        if self.to_kill == self.proc_ID and self.stage == 0:
            os.kill(current_process().pid, signal.SIGTERM)
        
        # Shamir my cipher
        cipher_shares = self.eg.generate_shares(list(self.coeffs), c, self.eval_points, self.proc_ID)

        # Print
        if self.proc_ID == self.peek or self.peek == 3:
            print("\nParty {} Init Values:\n\tc: {}\n\ts: {}\n\tcipher_shares: {}"
                .format(self.proc_ID, c, s, cipher_shares))

        # Share cipher shares
        for i in range(3):
            if i != self.proc_ID:
                self.qlist[i].put((self.proc_ID, cipher_shares[i]))
                time.sleep(1)

        try:
            # Get my cipher shares
            local_cipher_shares = [None] * 3
            for i in range(3):
                if i != self.proc_ID:
                    id, val = self.qlist[self.proc_ID].get(timeout=3)
                    local_cipher_shares[id] = val
                else:
                    local_cipher_shares[self.proc_ID] = cipher_shares[self.proc_ID]

        except Exception as e:
            self.fail_func()

        if self.to_kill == self.proc_ID and self.stage == 1:
            os.kill(current_process().pid, signal.SIGTERM)

        # Multiply
        m = self.eg.gmul(local_cipher_shares[0][1], local_cipher_shares[1][1])

        # Decrypt Share of C2
        dec_c2 = self.eg.gdiv(local_cipher_shares[2][1], s)

        # Add the Decrypted Shares
        res = self.eg.gadd(self.eg.gdiv(self.eg.gdiv(m, s), s), dec_c2)

        # Print
        if self.proc_ID == self.peek or self.peek == 3:
            print("\nParty {} res: {}, m: {}, dec_c2: {}"
                .format(self.proc_ID, res, m, dec_c2))

        # Encrypt again
        end = self.eg.gmul(res, s)

        # Print
        if self.proc_ID == self.peek or self.peek == 3:
            print("\nParty {} Maths:\n\tm: {}\n\tdec_c2: {}\n\tres: {}\n\tend: {}"
                .format(self.proc_ID, m, dec_c2, res, end))

        # Send Shares to Others
        for i in range(3):
            if i != self.proc_ID:
                self.qlist[i].put((self.proc_ID, end))

        try:
            # Receive end shares
            end_shares = [None] * 3
            for i in range(3):
                if i != self.proc_ID:
                    id, val = self.qlist[self.proc_ID].get(timeout=3)
                    end_shares[id] = (self.eval_points[id], val)
                else:
                    end_shares[self.proc_ID] = (self.eval_points[self.proc_ID], end)

        except Exception as e:
            self.fail_func()

        # Combine results
        end_res = self.eg.reconstruct(end_shares)

        if self.to_kill == self.proc_ID and self.stage == 2:
            os.kill(current_process().pid, signal.SIGTERM)

        # Print
        if self.proc_ID == self.peek or self.peek == 3:
            print("\nParty {} Final:\n\tend_shares: {}\n\tend_res: {}"
                .format(self.proc_ID, end_shares, end_res))

        # Notify Client
        self.qlist[3].put((self.proc_ID, end_res))


    def run(self):
        # Set up interrupt handlers
        signal.signal(signal.SIGINT, keyboard_int_handler)

        if self.algo:
            # block until the client sends money
            client = get_client()
            while self.qlist[self.proc_ID].empty():
                continue
            res, addr = self.qlist[self.proc_ID].get(timeout=3) 

            # received transaction, compute
            self.mpc()

            # receive payment
            if self.proc_ID == 2:
                lsig_payment_txn(res, addr, PAYMENT, mnemonic_to_pk(party_mnemonic), client)
        else:
            self.mpc()


'''
    Main:
    - Initializes
    - Contains Driver Code
'''
def main(kill=None, stage=None, algo=True, messages=None, peek=None):
    # Runtime Code
    print("\nStart")

    # Preparation
    doagain = False
    q, g = prepare_elgamal()
    eg = ElGamal(q, g)
    coeffs, eval_points = prepare_shamir(eg)

    # Setup IPC
    q0 = Queue(10)
    q1 = Queue(10)
    q2 = Queue(10)
    qc = Queue(10)

    # Party Stuff
    parties = []
    a = eg.gen_key(q)
    h = pow(g, a, q)

    adv_values = (kill, stage, peek)
    queues = ( q0, q1, q2, qc )
    shamir_info = ( coeffs, eval_points )
    public_info = ( q, g, h )

    print("\nMain Initialize Values:")
    print("\tq: {}, g: {}, h: {}".format(q, g, h))

    # Party 0
    party_proc = party("Party " + str(0), 0, queues, shamir_info, public_info, algo, adv_values)
    parties.append(party_proc)

    # Party 1
    party_proc = party("Party " + str(1), 1, queues, shamir_info, public_info, algo, adv_values)
    parties.append(party_proc)

    # Party 2
    party_proc = party("Party " + str(2), 2, queues, shamir_info, public_info, algo, adv_values)
    parties.append(party_proc)

    try: 
        # Start the Parties
        for i in range(3):
            parties[i].start()

        # Client Create & Start
        client_prc = client("Client", C_ID, queues, shamir_info, public_info, algo, messages)
        client_prc.start()

        # Wait for everything to finish
        for i in range(3):
            parties[i].join()
        client_prc.join()
            
    except Exception as e:
        # Exception Happened
        print("Exception:\n{}".format(e))
    
    # Check for failure
    for i in range(4):
        while not queues[i].empty():
            _, val = queues[i].get()
            if val == -1:
                doagain = True

    if doagain:
        # Force alive
        adv_values = (-1, -1, peek)

        # Remove old parties
        parties.clear()

        # Restart Function
        # Party 0
        party_proc = party("Party " + str(0), 0, queues, shamir_info, public_info, algo, adv_values)
        parties.append(party_proc)

        # Party 1
        party_proc = party("Party " + str(1), 1, queues, shamir_info, public_info, algo, adv_values)
        parties.append(party_proc)

        # Party 2
        party_proc = party("Party " + str(2), 2, queues, shamir_info, public_info, algo, adv_values)
        parties.append(party_proc)

        # Start the Parties
        for i in range(3):
            parties[i].start()

        # Client Create & Start
        client_prc = client("Client", C_ID, queues, shamir_info, public_info, algo, messages)
        client_prc.start()

        # Wait for everything to finish
        for i in range(3):
            parties[i].join()
        client_prc.join()


    print("\nExit")

'''
    __name__:
    - Parses Arguments
    - Starts Driver Code
'''
if __name__ == "__main__":
 
    # Initialize parser
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--messages", nargs = '*', help = "messages to pass in, up to 3, defaults to random")
    parser.add_argument("-a", "--algo", help = "default True, use the algorand smart contract")
    parser.add_argument("-k", "--kill", help = "party to kill, either 0, 1, 2")
    parser.add_argument("-s", "--stage", help = '''
        stage to kill, either:
        0 - after receiving cipher and share of key,
        1 - after sharing during MPC,
        2 - after computation, but before sending result,
        3 - after receiving client payment''')

    parser.add_argument("-p", "--peek", help = "party to watch, either 0, 1, 2")
    args = parser.parse_args()
    
    kill = -1
    peek = -1
    stage = -1
    algo = True
    messages = None
    if args.kill:
        kill = int(args.kill)
    if args.algo:
        algo = str(args.algo).lower == 'true'
    if args.messages:
        messages = [ int(x) for x in args.messages ]
    if args.peek:
        peek = int(args.peek)
    if args.stage:
        stage = int(args.stage)

    # Set up signal handlers
    signal.signal(signal.SIGINT, keyboard_int_handler)
    
    main(kill, stage, algo, messages, peek)
