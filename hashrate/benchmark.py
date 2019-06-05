from agavepy.agave import Agave
import ast #used for dirty json conversion
import time

# creates agave stuff
class AgaveServer:

    def __init__(self):
        print('\nCreating Agave Server Object.')
        url = 'https://dev.tenants.aloedev.tacc.cloud/'
        key =  'gNxzmw6XqELNYLaL8VNf1ejJCTwa'
        secret = 'jL2CS0QCuyyUHH_qawWx5n80fzoa'

        self.ag = Agave(api_server=url, 
                        username='testuser7',
                        password='testuser7',
                        api_key =  key,
                        api_secret = secret)
        self.actor_id = None
        self.isSerial = None


    # registers serial actor
    def makeSerialActor(self, workers=6):
        print('\nMaking serial actor.')
        my_actor = {"image": 'kreshel/pow:abaco2', 
                    "name": 'mypow', 
                    "description": "Actor that runs a serial PoW benchmark."}
        actor = self.ag.actors.add(body=my_actor)
        aid = actor['id']

        self.isSerial = True
        self.actor_id = aid

    # adds to n workers
    def addWorkers(self, workers):
        print(f'\nAdding workers (total={workers}).')

        if self.isSerial:
            self.ag.actors.addWorker(actorId=self.actor_id, body={'num': workers})


    # registers parallel actor
    def makeParallelActor(self):
        print('\nMaking parallel actor.')
        my_actor = {"image": 'kreshel/pow:abaco', 
                    "name": 'mypow', 
                    "description": "Actor that runs a parallel PoW benchmark."}
        actor = self.ag.actors.add(body=my_actor)
        aid = actor['id']

        self.isSerial = False
        self.actor_id = aid


    # polls actor's status for actor and workers ready status
    def waitOnActor(self, workers):
        while True:
            if self.ag.actors.get(actorId=self.actor_id)['status'] == 'READY':
                if len(self.ag.actors.listWorkers(actorId=self.actor_id)) >= workers:
                    print('Actor ready.')
                    return
                else:
                    print('Waiting for workers to get ready..')
                    time.sleep(1)
            else:
                print('Waiting for actor to get ready..')
                time.sleep(1)

    # checks how many workers each node has
    def checkWorkers(self):
        workers = self.ag.actors.listWorkers(actorId=self.actor_id)

        node_workers = dict()

        for worker in workers:
            if worker['hostId'] in node_workers:
                node_workers[worker['hostId']] += 1
            else:
                node_workers[worker['hostId']] = 1

        print(f'Node/Worker split: {node_workers}')
        return node_workers


    # deletes an actor
    def deleteActor(self):
        print('Deleting actor.')
        self.ag.actors.delete(actorId=self.actor_id)


    # lists registered actors
    def listActors(self):
        print('Listing actors.')
        print(self.ag.actors.list())


    # polls at certain rate for ready worker status; flagged by isDone
    def waitOnWorkers(self, interval=0.5, timeout=1800):
        begin = time.time()
        while True:
            isDone = True

            # gets worker status
            workers = self.ag.actors.listWorkers(actorId=self.actor_id)

            # says is not done if html request takes too long
            if not workers:
                isDone = False

            # checks each workers' status
            for worker in workers:
                if worker['status'] != 'READY':
                    isDone = False

            # exit condition
            if isDone:
                return workers

            # timeout
            if (time.time()-begin) > timeout:
                print('Timed Out!')
                raise 
            time.sleep(interval)

    # benchmark
    def benchmark(self, msgs=1, bits=20, cores=1, block_count=1):
        # list of execution ids
        execs = []

        # message for execution; depends on parallel or serial
        if self.isSerial:
            message = f'{{"bits":{bits}}}'
        else:
            message = f'{{"blocks": {block_count},"bits": {bits},"cores": {cores}}}'

        # waits until actor's workers are ready for new messages
        self.waitOnWorkers()

        ### runs the benchmark ###
        msg_start = time.time()
        for i in range(msgs):
            execution = self.ag.actors.sendMessage(actorId=self.actor_id, body=message)
            exec_id = execution['executionId']
            execs.append(exec_id)
        msg_end = time.time()

        # Polling workers for task completion
        task_start = time.time()
        workers = self.waitOnWorkers(interval=0.25)
        task_end = time.time()

        # test to make sure workers are actually ready
        for worker in workers:
            assert worker['status'] == 'READY'

        # calling log executions for results
        runtimes = []
        hashrates = []
        hashes = []
        for eid in execs:
            log = self.ag.actors.getExecutionLogs(actorId=self.actor_id, executionId=eid)['logs']
            if log:
                log_json = ast.literal_eval(log)
                runtimes.append(log_json['runtime'])
                hashrates.append(log_json['hashrate'])
                hashes.append(log_json['hashes'])

        # return benchmark for particular inputs
        return {'msgs': msgs,
                'bits': bits,
                'cores': cores,
                'block_count': block_count,
                'msgtime': f'{msg_end-msg_start}',
                'clocktime': f'{sum(runtimes)}', 
                'tasktime': f'{task_end-task_start}', 
                'hashes': f'{sum(hashes)}', 
                'hashrate': f'{sum(hashes)/(task_end-task_start):.3e}'
                }

    ### WIP; unfinished verification for each execution/block ###
    def verify(self, execs):
        import hashlib
        for eid in execs:
            log = self.ag.actors.getExecutionLogs(actorId=self.actor_id, executionId=eid)['logs']
            if log:
                log_json = ast.literal_eval(log)
                genesis_block = log_json['genesis_block']
                next_block = log_json['next_block']

            block_serialization = json.dumps(genesis_block, sort_keys=True).encode('utf-8')
            block_hash = hashlib.sha256(block_serialization).hexdigest()

            assert (block_hash == next_block)

def main():
    # maxes out workers on number of nodes(6 workers per medium node)
    nodes = int(input('How many nodes are active? '))
    N = nodes*6

    # creates server and actor
    myserver = AgaveServer()
    actorStart = time.time()
    myserver.makeSerialActor()
    myserver.addWorkers(workers=N)
    #myserver.makeParallelActor()

    # waits for actor to get ready
    myserver.waitOnActor(workers=N)
    myserver.checkWorkers()
    actorReadyTime = time.time()-actorStart

    # I/O for results
    with open('benchresults.txt', 'a+') as f:
        f.write('~~~~~~~~~~~~~~~~~~\n')
        f.write(f'Actor Ready Time: {actorReadyTime:.4}s\n\n')
        if myserver.isSerial == True:
            f.write(f'Testing on serial image at {time.ctime()}\n')
        else:
            f.write(f'Testing on parallel image at {time.ctime()}\n')
        f.write('Benchmark Results:\n\n')

        ###### CHANGE THIS FOR SERIAL/PARALLEL #####
        for i in range(20):
            print(f'\nRunning Trial {i+1}..')
            f.write(f'{myserver.benchmark(msgs=nodes*30, bits=20)}\n')
            #f.write(f'{myserver.benchmark(bits=20, cores=6, block_count=10)}\n')
        ############################################

        f.write('\n\n')

    # deletes actor
    myserver.deleteActor()

if __name__ == '__main__':
    main()