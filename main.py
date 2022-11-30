# Python Imports
import random
import time

from threading import Thread
from multiprocessing import Process, Queue
from elgamal import ElGamal
from Crypto.Util import number

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
        self.g = g

    def run(self):
        # Hard Coded Values to Start
        messages = [random.randint(0, 1000), random.randint(0, 1000), random.randint(0, 1000)]
        # messages = [5, 1, 7]
        goal = ((messages[0] * messages[1]) + messages[2]) % self.q

        # Generate k, which is private key
        self.k = self.eg.gen_key(self.q)
        self.k = 9

        # Generate h^k, which is secret
        self.s = self.eg.power(self.h, self.k, self.q)

        # Shamir Share the secret
        s_shares = self.eg.generate_shares(list(self.coeffs), self.s, self.eval_points, self.proc_ID)

        # Encrypt the messages
        cipher = [self.eg.gmul(messages[0], self.s), self.eg.gmul(messages[1], self.s),
            self.eg.gmul(self.g ** messages[2] % self.q, self.s)]
        # cipher = [self.eg.gmul(messages[i], self.s) for i in range(3)]

        print("\nClient Initialization") 
        print("\tk: {}\ts: {}".format(self.k, self.s))
        print("\tmessages[0]: {}\tmessages[1]: {}\tmessages[2]: {}".format(messages[0], messages[1], messages[2]))
        print("\ts_shares[0]: {}\ts_shares[1]: {}\ts_shares[2]: {}".format(s_shares[0], s_shares[1], s_shares[2]))
        print("\tg ({}) ^ messages[2] ({}): {}".format(self.g, messages[2], self.g ** messages[2] % self.q))
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
            print("\nClient Results:")
            print("\tGoal: {}".format(goal))
            print("\tg ({}) ^ Goal ({}) : {}".format(self.g, goal, self.eg.power(self.g, goal, self.q)))
            print("\tDecrypted: {}".format(self.eg.gdiv(vals[0], self.s)))

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
        self.q = q
        self.g = g

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

        # print("\nParty {} Init Values:\n\tc: {}\n\ts: {}\n\tcipher_shares: {}"
        #     .format(self.proc_ID, c, s, cipher_shares))

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

        print("\nParty {} Communication:\n\tlocal_cipher_shares: {}\n\tcipher_texts: {}"
            .format(self.proc_ID, local_cipher_shares, cipher_texts))

        strat = 0.5

        if strat == 0:
            # Strategy 0 -- No Sharing & Full Decrypt (WORKS!!)
            # Multiply Cipher Texts
            m = self.eg.gmul(cipher_texts[0], cipher_texts[1])

            # Decrypt Cipher Text Product
            dec_m = self.eg.gdiv(m, s)
            dec_m = self.eg.gdiv(dec_m, s)

            # Encrypt Cipher Text Product for "Addition"
            pow_m = self.eg.power(self.g, dec_m, self.q)
            enc_m = self.eg.gmul(pow_m, s)

            # Decrypt c2 for testing
            dec_c2 = self.eg.gdiv(cipher_texts[2], s)

            # "Add"
            sum = self.eg.gmul(enc_m, cipher_texts[2])
            sum = self.eg.gmul(pow_m, dec_c2)

            # Decrypt?
            res = self.eg.gdiv(sum, s)
            res = self.eg.gdiv(res, s)
            res = self.eg.gmul(sum, s)

            print("\nParty {} MPC:\n\tmul: {}\n\tdec_m: {}\n\tdec_c2: {}\n\tpow_m: {}\n\tenc_m: {}\n\tsum: {}\n\tres: {}"
                .format(self.proc_ID, m, dec_m, dec_c2, pow_m, enc_m, sum, res))
        elif strat == 0.5:
            # Strategy 0.5 -- No Sharing & No Full Decrypt (WORKS!!)
            # Multiply Cipher Texts
            m = self.eg.gmul(cipher_texts[0], cipher_texts[1])

            # Decrypt Cipher Text Product
            dec_m = self.eg.gdiv(m, s)
            dec_m = self.eg.gdiv(dec_m, s)

            # Encrypt Cipher Text Product for "Addition"
            pow_m = self.eg.power(self.g, dec_m, self.q)
            enc_m = self.eg.gmul(pow_m, s)

            # "Add"
            sum = self.eg.gmul(enc_m, cipher_texts[2])

            # Decrypt?
            res = self.eg.gdiv(sum, s)

            print("\nParty {} MPC:\n\ts^-1: {}\n\tmul: {}\n\tdec_m: {}\n\tpow_m: {}\n\tenc_m: {}\n\tsum: {}\n\tres: {}"
                .format(self.proc_ID, self.eg.ginv(s), m, dec_m, pow_m, enc_m, sum, res))
        elif strat == 1:
            # Strategy 1
            # Multiplying Using Cipher Shares
            mul_shared = self.eg.gmul(local_cipher_shares[0][1], local_cipher_shares[1][1])

            # Decrypt The Share of The Product (Do we do it twice?)
            dec_mul_shared = self.eg.gdiv(mul_shared, s)
            dec_mul_shared = self.eg.gdiv(mul_shared, s)

            # Re-encypt for "addition"
            mul_pow = self.eg.power(self.g, dec_mul_shared, self.q)
            mul_enc = self.eg.gmul(mul_pow, s)

            # "Add"
            add_enc = self.eg.gmul(mul_enc, local_cipher_shares[2][1])

            # Set up for expected decryption
            res = self.eg.gdiv(add_enc, s)

            print("\nParty {} MPC:\n\tmul: {}\n\tdec_mul: {}\n\tmul_pow: {}\n\tmul_enc: {}\n\t\"add\": {}\n\tres: {}"
                .format(self.proc_ID, mul_shared, dec_mul_shared, mul_pow, mul_enc, add_enc, res))
        elif strat == 2:
            # Strategy 2
            # Multiplying Using Full Cipher Texts
            mul_texts = self.eg.gmul(cipher_texts[0], cipher_texts[1])
            
            # Decrypt the full cipher multiply (do we do it twice?)
            dec_mul_texts = self.eg.gdiv(mul_texts, s)
            dec_mul_texts = self.eg.gdiv(mul_texts, s)

            m_shares = self.eg.generate_shares(list(self.coeffs), dec_mul_texts, list(self.eval_points), self.proc_ID)
            m_loc_share = None
            if self.proc_ID == 0:
                m_loc_share = m_shares[0]
            elif self.proc_ID == 1:
                m_loc_share = m_shares[1]
            elif self.proc_ID == 2:
                m_loc_share = m_shares[2]

            # Re-encypt for addition
            mul_enc = self.eg.gmul(self.eg.power(self.g, m_loc_share[1], self.q), s)

            # Add
            add_enc = self.eg.gmul(mul_enc, local_cipher_shares[2][1])

            # Set up for expected decryption
            res = self.eg.gdiv(add_enc, s)
        else:
            # Strategy 3
            # Decrypting each cipher shares(?)
            dec_c0 = self.eg.gdiv(local_cipher_shares[0][1], s)
            dec_c1 = self.eg.gdiv(local_cipher_shares[1][1], s)
            dec_c2 = self.eg.gdiv(local_cipher_shares[2][1], s)

            dec_m = self.eg.gmul(dec_c0, dec_c1)

            # Re-encypt for addition
            mul_enc = self.eg.power(self.g, dec_m, self.q)

            # Add
            add_enc = self.eg.gmul(mul_enc, dec_c2)

            # Set up for expected decryption?
            # res = self.eg.gdiv(add_enc, s)
            res = add_enc

        # # Original Strategy
        # # Add decrypted m & c3
        # res = self.eg.gadd(self.eg.gdiv(m_loc_share[1], s), dec_c2)
        # print("\nParty {} res: {}, m_loc_share[1]: {}, dec_c2: {}"
        #     .format(self.proc_ID, res, m_loc_share[1], dec_c2))

        # res = self.eg.gadd(dec_m, dec_c2)

        # # Encrypt again
        # end = self.eg.gmul(res, s)

        # print("\nParty {} Maths:\n\tm: {}\n\tm_shares: {}\n\tm_loc_share: {}\n\tdec_c2: {}\n\tres: {}\n\tend: {}"
        #     .format(self.proc_ID, m, m_shares, m_loc_share, dec_c2, res, end))

        # Send Shares to Others
        for i in range(3):
            if i != self.proc_ID:
                self.qlist[i].put((self.proc_ID, res))

        # Receive end shares
        end_shares = [None] * 3
        for i in range(3):
            if i != self.proc_ID:
                id, val = self.qlist[self.proc_ID].get()
                end_shares[id] = (self.eval_points[id], val)
            else:
                end_shares[self.proc_ID] = (self.eval_points[self.proc_ID], res)

        # print("Party " + str(self.proc_ID) + ": Got Result Shares")

        # Combine results
        # Check that shamir is doing group math
        end_res = self.eg.reconstruct(end_shares)
        # print("Party " + str(self.proc_ID) + ": Reconstructed and Got - " + str(end_res))

        # print("\nParty {} Final:\n\tend_shares: {}\n\tend_res: {}"
        #     .format(self.proc_ID, end_shares, end_res))

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
    q = number.getPrime(1024)
    # q = 17 # must be bigger than the goal!!
    g = random.randint(2, q)
    g = 5
    eg = ElGamal(q, g)

    # Set Globals
    # coeffs = eg.coeff(3)
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
    a = 3
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
