import threading

class mpc():
    def __init__(self, group_size) -> None:
        self.group_size = group_size

    def group_add(x, y):
        return (x + y) % p

class client(threading.Thread):
    def __init__(self, thread_name, thread_ID):
        threading.Thread.__init__(self)
        self.thread_name = thread_name
        self.thread_ID = thread_ID

    def run(self):
        print(str(self.thread_name) + " " + str(self.thread_ID))

msg = "Hello, World!"
print(msg)

def client():
    print(msg + "I'm the client.")

def client():
    print(msg + "I'm the client.")