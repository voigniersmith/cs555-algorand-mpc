def ginv(x, p):
    t = 0
    new_t = 1
    r = p
    new_r = x
    while new_r != 0:
        quotient = r // new_r
        t, new_t = (new_t, t - quotient * new_t)
        r, new_r = (new_r, r - quotient * new_r)
    if t < 0:
        t = t + p
    return t

def gadd(x, y, p):
    return (x + y) % p

def gmul(x, y, p):
    return (x * y) % p

def gdiv(x, y, p):
    return (x * ginv(y)) % p