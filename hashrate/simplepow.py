from uuid import uuid4
import json, time, hashlib, os


# creates random block
def randomBlock(prev_hash=None, hashes=0, transactions=str(uuid4()), nonce=0):
    return {
            'prev_hash': prev_hash,
            'hashes': hashes,
            'transactions': transactions,
            'nonce': nonce,
            }


# Hashes an encoded json object (our block)
def hashBlock(block):
    block_serialization = json.dumps(block, sort_keys=True).encode('utf-8')
    block_hash = hashlib.sha256(block_serialization).hexdigest()

    return block_hash


# Mines/hashes until the desired hash is found
def mineNextBlock(prev_block, num_hashes):
    # hashes 5000000 times
    for nonce in range(num_hashes+1):
        hashy = hashBlock(prev_block)
        prev_block['nonce'] = prev_block['nonce'] + 1

    return randomBlock(prev_hash=hashy, hashes=nonce)


def main():
    start = time.time()
    logs = {}
    num_hashes = int(os.getenv('MSG'))

    #####
    genesis_block = randomBlock()
    next_block = mineNextBlock(genesis_block, num_hashes)
    #####

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