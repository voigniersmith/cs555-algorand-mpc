# CS 555 Algorand Calculator <!-- omit from toc -->

## Table of Contents <!-- omit from toc -->

- [Usage](#usage)
- [Installation](#installation)
- [Languages \& Libraries](#languages--libraries)
- [PyTeal](#pyteal)
- [Protocol](#protocol)
- [Security](#security)
- [Virtual Python Environment](#virtual-python-environment)
- [PyTeal Course Comands](#pyteal-course-comands)
- [Definitions](#definitions)
- [Running the Debugger](#running-the-debugger)

***

## Usage

Welcome to our cryptographic calculator.

*The Client*  
&emsp;&emsp;Let's say the client has three numbers: 5, 0, and 7, let's call these $m_0$, $m_1$, and $m_2$. The client wants to know $(m_0 \cdot m_1) + m_2$, but without doing any work, instead they will pay someone else to do the work.  
&emsp;&emsp;Because the client doesn't trust any one entity with their money, they will use a smart contract, and put money on the contract to signify that the client wants work to be done. The computation parties will recognize this and wait to receive the encrypted information to do the work on. The client will then encrypt each number, as well as any necessary info, and send it to the parties, $p_0$, $p_1$, and $p_2$.  
&emsp;&emsp;The client then waits for the result. When the encrypted result is on the smart contract, the client then pulls it off, and decrypts to find the result of the equation.

*Computation Parties*  
&emsp;&emsp;The parties simply do the work without learning anything about $m_0$, $m_1$, or $m_2$. They then put the encrypted message on the smart contract, and take the money off the contract.

*The Smart Contract*  
&emsp;&emsp;Algorand and smart contract explained here

The goal is to calculate the equation: $(m_0 \cdot m_1) + m_2$ by using distributed computing power without any of the parties (who are doing the computation) knowing any information about what they are computing, besides the function that they compute.

*Commands*  

```bash
# Usage
python3 main.py

# Help
python3 main.py -h

# Options
 -h, --help         show this help message and exit
 -m, --messages     messages to pass in, up to 3, defaults to random
 -a, --algo         default True, use the algorand smart contract
 -p, --peek         party to watch, either 0, 1, 2
 -k, --kill         party to kill, either 0, 1, 2
 -s, --stage        stage to kill, either:
                        0 - after receiving cipher and share of key,
                        1 - after sharing during MPC,
                        2 - after computation, but before sending result,
                        3 - after receiving client payment
```

## Installation

Use the github i guess.

***

## Languages & Libraries

Languages

- Python
- PyTeal

Libraries

- multiprocessing
- algosdk.future
- algosdk
- algosdk.v2client
- pyteal
- Crypto.Util

***

## PyTeal

Edwin please

***

## Protocol

To do this, two protocols are used, ElGamal & Shamir's Secret Sharing.

  1. The public information is generated.
  2. Client encrypts message using ElGamal
       - Generate a random secret key
       - Use secret key to encrypt messages
  3. Client sends each party their encrypted message
  4. Each party then shares their ciphertext to the other parties
       - Party calculates a result using their shares
       - The share of the encrypted result is then sent to the other parties
       - Each party interpolates the result and notifies the client
  5. The client takes the encrypted result and decrypts it for the information.

***

## Security

*Goal*  
No party should be able to learn anything about $m_1$, $m_2$, $m_3$, $(m_1 \cdot m_2)$, or $(m_1 \cdot m_2) + m_3$.  

TODO: I also think there should be something about how an active adversary wouldn't be able to break the protocol given that one of the parties is killed.

*Analysis*  
How do I do a security analysis on this

***

## Virtual Python Environment

```python
# Initial venv setup
python -m venv venv

# Activate a venv
source ./venv/bin/activate

# Stop a venv
deactivate
```

***

## PyTeal Course Comands

```bash
# Setting up docker containers
./sandbox/sandbox up

# Close docker container
./sandbox/sandbox down

# Create contract handler
./build.sh contracts.counter.step_01

# Connecting to docker container
./sandbox enter <container name>

# Create application (smart contract) in container
goal app create --creator $ONE --approval-prog /data/build/approval.teal --clear-prog /data/build/clear.teal --global-byteslices 1 --global-ints 1 --local-byteslices 0 --local-ints 0

# check app info
goal app info --app-id <application index>

# Check the storage of application storage
goal app read --global --app-id <application index>

# Send a request to the smart contract
goal app call --app-id 8 --from $ONE --app-arg "str:inc"
```

***

## Definitions

- Application Account -> Where the ALGOS (currency) go and are then from

- tt -> Teal Type, there are only 2
  - tt == 2 -> uint64
  - tt == 1 -> byteslice

***

## Running the Debugger

While inside an application to generate a dry run for a debugger

```bash
goal app call --app-id 8 --from $ONE --app-arg "str:dec" --dryrun-dump -o tx.dr

tealdbg debug -d tx.dr --listen 0.0.0.0
```
