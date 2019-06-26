from agavepy.agave import Agave
import ast
import time
from multiprocessing import Pool
import requests as r
from datetime import datetime
from dateutil.parser import parse


#### GLOBAL STUFF :( ####
AG = None
ACTOR_ID = ''
MESSAGE = ''


# creates agave stuff
def hashBlock(block):
    block_serialization = json.dumps(block, sort_keys=True).encode('utf-8')
    block_hash = hashlib.sha256(block_serialization).hexdigest()

    return block_hash


def timeFunction(msgs):
    msg_start = time.time()
    pool = Pool(processes=16)
    result = pool.map(sendMessage, range(msgs))
    msg_end = time.time()
    pool.close()
    pool.join()

    return [msg_end-msg_start, result]


def sendMessage(iterator):
    msg_timeout = time.time()
    try:
        execution = r.post(f"https://dev.tenants.aloedev.tacc.cloud/actors/v2/{ACTOR_ID}/messages",
                       headers={'Authorization': 'Bearer 74b1aaf8ca3f131071be811964fd2987'},
                       data={'message':f'{MESSAGE}'})
        #time.sleep(0.1)
        return [execution.json()['result']['executionId'], time.time()-msg_timeout]
    except Exception as e:
        print('Message send failed:', e)
        print('Time:', time.time()-msg_timeout)
        return [None, -1]


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
        global AG
        AG = self.ag
        self.actor_id = None
        self.execs = []


    # registers actor
    def makeActor(self, image='kreshel/pow:3'):
        print('\nMaking actor.')
        my_actor = {"image": f'image',      ################## 
                    "name": 'mypow', 
                    "description": "Actor that runs a PoW benchmark."}
        actor = self.ag.actors.add(body=my_actor)
        aid = actor['id']

        self.actor_id = aid
        global ACTOR_ID
        ACTOR_ID = self.actor_id


    # lists registered actors
    def listActors(self):
        print('Listing actors.')
        print(self.ag.actors.list())


    # deletes an actor
    def deleteActor(self, attempts=5):
        print('\nDeleting actor.')
        for attempt in range(attempts):
            all_actors = self.ag.actors.list()
            aids = []
            for item in all_actors:
                aids.append(item['id'])
            if self.actor_id not in aids:
                break
            try:
                self.ag.actors.delete(actorId=self.actor_id)
            except:
                print(f'Failed to delete actor on attempt {attempt+1}. Retrying..')


    # adds to n workers; 100 at a time
    def addWorkers(self, workers):
        if workers > 100:
            temp_workers = 0
            while temp_workers < workers:
                if (temp_workers+100) > workers:
                    temp_workers += (workers-temp_workers)
                else:
                    temp_workers += 100

                print(f'\nAdding workers (total={temp_workers}).')
                worker_timeout = time.time()
                try:
                    self.ag.actors.addWorker(actorId=self.actor_id, body={'num': temp_workers})
                    self.waitOnWorkers()
                    self.checkAmount()
                except:
                    print('Adding workers failed.')
                    print('Time:', time.time()-worker_timeout)
                    raise

        else:
            print(f'\nAdding workers (total={workers}).')
            self.ag.actors.addWorker(actorId=self.actor_id, body={'num': workers})
            self.waitOnWorkers()
            self.checkAmount()

    def workerTest(self,workers):
        for i in range(workers):
            print(f'\nAdding workers (total={i}).')
            self.ag.actors.addWorker(actorId=self.actor_id, body={'num': i})
            self.waitOnWorkers()


    # polls actor's status for actor and workers ready status
    def waitOnActor(self, num_workers):
        while True:
            if self.ag.actors.get(actorId=self.actor_id)['status'] == 'READY':
                print('\nWaiting on workers to get ready..')
                self.waitOnWorkers()
                assert len(self.ag.actors.listWorkers(actorId=self.actor_id)) == num_workers
                print('Actor ready.')
                return
            else:
                print('\nWaiting for actor to get ready..')
                time.sleep(1)


    # check amount of workers that have hostIds
    def checkAmount(self):
        workers = self.ag.actors.listWorkers(actorId=self.actor_id)
        num_workers = 0


        for worker in workers:
            try:
                if worker['hostId']:
                    num_workers += 1
            except:
                pass

        print('Total Number of Workers:', num_workers)


    # checks how many workers each node has and total number of active nodes
    def checkWorkers(self):
        workers = self.ag.actors.listWorkers(actorId=self.actor_id)

        node_workers = dict()

        for worker in workers:
            if worker['hostId'] in node_workers:
                node_workers[worker['hostId']] += 1
            else:
                node_workers[worker['hostId']] = 1

        print(f'Node/Worker split: {node_workers}')
        print(f'Number of actives nodes: {len(node_workers.keys())}')
        return node_workers


    # polls at certain rate for ready worker status; flagged by isDone
    def waitOnWorkers(self, interval=0.5, timeout=1800):
        print('Polling Workers..')
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
                print(workers)
                raise 
            time.sleep(interval)


    # benchmark ~1e6 hashes takes 1 minute
    def benchmark(self, msgs=1, num_hashes=1000000):
        # list of execution ids
        execs = []

        # Message for execution
        global MESSAGE
        MESSAGE = str(num_hashes)

        # Waits until actor's workers are ready for new messages
        print('\nChecking if workers are actually ready..')
        self.waitOnWorkers()

        # Sends messages for workers
        print('\nSending messages..')
        message_stuff = timeFunction(msgs)
        print('msgsendtime', message_stuff[0])
        wow = list(map(list, zip(*message_stuff[1])))
        msg_times = wow[1]

        #print(msg_times)

        # Polling workers for task completion
        print('\nWaiting for task completion..')
        clock_start = time.time()
        workers = self.waitOnWorkers(interval=0.25, timeout=300)
        clock_end = time.time()
        print(f'Clocktime: {clock_end-clock_start}')

        # test to make sure workers are actually ready
        for worker in workers:
            assert worker['status'] == 'READY'

        # Calling log executions for results
        worktimes = []
        hashes = []
        abaco_inittimes = []
        abaco_worktimes = []
        startedAts = []
        finishedAts = []

        eids = wow[0]
        print(f'\nRetrieving {len(eids)} results..')
        retrieval_start = time.time()
        for eid in eids:
            log = self.ag.actors.getExecutionLogs(actorId=self.actor_id, executionId=eid)['logs']
            exec_results = self.ag.actors.getExecution(actorId=self.actor_id, executionId=eid)
            if log:
                log_json = ast.literal_eval(log)
                worktimes.append(log_json['runtime'])
                hashes.append(log_json['hashes'])

            if exec_results['finalState']:
                receivedTime = parse(exec_results['messageReceivedTime'].replace(' ','T')+'Z')
                startTime = parse(exec_results['startTime'].replace(' ','T')+'Z')
                startedAt = parse(exec_results['finalState']['StartedAt'])
                finishedAt = parse(exec_results['finalState']['FinishedAt'])

                abaco_inittimes.append((startedAt-startTime).total_seconds())
                abaco_worktimes.append((finishedAt-startedAt).total_seconds())
                startedAts.append((startedAt-startTime).total_seconds())
                finishedAts.append((finishedAt-startTime).total_seconds())

        print(f'Retrieval Time: {time.time()-retrieval_start}')


        # Return benchmark for particular inputs
        return {'msgs': msgs,
                'msgtime': message_stuff[0],
                'worktime': f'{sum(worktimes)/len(worktimes)}',  
                'abaco_inittime': f'{sum(abaco_inittimes)/len(abaco_inittimes)}',
                'abaco_worktime': f'{sum(abaco_worktimes)/len(abaco_worktimes)}',
                'startedAts': f'{sum(startedAts)/len(startedAts)}',
                'finishedAts': f'{sum(finishedAts)/len(finishedAts)}',
                'clocktime': f'{clock_end-clock_start}',
                'hashes': f'{sum(hashes)}', 
                'hashrate': f'{sum(hashes)/(clock_end-clock_start):.3e}'
                }


def main():
    # maxes out workers on number of nodes(6 workers per medium node)
    nodes = int(input('How many nodes are active? '))
    cores = 6
    N = nodes*cores

    # creates server and actor
    myserver = AgaveServer()

    actorStart = time.time()
    myserver.makeActor(image='kreshel/pow:3')
    try:
        myserver.addWorkers(workers=N)
        print(f'Worker Time: {time.time()-actorStart}')
    except:
        myserver.deleteActor()
        raise

    # waits for actor to get ready
    myserver.waitOnActor(num_workers=N)
    node_workers = myserver.checkWorkers()
    actorReadyTime = time.time()-actorStart

    # I/O for results
    with open('results.txt', 'a+') as f:
        f.write(f'\n~~~~~~~~~~~~~~~~~~\n'
                f'Actor Ready Time: {actorReadyTime:.4}s\n\n'
                f'Testing on image at {time.ctime()}\n'
                f'{N} worker(s) on {len(node_workers.keys())} node(s)\n'
                f'Benchmark Results:\n\n')

        for i in range(10):
            print(f'\n~~~~~~~~~~~~~~~~~~~~~~~~~~Running Trial {i+1}~~~~~~~~~~~~~~~~~~~~~~~~~~')
            try:
                f.write(f'{myserver.benchmark(msgs=N*3, num_hashes=3000000)}\n')
            except:
                myserver.deleteActor()
                raise

        f.write('\n\n')

    # deletes actor
    myserver.deleteActor()


if __name__ == '__main__':
    main()