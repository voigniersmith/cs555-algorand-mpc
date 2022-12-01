# code modified from GeeksForGeeks 
# https://www.geeksforgeeks.org/elgamal-encryption-algorithm/
import random
from math import pow

from Crypto.Util import number
# q = number.getPrime(1024)
# q = 11
# g = random.randint(2, q)
# print("g: {}".format(g))
# g = 5
 
class ElGamal():
    def __init__(self, q, g):
        self.q = q
        self.g = g

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
    
        # key = random.randint(pow(10, 20), q)
        key = random.randint(0, q)
        # while self.gcd(q, key) != 1:
        #     key = random.randint(pow(10, 20), q)
        # key = 6
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

    def ginv(self, x):
        t = 0
        new_t = 1
        r = self.q
        new_r = x
        while new_r != 0:
            quotient = r // new_r
            t, new_t = (new_t, t - quotient * new_t)
            r, new_r = (new_r, r - quotient * new_r)
        if t < 0:
            t = t + self.q
        return t

    def gadd(self, x, y):
        return (x + y) % self.q

    def gmul(self, x, y):
        return (x * y) % self.q

    def gdiv(self, x, y):
        return (x * self.ginv(y)) % self.q


    def reconstruct(self, shares):
        """
        Combines individual shares (points on graph)
        using Lagranges interpolation.
    
        `shares` is a list of points (x, y) belonging to a
        polynomial with a constant of our key.
        """
        sums = 0
        prod_arr = []
    
        for j, share_j in enumerate(shares):
            xj, yj = share_j
            prod = 1
    
            for i, share_i in enumerate(shares):
                xi, _ = share_i
                if i != j:
                    prod = self.gmul(prod, self.gdiv(xi, (xi-xj) % self.q))
    
            prod = self.gmul(prod, yj)
            sums = self.gadd(sums, prod)
    
        return sums
    
    
    def polynom(self, x, coefficients):
        """
        This generates a single point on the graph of given polynomial
        in `x`. The polynomial is given by the list of `coefficients`.
        """
        point = 0
        # Loop through reversed list, so that indices from enumerate match the
        # actual coefficient indices
        for coefficient_index, coefficient_value in enumerate(list(coefficients)[::-1]):
            point = self.gadd(point, self.gmul(x ** coefficient_index % self.q, coefficient_value))
        return point
    
    
    def coeff(self, t):
        """
        Randomly generate a list of coefficients for a polynomial with
        degree of `t` - 1, whose constant is `secret`.
    
        For example with a 3rd degree coefficient like this:
            3x^3 + 4x^2 + 18x + 554
    
            554 is the secret, and the polynomial degree + 1 is
            how many points are needed to recover this secret.
            (in this case it's 4 points).
        """
        coeff = [random.randrange(0, self.q) for _ in range(t - 1)]
        # coeff.append(secret)
        return coeff
    
    def get_eval_points(self, n):
        '''
        get evaluation points for n parties
        '''
        # return [1, 2, 3]
        # need unique evaluation points
        temp = set()
        while len(temp) != n:
            temp.add(random.randrange(1, self.q))
        return list(temp)
    
    def generate_shares(self, coefficients, secret, eval_points, pid):
        """
        Split given `secret` into `n` shares with minimum threshold
        of `m` shares to recover this `secret`, using SSS algorithm.
        """
        coefficients = list(coefficients)
        coefficients.append(secret)
        # return [(x, self.polynom(x, coefficients)) for x in list(eval_points)]
        shares = [(x, self.polynom(x, coefficients)) for x in list(eval_points)]
        # print("\nPID: {} in Generate Shares\n\tCoefficients: {}\n\tsecret: {}\n\teval_points: {}\n\tshares: {}"
        #     .format(pid, coefficients, secret, eval_points, shares))
        # print("\nShares: {}\n".format(shares))
        return shares


# msg = "hello world"
# test = ElGamal()
# en_msg, p = test.encrypt(msg, test.q, test.h, test.g)
# dc_msg = test.decrypt(en_msg, p, test.key, test.q)
# dmsg = ''.join(dc_msg)
# print(msg, en_msg, dmsg)