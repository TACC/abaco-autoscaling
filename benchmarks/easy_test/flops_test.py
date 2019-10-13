"""
Testing flops 24/7/365.
"""
import os
import time 
import multiprocessing
import numpy as np
import pandas as pd
import requests as r
from datetime import datetime
from dateutil.parser import parse


JWT = open('jwt.txt', 'r').read()
HEADER_DAT = {'x-JWT-assertion-dev': JWT}
URL = "http://129.114.104.189/actors"


# Does a batch of runs - Amount of runs is specified along with batch properties
def flop_batch_tester(actor_id, nodes, runs, workers_per_node, messages_per_worker, threads, std_dev, size)
    executions = nodes * workers_per_node * messages_per_worker
    msg_dat = f'{threads} {std_dev} {size}'

    messager_inp = [actor_id, HEADER_DAT, msg_dat, URL]
    messager_iterator = [messager_inp] * executions

    all_data = pd.DataFrame()

    # Message sending function for parallel messaging functionality
    def send_actor_message(it):
        msg_send = r.post(f"{it[3]}/{it[0]}/messages",
                          headers=it[1], data={'message': it[2]})
        return msg_send.json()['result']['executionId']

    # Runs a specified amount of runs
    for run_num in range(1, runs + 1):
        print('')
        print(f'Starting Run {run_num}.')
        
        # Message sending using pool multiprocessing
        pool = multiprocessing.Pool(processes=16)
        msg_start = time.time()
        exec_id_list = pool.map(send_actor_message, messager_iterator)
        pool.close()
        pool.join()
        msg_end = time.time()
        print(f'Messaging complete and took {msg_end - msg_start}')

        post_msg_start = time.time()
        non_complete_list = exec_id_list.copy()
        executions_completed = 0
        print('Waiting a bit to prevent timeout issues')
        print(f'\rExecutions completed: {executions_completed}', end='')
        time.sleep(.5 * nodes)
        while non_complete_list:
            all_exec_reses = r.get(f"{URL}/{actor_id}/executions",
                                   headers=HEADER_DAT).json()
            for exec_res in all_exec_reses['result']['executions']:
                exec_id = exec_res['id']
                if (exec_id in non_complete_list) and (exec_res['status'] == 'COMPLETE'):
                    executions_completed += 1
                    print(f'\rExecutions completed: {executions_completed}', end='')
                    non_complete_list.remove(exec_id)

        post_msg_end = time.time() 

        msg_time = msg_end - msg_start
        post_msg_time = post_msg_end - post_msg_start
     
        print('\nDoing analytics.')
        results_list = []
        whole_work_times = 0
        calc_times = 0
        exec_init_times = 0
        exec_run_times = 0
        for exec_id in exec_id_list:
            exec_logs = r.get(f"{URL}/{actor_id}/executions/{exec_id}/logs",
                              headers=HEADER_DAT).json()['result']['logs']
            whole_work_time, calc_time = list(map(float, exec_logs.replace('\n','').split()))
            whole_work_times += whole_work_time
            calc_times += calc_time

            exec_res = r.get(f"{URL}/{actor_id}/executions/{exec_id}",
                             headers=HEADER_DAT).json() ['result']
            msg_receive_time = parse(exec_res['messageReceivedTime'].replace(' ','T') + 'Z')
            exec_start_time = parse(exec_res['startTime'].replace(' ', 'T') + 'Z')
            exec_start_run_time = parse(exec_res['finalState']['StartedAt'])
            exec_end_run_time = parse(exec_res['finalState']['FinishedAt'])

            exec_init_time = (exec_start_run_time - exec_start_time).total_seconds()
            exec_run_time = (exec_end_run_time - exec_start_run_time).total_seconds()
            
            exec_init_times += exec_init_time
            exec_run_times += exec_run_time
        
        print(f"\n\nRun Number {run_num}")
        if threads:
            print(f"Threads: {threads}")
        print(f"Std Dev: {std_dev}")
        print(f"Size: {size}")
        print(f"Executions: {executions}")
        print(f"Message Time: {msg_time}")
        print(f"Post Msg Time: {post_msg_time}")
        print(f"Abaco Exec Init Time: {exec_init_times}")
        print(f"Abaco Exec Run Time: {exec_run_times}")
        print(f"Whole Work Time: {whole_work_times}")
        print(f"Calc Time: {calc_times}")

        run_data = pd.DataFrame(
            [[run_num, threads, std_dev, size, executions, msg_time, post_msg_time,
              exec_init_times, exec_run_times, whole_work_times, calc_times]],
            columns=['Run Number', 'Threads', 'Std Dev', 'Size', 'Executions',
                     'Message Time', 'Post Message Time', 'Exec Init Time',
                     'Exec Run Time', 'Whole Work Time', 'Calc Time'])
        all_data = all_data.append(run_data, ignore_index = True)
    # Checks if data folders exist, if they don't create them 
    if not os.path.isdir(f'data/{workers_per_node}'):
        os.mkdirs(f'data/{workers_per_node}')
    # Saves pandas analytics dataframe to csv in data folder
    all_data.to_csv(f'data/{workers_per_node}_workers/{nodes}_nodes_{workers_per_node}_workers_{runs}_trials.csv')


# Create actor for work
def create_actor():
    actor = r.post(f"{url}",
                   headers=header_dat,
                   data={"image":"notchristiangarcia/flops_test:6.0",
                         "default_environment":{"WAIT": "1"}})
    actor_id = actor.json()['result']['id']
    return actor_id


# Create workers for actor in batches of 'incr' to ensure no timeouts
def create_workers(actor_id, num_nodes):
    try:
        start_workers = time.time()
        workers_needed = num_nodes*6
        curr_workers = 0
        incr = 50
        while workers_needed != curr_workers:
            if curr_workers + incr > workers_needed:
                curr_workers += (workers_needed - curr_workers) % incr
            else:
                curr_workers += incr

            print(f'Getting {curr_workers} workers')
            spool_res = r.post(f"{URL}/{actor_id}/workers",
                                headers=HEADER_DAT,
                                data={'num': curr_workers})
    except Exception as e:
        print(time.time() - start_workers, e)


# Delete workers to ensure they properly get destroyed and don't just hangout
def delete_workers(actor_id):
    while True:
        worker_res = r.get(f"{URL}/{actor_id}/workers",
                           headers=HEADER_DAT)
        all_workers == worker_res.json()['results']
        if not all_workers == 0:
            for worker_info in all_workers:
                del_worker_res = r.delete(f"{URL}/{actor_id}/workers/{worker_info['id']}",
                                    headers=HEADER_DAT)
        else:
            break


# Deletes the actor once workers are deleted.
def delete_actor(actor_id):
    r.delete(f"{URL}/{actor_id}", headers=HEADER_DAT)


def main():
    # Queries
    num_nodes = input("How many nodes are running? ")
    runs = 5
    threads = 0        # set to 0 for all threads

    # First batch of runs: six workers per node, easy work.
    # Create Actor
    actor_id = create_actor()
    # Create Workers
    create_workers(actor_id, num_nodes)
    # Run Test
    flop_tester(actor_id, num_nodes, runs, workers_per_node=6, messages_per_worker=5, threads, std_dev=1000, size=16000) 
    # Delete Workers
    delete_workers(actor_id)
    # Delete Actor
    delete_actor(actor_id)


    # Second batch of runs: 1 worker per node, hard work.
    # Create Actor
    actor_id = create_actor()
    # Create Workers
    create_workers(actor_id, num_nodes)
    # Run Test
    flop_tester(actor_id, num_nodes, runs, workers_per_node=1, messages_per_worker=1, threads, std_dev=1000, size=25000) 
    # Delete Workers
    delete_workers(actor_id)
    # Delete Actor
    delete_actor(actor_id)


if __main__ == '__init__':
    main()
