import json
import multiprocessing
import os
import sys
import requests
import time
import timeit
import pandas as pd
from datetime import datetime
from dateutil.parser import parse


TRIAL_TYPE = int(sys.argv[1])

NUM_NDOES = NUM_ACTORS = int(sys.argv[1])
TRIAL_NUM = int(sys.argv[2])
AUTOSCALING = sys.argv[3].lower() = 'true'
HASHES = int(sys.argv[4])
NUM_WORKERS_PER_ACTOR = int(sys.argv[5])
NUM_MESSAGES_PER_WORKER = int(sys.argv[6])
NUM_MESSAGES_PER_ACTOR = NUM_WORKERS_PER_ACTOR * NUM_MESSAGES_PER_WORKER

with open('jwt-abaco_admin', 'r') as f:
    JWT_DEFAULT = f.read()
HEADERS = {'X-Jwt-Assertion-DEV': JWT_DEFAULT}
BASE = 'http://129.114.104.189'

def register_actor(idx):
    data = {'image': 'kreshel/pow:3', 'name': f'abaco_hash_test_{idx}'}
    rsp = requests.post(f'{BASE}/actors', data=data, headers=HEADERS)
    result = basic_response_checks(rsp)
    return result['id']

def start_workers(aid, num_workers):
    data = {'num': num_workers}
    rsp = requests.post(f'{BASE}/actors/{aid}/workers', data=data, headers=HEADERS)
    result = basic_response_checks(rsp)

def check_for_ready(actor_ids):
    """
    Check for READY status of each actor in the actor_ids list.
    :param actor_ids:
    :return:
    """
    for aid in actor_ids:
        # check for workers to be ready
        idx = 0
        ready = False
        while not ready and idx < 60:
            url = '{}/actors/{}/workers'.format(BASE, aid)
            rsp = requests.get(url, headers=HEADERS)
            result = basic_response_checks(rsp)
            for worker in result:
                if not worker['status'] == 'READY':
                    idx = idx + 1
                    time.sleep(2)
                    continue
                ready = True
        if not ready:
            print("ERROR - workers for actor {} never entered READY status.")
            raise Exception()
        # now check that the actor itself is ready -
        ready = False
        idx = 0
        while not ready and idx < 10:
            purl = '{}/actors/{}'.format(BASE, aid)
            rsp = requests.get(url, headers=HEADERS)
            result = basic_response_checks(rsp)
            if result['status'] == 'READY':
                ready = True
                break
            idx = idx + 1
            time.sleep(1)
        if not ready:
            print("ERROR - actor {} never entered READY status.")
            raise Exception()
        print(f"workers and actor ready for actor {aid}")

def get_actors():
    """
    Helper script that can return that actor_ids associated with this test suite.
    :return:
    """
    aids = []
    url = '{BASE}/actors'
    rsp = requests.get(url, headers=HEADERS)
    result = basic_response_checks(rsp)
    for actor in result:
        if 'abaco_flops_test_' in actor.get('name'):
            aids.append(actor.get('id'))
    return aids

def get_executions(actor_ids):
    ex_ids = {}
    for a in actor_ids:
        ex_ids[a] = []
        url = 'f{BASE}/actors/{a}/executions'
        rsp = requests.get(url, headers=HEADERS)
        result = basic_response_checks(rsp)
        for ex in result['executions']:
            ex_ids[a].append(ex['id'])
    return ex_ids

def send_one_message(actor_ids):
    prime_execution_ids = {}
    for idx, aid in enumerate(actor_ids):
        prime_execution_ids[aid] = []
        url = '{}/actors/{}/messages'.format(BASE, aid)
        rsp = requests.post(url, data={'message': 'PURPOSEFUL_BREAKING_MESSAGE'.format(idx)}, headers=HEADERS)
        result = basic_response_checks(rsp)
        ex_id = result['execution_id']
        print("Priming actor id {}; message {}; execution id: {}".format(aid, idx, ex_id))
        prime_execution_ids[aid].append(ex_id)
    print("All primer messages sent.")

def send_messages(actor_ids, num_messages_per_actor):
    execution_ids = {}
    for idx, aid in enumerate(actor_ids):
        execution_ids[aid] = []
        url = '{}/actors/{}/messages'.format(BASE, aid)
        for j in range(num_messages_per_actor):
            rsp = requests.post(url, data={'message': 'test_{}_{}'.format(idx, j)}, headers=HEADERS)
            result = basic_response_checks(rsp)
            ex_id = result['execution_id']
            print("Send actor id {} message {}_{}; execution id: {}".format(aid, idx, j, ex_id))
            execution_ids[aid].append(ex_id)
    return execution_ids

def _thread_send_actor_message(url):
    data = {'message': HASHES}
    try:
        rsp = requests.post(url, headers=HEADERS, data=data)
    except Exception as e:
        print(f"got exception trying to send message to {url}; exception: {e}")
    try:
        result = rsp.json()['result']['execution_id']
    except Exception as e:
        print(f"got exception trying to assign execID to result; rsp: {rsp}; exception: {e}")
    return url.replace('messages', 'executions/') + result

def send_messages_threaded(actor_ids, num_messages_per_actor):
    POOL_SIZE = os.environ.get('POOL_SIZE', 16)
    print(f"using pool of size: {POOL_SIZE}")
    pool = multiprocessing.Pool(processes=POOL_SIZE)
    # this is a list with a URL for every message we want to send
    urls = [f'{BASE}/actors/{aid}/messages' for aid in actor_ids] * num_messages_per_actor
    execution_urls = pool.map(_thread_send_actor_message, urls)
    pool.close()
    pool.join()
    print(f'All {len(actor_ids) * num_messages_per_actor} messages sent')
    return execution_urls

def check_for_complete(actor_ids):
    done_actors = []
    time.sleep(10)
    while not len(done_actors) == len(actor_ids):
        messages = []
        for aid in actor_ids:
            if aid in done_actors:
                continue
            url = f'{BASE}/actors/{aid}/executions'
            try:
                rsp = requests.get(url, headers=HEADERS)
                result = basic_response_checks(rsp)
            except Exception as e:
                print(rsp.content)
                print(f"got exception trying to check executions for actor {aid}, exception: {e}")
                continue
            tot_done = 0
            tot = 0
            for e in result['executions']:
                tot = tot + 1
                if e['status'] == 'COMPLETE':
                    tot_done = tot_done + 1
            if tot == tot_done:
                done_actors.append(aid)
            else:
                messages.append(f"{tot_done - 1}/{tot - 1} for actor {aid}.")

        print(f"{len(done_actors)}/{len(actor_ids)} actors completed executions.")
        for m in messages:
            print(m)
        # sleep more at the beginning -
        if tot_done/tot < 0.5:
            time.sleep(50)
        elif tot_done/tot < 0.75:
            time.sleep(15)
        elif tot_done/tot < 0.9:
            time.sleep(7.5)
        elif tot_done/tot < 0.95:
            time.sleep(2)
    print("All executions complete.")

def exec_analytics(all_data, execution_urls, start_t, end_t, reg_t, work_t, ready_t, send_t, wait_t, run_num, num_nodes, num_workers, num_runs):
    print("Doing analytics.")
    whole_work_times = 0
    calc_times = 0
    exec_init_times = 0
    exec_run_times = 0
    for exec_url in execution_urls:
        try:
            exec_logs_r = requests.get(f"{exec_url}/logs",
                                     headers=HEADERS)
            exec_logs = exec_logs_r.json()['result']['logs']
        except:
            print(exec_logs_r.content)
            raise

        work_time = float(exec_logs.replace('}', '').replace(',', '').split()[1])
        whole_work_times += work_time

        try:
            exec_res_r = requests.get(f"{exec_url}",
                                    headers=HEADERS)
            exec_res = exec_res_r.json()['result']
        except:
            print(exec_res_r.content)
            raise

        msg_receive_time = parse(exec_res['message_received_time'].replace(' ','T') + 'Z')
        exec_start_time = parse(exec_res['start_time'].replace(' ', 'T') + 'Z')
        exec_start_run_time = parse(exec_res['final_state']['StartedAt'])
        exec_end_run_time = parse(exec_res['final_state']['FinishedAt'])

        exec_init_time = (exec_start_run_time - exec_start_time).total_seconds()
        exec_run_time = (exec_end_run_time - exec_start_run_time).total_seconds()
        
        exec_init_times += exec_init_time
        exec_run_times += exec_run_time

    run_data = pd.DataFrame(
        [[run_num, len(execution_urls), end_t - start_t, work_t - reg_t, ready_t - reg_t, send_t - ready_t, end_t - wait_t,
            exec_init_times, exec_run_times, whole_work_times]],
        columns=['Run #', 'Executions', 'Complete Run Time', 'Startup Workers', 'Workers Ready',
                    'Message Time', 'Post Message Time', 'Exec Init Time', 'Exec Run Time', 'Whole Work Time'])
    all_data = all_data.append(run_data, ignore_index = True)
    return all_data

def delete_actors_and_workers(actor_ids):
    actor_worker_links = {}
    for actor_id in actor_ids:
        worker_res = requests.get(f"{BASE}/actors/{actor_id}/workers", headers=HEADERS).json()['result']
        actors_workers_ids = []
        for worker_info in worker_res:
            actors_workers_ids.append(worker_info['id'])
        actor_worker_links[actor_id] = actors_workers_ids

    # Delete all current workers!
    print('Deleting Workers')
    for aid in actor_worker_links:
        for worker_id in actor_worker_links[aid]:
            del_worker_res = requests.delete(f"{BASE}/actors/{aid}/workers/{worker_id}", headers=HEADERS)

    # Delete all actors.
    print('Deleting Actors')
    for actor_id in actor_ids:
        del_actor_res = requests.delete(f"{BASE}/actors/{actor_id}",
                         headers=HEADERS)

def basic_response_checks(rsp, check_tenant=True):
    assert rsp.status_code in [200, 201]
    response_format(rsp)
    data = json.loads(rsp.content.decode('utf-8'))
    assert 'result' in data.keys()
    result = data['result']
    if check_tenant:
        if result is not None:
            assert 'tenant' not in result
    return result

def response_format(rsp):
    assert 'application/json' in rsp.headers['content-type']
    data = json.loads(rsp.content.decode('utf-8'))
    assert 'message' in data.keys()
    assert 'status' in data.keys()
    assert 'version' in data.keys()
    return data


def main():
    # maxes out workers on number of nodes(6 workers per medium node)
    #nodes = int(input('How many nodes are active? '))
    num_nodes = int(sys.argv[1])
    num_runs = 5
    num_workers = 6 #per actor
    num_actors = num_nodes
    num_messages_per_actor = num_workers * 6

    all_data = pd.DataFrame()
    
    for run_num in range(1, num_runs + 1):
        print(f'\nStarting Run {run_num}')
        actor_ids = []

        start_t = timeit.default_timer()
        for i in range(num_actors):
            aid = register_actor(i)
            actor_ids.append(aid)
            print(f"registered actor # {i}; id: {aid}")

        reg_t = timeit.default_timer()
        
        # start up workers
        for aid in actor_ids:
            start_workers(aid, num_workers)
            print(f"workers started for {aid}")

        work_t = timeit.default_timer()
        print('Waiting for ready')
        # wait for actors and workers to reach READY status
        check_for_ready(actor_ids)
        
        # send a "primer" message -
        send_one_message(actor_ids)

        ready_t = timeit.default_timer()

        # send actors messages -
        THREADED = os.environ.get('THREADED_MESSAGES', 'TRUE')
        if THREADED == 'TRUE':
            execution_urls = send_messages_threaded(actor_ids, num_messages_per_actor)
        else:
            execution_urls = send_messages(actor_ids, num_messages_per_actor)

        send_t = timeit.default_timer()
        
        wait_t = timeit.default_timer()
        
        # check for executions to complete
        check_for_complete(actor_ids)
        end_t = timeit.default_timer()
        
        # run analytics on executions
        all_data = exec_analytics(all_data, execution_urls, start_t, end_t, reg_t, work_t, ready_t, send_t, wait_t, run_num, num_nodes, num_workers, num_runs)

        print(f"Final times -- ")
        print(f"Complete Run: {end_t - start_t}")
        print(f"Register: {reg_t - start_t}")
        print(f"Start up workers: {work_t - reg_t}")
        print(f"Workers ready: {ready_t - reg_t}")
        print(f"Send messages: {send_t - ready_t}")
        print(f"Complete executions: {end_t - wait_t}")
        
        # delete all actors and workers afterwards
        delete_actors_and_workers(actor_ids)

    # Creates folder if needed    
    if not os.path.isdir(f'data/nonScaled/hash'):
        os.makedirs(f'data/nonScaled/hash')
    # Saves pandas analytics dataframe to csv in data folder
    all_data.to_csv(f'data/nonScaled/hash/{num_nodes}_nodes_{num_workers}_workers_{num_runs}_trials.csv')


if __name__ == '__main__':
    main()
