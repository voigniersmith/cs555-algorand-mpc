# Python Imports
import random
import time

from threading import Thread
from multiprocessing import Process, Queue
from elgamal import ElGamal

# Client Process
class client(Process):
    def __init__(self, proc_name, proc_ID, q0, q1, q2, qc, coeffs, eval_points, h, q, g):
        super(client, self).__init__()
        self.proc_name = proc_name
        self.proc_ID = proc_ID
        self.eg = ElGamal(q, g)
        self.q0 = q0
        self.q1 = q1
        self.q2 = q2
        self.qc = qc
        self.coeffs = coeffs
        self.eval_points = eval_points
        self.h = h
        self.q = q

    def run(self):
        # Hard Coded Values to Start
        messages = [5, 3, 6]
        goal = ((messages[0] * messages[1]) + messages[2]) % self.q

        # Generate k, which is private key
        # self.k = self.eg.gen_key(self.q)
        self.k = 9

        # Generate h^k, which is secret
        self.s = self.eg.power(self.h, self.k, self.q)

        # Shamir Share the secret
        s_shares = self.eg.generate_shares(list(self.coeffs), self.s, self.eval_points, self.proc_ID)

        # Encrypt the messages
        # cipher = [self.eg.gmul(messages[0], self.s), self.eg.gmul(messages[1], self.s), self.eg.gmul(messages[2], self.s)]
        cipher = [self.eg.gmul(messages[i], self.s) for i in range(3)]

        print("\nClient Initialization") 
        print("\tk: {}\ts: {}".format(self.k, self.s))
        print("\ts_shares[0]: {}\ts_shares[1]: {}\ts_shares[2]: {}".format(s_shares[0], s_shares[1], s_shares[2]))
        print("\tcipher[0]: {}\tcipher[1]: {}\tcipher[2]: {}".format(cipher[0], cipher[1], cipher[2]))

        # Send Secret to Each
        self.q0.put((self.proc_ID, cipher[0]))
        self.q0.put((self.proc_ID, s_shares[0]))

        self.q1.put((self.proc_ID, cipher[1]))
        self.q1.put((self.proc_ID, s_shares[1]))

        self.q2.put((self.proc_ID, cipher[2]))
        self.q2.put((self.proc_ID, s_shares[2]))

        vals = []

        for i in range(3):
            _, val = self.qc.get()
            vals.append(val)

        print("\nClient Final Check:")
        print("\tvals[0]: {}\tvals[1]: {}\tvals[2]: {}".format(vals[0], vals[1], vals[2]))

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
            print("\nGoal: {}, Decrypted: {}".format(goal, self.eg.gdiv(vals[0], self.s)))

        print("\n" + str(self.proc_name) + ": ID " + str(self.proc_ID) + " finished")

class party(Process):
    def __init__(self, proc_name, proc_ID, q0, q1, q2, qc, coeffs, eval_points, q, g):
        super(party, self).__init__()
        self.proc_name = proc_name
        self.proc_ID = proc_ID
        self.eg = ElGamal(q, g)
        self.qlist = [q0, q1, q2, qc]
        self.coeffs = coeffs
        self.eval_points = eval_points

    def run(self):
        # Get Cipher & Share of the Secret
        c = None
        s = None
        _, temp = self.qlist[self.proc_ID].get()
        if type(temp) == tuple:
            s = temp
            _, c = self.qlist[self.proc_ID].get()
        else:
            c = temp
            _, s = self.qlist[self.proc_ID].get()
        s = s[1]
        
        # Shamir my cipher
        cipher_shares = self.eg.generate_shares(list(self.coeffs), c, self.eval_points, self.proc_ID)

        print("\nParty {} Init Values:\n\tc: {}\n\ts: {}\n\tcipher_shares: {}"
            .format(self.proc_ID, c, s, cipher_shares))

        # Share cipher shares
        for i in range(3):
            if i != self.proc_ID:
                self.qlist[i].put((self.proc_ID, cipher_shares[i]))
                time.sleep(1)

        # Get my cipher shares
        local_cipher_shares = [None] * 3
        for i in range(3):
            if i != self.proc_ID:
                id, val = self.qlist[self.proc_ID].get()
                local_cipher_shares[id] = val
            else:
                local_cipher_shares[self.proc_ID] = cipher_shares[self.proc_ID]

        # Send Ciphers
        for i in range(3):
            if i != self.proc_ID:
                self.qlist[i].put((self.proc_ID, c))
                time.sleep(1)
        
        # Receive Ciphers
        cipher_texts = [None] * 3
        for i in range(3):
            if i != self.proc_ID:
                id, val = self.qlist[self.proc_ID].get()
                cipher_texts[id] = val
            else:
                cipher_texts[i] = c

        print("\nParty {} Communication 1:\n\tlocal_cipher_shares: {}\n\tcipher_texts: {}"
            .format(self.proc_ID, local_cipher_shares, cipher_texts))

        # Multiply
        # m = self.eg.gmul(local_cipher_shares[0][1], local_cipher_shares[1][1])
        m = self.eg.gmul(cipher_texts[0], cipher_texts[1])
        m_shares = self.eg.generate_shares(list(self.coeffs), m, list(self.eval_points), self.proc_ID)

        m_loc_share = None
        if self.proc_ID == 0:
            m_loc_share = m_shares[0]
        elif self.proc_ID == 1:
            m_loc_share = m_shares[1]
        elif self.proc_ID == 2:
            m_loc_share = m_shares[2]

        dec_c0 = self.eg.gdiv(local_cipher_shares[0][1], s)
        dec_c1 = self.eg.gdiv(local_cipher_shares[1][1], s)
        dec_m = self.eg.gmul(dec_c0, dec_c1)

        # Decrypt m & c3
        # dec_m = gdiv(m, s)
        # dec_m = gdiv(dec_m, s)
        dec_c2 = self.eg.gdiv(local_cipher_shares[2][1], s)

        # Add decrypted m & c3
        # res = self.eg.gadd(m_loc_share[1], dec_c2)
        res = self.eg.gadd(self.eg.gdiv(m_loc_share[1], s), dec_c2)
        print("\nParty {} res: {}, m_loc_share[1]: {}, dec_c2: {}"
            .format(self.proc_ID, res, m_loc_share[1], dec_c2))

        res = self.eg.gadd(dec_m, dec_c2)

        # Encrypt again
        end = self.eg.gmul(res, s)

        print("\nParty {} Maths:\n\tm: {}\n\tm_shares: {}\n\tm_loc_share: {}\n\tdec_c2: {}\n\tres: {}\n\tend: {}"
            .format(self.proc_ID, m, m_shares, m_loc_share, dec_c2, res, end))

        # Send Shares to Others
        for i in range(3):
            if i != self.proc_ID:
                self.qlist[i].put((self.proc_ID, end))

        # Receive end shares
        end_shares = [None] * 3
        for i in range(3):
            if i != self.proc_ID:
                id, val = self.qlist[self.proc_ID].get()
                end_shares[id] = (self.eval_points[id], val)
            else:
                end_shares[self.proc_ID] = (self.eval_points[self.proc_ID], end)

        # print("Party " + str(self.proc_ID) + ": Got Result Shares")

        # Combine results
        # Check that shamir is doing group math
        end_res = self.eg.reconstruct(end_shares)
        # print("Party " + str(self.proc_ID) + ": Reconstructed and Got - " + str(end_res))

        print("\nParty {} Final:\n\tend_shares: {}\n\tend_res: {}"
            .format(self.proc_ID, end_shares, end_res))

        # Notify Client
        self.qlist[3].put((self.proc_ID, end_res))

        # Put value on smart contract?


P0_ID = 0
P1_ID = 1
P2_ID = 2
C_ID = 3

def main():
    # Runtime Code
    print("Main Start\n")

    # Set Random Seed
    random.seed(time.time_ns())
    q = 11
    g = random.randint(2, q)
    # g = 5
    eg = ElGamal(q, g)

    # Set Globals
    coeffs = eg.coeff(2)
    coeffs = [0]
    eval_points = eg.get_eval_points(3)
    eval_points = [1, 2, 3]

    # Setup IPC
    q0 = Queue(10)
    q1 = Queue(10)
    q2 = Queue(10)
    qc = Queue(10)

    # Party Stuff
    parties = []
    a = eg.gen_key(q)
    a = 0
    h = pow(g, a, q)
    h = 4

    print("\nMain Initialize Values:")
    print("\ta: {}, h: {}, g: {}, q: {}".format(a, h, g, q))
    print("\tCoeff: {}".format(list(coeffs)))
    print("\tEval Points: {}".format(eval_points))

    # Party 0
    party_proc = party("Party " + str(0), 0, q0, q1, q2, qc, coeffs, eval_points, q, g)
    parties.append(party_proc)

    # Party 1
    party_proc = party("Party " + str(1), 1, q0, q1, q2, qc, coeffs, eval_points, q, g)
    parties.append(party_proc)

    # Party 2
    party_proc = party("Party " + str(2), 2, q0, q1, q2, qc, coeffs, eval_points, q, g)
    parties.append(party_proc)

    for i in range(3):
        parties[i].start()

    # Client Stuff
    client_prc = client("Client", C_ID, q0, q1, q2, qc, coeffs, eval_points, h, q, g)
    client_prc.start()

    # Wait for everything to finish
    for i in range(3):
        parties[i].join()
    client_prc.join()

    print("\nMain Exit")

if __name__ == "__main__":
    main()
