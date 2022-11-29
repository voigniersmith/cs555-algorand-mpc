import random

# Classes
class Shamir():
    def __init__(self, secret, group_size) -> None:
        # Save Function
        self.function = self.func()

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
        return x + self.secret

    # Get evaluation point using party number
    def get_alpha(self, num):
        return self.alpha[num]

    # Get a share, based on party number
    def get_share(self, num):
        return self.func(self.get_alpha(num))