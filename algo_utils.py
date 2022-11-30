import base64

from algosdk.future import transaction
from algosdk import mnemonic
from algosdk.v2client import algod
from pyteal import *

from conf import party_mnemonic, client_mnemonic

# DO NOT CHANGE
algod_token = 'a' * 64
algod_address = 'http://localhost:4001'
client = algod.AlgodClient(algod_token, algod_address)

# user declared account mnemonics
benefactor_mnemonic = party_mnemonic
sender_mnemonic = client_mnemonic

# helper function to compile program source
def compile_smart_signature(client, source_code):
    compile_response = client.compile(source_code)
    return compile_response['result'], compile_response['hash']

# helper function that converts a mnemonic passphrase into a private signing key
def get_private_key_from_mnemonic(mn) :
    private_key = mnemonic.to_private_key(mn)
    return private_key

def payment_transaction(creator_mnemonic, amt, rcv, algod_client)->dict:
    params = algod_client.suggested_params()
    add = mnemonic.to_public_key(creator_mnemonic)
    key = mnemonic.to_private_key(creator_mnemonic)
    unsigned_txn = transaction.PaymentTxn(add, params, rcv, amt)
    signed = unsigned_txn.sign(key)
    txid = algod_client.send_transaction(signed)
    pmtx = transaction.wait_for_confirmation(algod_client, txid , 5)
    return pmtx

def lsig_payment_txn(escrowProg, escrow_address, amt, rcv, algod_client):
    params = algod_client.suggested_params()
    unsigned_txn = transaction.PaymentTxn(escrow_address, params, rcv, amt)
    encodedProg = escrowProg.encode()
    program = base64.decodebytes(encodedProg)
    lsig = transaction.LogicSigAccount(program)
    stxn = transaction.LogicSigTransaction(unsigned_txn, lsig)
    tx_id = algod_client.send_transaction(stxn)
    pmtx = transaction.wait_for_confirmation(algod_client, tx_id, 10)
    return pmtx

"""Basic Donation Escrow"""
def donation_escrow(benefactor):

    #Only the benefactor account can withdraw from this escrow
    program = And(
        Txn.type_enum() == TxnType.Payment,
        Txn.receiver() == Addr(benefactor),
        Global.group_size() == Int(1),
        Txn.rekey_to() == Global.zero_address()
    )

    # Mode.Signature specifies that this is a smart signature
    return compileTeal(program, Mode.Signature, version=5)

def get_client():
    # initialize an algodClient
    client = algod.AlgodClient(algod_token, algod_address)

def main() :
    # initialize an algodClient
    algod_client = algod.AlgodClient(algod_token, algod_address)

    # define private keys
    receiver_public_key = mnemonic.to_public_key(benefactor_mnemonic)

    print("--------------------------------------------")
    print("Compiling Donation Smart Signature......")

    stateless_program_teal = donation_escrow(receiver_public_key)
    escrow_result, escrow_address= compile_smart_signature(algod_client, stateless_program_teal)

    # print(result)
    print("Program:", escrow_result)
    print("hash: ", escrow_address)

    print("--------------------------------------------")
    print("Activating Donation Smart Signature......")

    # Activate escrow contract by sending 2 algo and 1000 microalgo for transaction fee from creator
    amt = 2
    payment_transaction(sender_mnemonic, amt, escrow_address, algod_client)

    print("--------------------------------------------")
    print("Withdraw from Donation Smart Signature......")

    # Withdraws 1 ALGO from smart signature using logic signature.
    withdrawal_amt = 2
    lsig_payment_txn(escrow_result, escrow_address, withdrawal_amt, receiver_public_key, algod_client)

main()