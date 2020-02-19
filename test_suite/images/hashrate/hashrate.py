import os
import time
import json
import hashlib
from uuid import uuid4

# Creates random genesis block to be used in SHA256 function
def randomBlock(prev_hash=None, hashes=0, transactions=str(uuid4()), nonce=0):
    return {'prev_hash': prev_hash,
            'hashes': hashes,
            'transactions': transactions,
            'nonce': nonce,}


# Hashes an encoded JSON object (our genesis block)
def hashBlock(block):
    block_serialization = json.dumps(block, sort_keys=True).encode('utf-8')
    block_hash = hashlib.sha256(block_serialization).hexdigest()

    return block_hash


# Hashes until an inputted number of hashes is completed
def mineNextBlock(prev_block, num_hashes):
    # For Abaco performance study, num_hashes = 3,000,000
    for nonce in range(num_hashes+1):
        hashy = hashBlock(prev_block)
        prev_block['nonce'] = prev_block['nonce'] + 1

    return randomBlock(prev_hash=hashy, hashes=nonce)


def main():
    start = time.time()
    logs = {}
    #num_hashes = int(os.getenv('MSG'))
    num_hashes=3000000
    genesis_block = randomBlock()
    print(time.time() - start)
    next_block = mineNextBlock(genesis_block, num_hashes)

    end = time.time()
    hashrate = next_block['hashes']/(end-start)

    # writing logs
    logs['runtime'] = end-start
    logs['hashrate'] = hashrate
    logs['hashes'] = next_block['hashes']

    # sends logs to execution/logs
    print(logs,end='')


if __name__ == '__main__':
    main()
