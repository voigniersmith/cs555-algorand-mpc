# code taken from geeks for geeks
# https://www.geeksforgeeks.org/implementing-shamirs-secret-sharing-scheme-in-python/

import random
from group import ginv, gadd, gmul, gdiv
 
from elgamal import q as FIELD_SIZE
 
 
def reconstruct(shares):
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
                prod = gmul(prod, gdiv(xi, (xi-xj) % FIELD_SIZE))
 
        prod = gmul(prod, yj)
        sums = gadd(sums, prod)
 
    return sums
 
 
def polynom(x, coefficients):
    """
    This generates a single point on the graph of given polynomial
    in `x`. The polynomial is given by the list of `coefficients`.
    """
    point = 0
    # Loop through reversed list, so that indices from enumerate match the
    # actual coefficient indices
    for coefficient_index, coefficient_value in enumerate(coefficients[::-1]):
        point = gadd(point, gmul(x ** coefficient_index % FIELD_SIZE, coefficient_value))
    return point
 
 
def coeff(t):
    """
    Randomly generate a list of coefficients for a polynomial with
    degree of `t` - 1, whose constant is `secret`.
 
    For example with a 3rd degree coefficient like this:
        3x^3 + 4x^2 + 18x + 554
 
        554 is the secret, and the polynomial degree + 1 is
        how many points are needed to recover this secret.
        (in this case it's 4 points).
    """
    coeff = [random.randrange(0, FIELD_SIZE) for _ in range(t - 1)]
    # coeff.append(secret)
    # coeff = [1]
    return coeff
 
def get_eval_points(n):
    '''
    get evaluation points for n parties
    '''
    return [1, 2, 3]
    # need unique evaluation points
    # temp = set()
    # while len(temp) != 3:
    #     temp.add(random.randrange(1, FIELD_SIZE))
    # return list(temp)
 
def generate_shares(coefficients, secret, eval_points):
    """
    Split given `secret` into `n` shares with minimum threshold
    of `m` shares to recover this `secret`, using SSS algorithm.
    """
    coefficients = list(coefficients)
    coefficients.append(secret)
    print("Coefficients: {}".format(coefficients))
    shares = [(x, polynom(x, coefficients)) for x in eval_points]
    print("Shares: {}".format(shares))
    return shares

# # Driver code
# if __name__ == '__main__':
 
#     # (3,5) sharing scheme
#     t, n = 3, 5
#     secret = 1234
#     print(f'Original Secret: {secret}')
 
#     # Phase I: Generation of shares
#     shares = generate_shares(n, t, secret)
#     print(f'Shares: {", ".join(str(share) for share in shares)}')
 
#     # Phase II: Secret Reconstruction
#     # Picking t shares randomly for
#     # reconstruction
#     pool = random.sample(shares, t)
#     print(f'Combining shares: {", ".join(str(share) for share in pool)}')
#     print(f'Reconstructed secret: {reconstruct_secret(pool)}')


# import random
# from elgamal import q as group_size

# alphas = []

# # Shamir Function
# def func(x, secret):
#     return x + secret

# def check_alphas():
#     if len(alphas) == 0:
#         return True
    
#     # Checking what we generate is all different
#     temp = alphas[0]
#     for i in range(1, alphas):
#         if temp == alphas[i]:
#             alphas.pop()
#             return True
#     return False


# # Generate evaluation points
# def gen_alphas():
#     while check_alphas():
#         alphas.append(random.randint(1, group_size - 1))

# # Get a share, based on party number
# def get_share(num):
#     return func(num)

# def shamir_share(value):
#     # Generate Alphas (Evaluation Points)
#     gen_alphas()
    
#     vals = []
#     for i in range(3):
#         vals.append(get_share(value))
#     return vals