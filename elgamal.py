# code modified from GeeksForGeeks 
# https://www.geeksforgeeks.org/elgamal-encryption-algorithm/
import random
from math import pow
 
class ElGamal():
    def __init__(self):
        self.q = random.randint(pow(10, 20), pow(10, 50))
        self.g = random.randint(2, self.q)

        # self.key = self.gen_key(self.q)# Private key for receiver
        # self.h = self.power(self.g, self.key, self.q)
        
    def gcd(self, a, b):
        if a < b:
            return self.gcd(b, a)
        elif a % b == 0:
            return b
        else:
            return self.gcd(b, a % b)
    
    # Generating large random numbers
    def gen_key(self, q):
    
        key = random.randint(pow(10, 20), q)
        while self.gcd(q, key) != 1:
            key = random.randint(pow(10, 20), q)
    
        return key
    
    # Modular exponentiation
    def power(self, a, b, c):
        x = 1
        y = a
    
        while b > 0:
            if b % 2 != 0:
                x = (x * y) % c
            y = (y * y) % c
            b = int(b / 2)
    
        return x % c
    
    # Asymmetric encryption
    def encrypt(self, msg, q, h, g):
    
        en_msg = []
    
        k = self.gen_key(q)# Private key for sender
        s = self.power(h, k, q)
        p = self.power(g, k, q)
        
        for i in range(0, len(msg)):
            en_msg.append(msg[i])
    
        print("g^k used : ", p)
        print("g^ak used : ", s)
        for i in range(0, len(en_msg)):
            en_msg[i] = s * ord(en_msg[i])
    
        return en_msg, p
    
    def decrypt(self, en_msg, p, key, q):
    
        dr_msg = []
        h = self.power(p, key, q)
        for i in range(0, len(en_msg)):
            dr_msg.append(chr(int(en_msg[i]/h)))
            
        return dr_msg

# msg = "hello world"
# test = ElGamal()
# en_msg, p = test.encrypt(msg, test.q, test.h, test.g)
# dc_msg = test.decrypt(en_msg, p, test.key, test.q)
# dmsg = ''.join(dc_msg)
# print(msg, en_msg, dmsg)