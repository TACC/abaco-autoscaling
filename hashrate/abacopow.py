# "Flop is floating operation. Hashing is integer operation"
# Have not linked blocks together

from uuid import uuid4
from agavepy.actors import get_context
import json, time, hashlib, os

MAX_NONCE = 2**32       # global max nonce; maximum attempts before failing to find next block
                        # 32-bit system

# creates random block
def randomBlock(prev_hash=None, hashes=0, transactions=str(uuid4()), bits=10, nonce=0):
    return {
            'prev_hash': prev_hash,
            'hashes': hashes,
            'transactions': transactions, 
            'bits': bits, 
            'nonce': nonce,
            }


# Hashes an encoded json object (our block)
def hashBlock(block):
    block_serialization = json.dumps(block, sort_keys=True).encode('utf-8')
    block_hash = hashlib.sha256(block_serialization).hexdigest()

    return block_hash


# Mines/hashes until the desired hash is found
def mineNextBlock(prev_block, start_nonce=0, end_nonce=MAX_NONCE):
    prev_block = copy.deepcopy(prev_block)
    prev_block['nonce'] = start_nonce        # initiates new start nonce
    bits = prev_block['bits']                # pulls the bit value from the block
    target = 2 ** (256 - bits)                  # target value (difficulty determined by bits)

    # attempts max_nonce times to find hash/int that's less than target
    for nonce in range(start_nonce, end_nonce):
        hashy = hashBlock(prev_block)

        if int(hashy, 16) < target:
            return randomBlock(prev_hash=hashy, hashes=nonce, bits=bits)

        prev_block['nonce'] = prev_block['nonce'] + 1

    print(f'Failed after {MAX_NONCE} (max_nonce) tries\n')
    return randomBlock(prev_hash='FAILED', bits=bits, nonce=MAX_NONCE)

def main():
    start = time.time()
    logs = {}
    logs['messages'] = f'Max Cores: {os.cpu_count()}'

    # intializes core count, bit difficulty, and blockchain length
    context = get_context()
    try:
        n_bits = int(context['message_dict']['bits'])
    except Exception:
        logs['messages'] += 'Didnt get any/valid values.. using default values..'
        n_bits=10

    logs['messages'] = f' Mining a {n_bits}-bit block to the next block on 1 core..'

    #####
    genesis_block = randomBlock(bits=n_bits)
    next_block = mineNextBlock(genesis_block)
    #####

    hashrate = next_block['hashes']/(end-start)
    end = time.time()

    # writing logs
    logs['genesis_block'] = str(genesis_block)
    logs['next_block'] = str(next_block)
    logs['runtime'] = end-start
    logs['hashrate'] = hashrate
    logs['hashes'] = next_block['hashes']

    # sends logs to execution/logs
    print(logs,end='')

if __name__ == '__main__':
    main()



