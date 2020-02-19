"""
Start worker creation test with:
    python3 worker_creation_test.py $nodes $trial
"""
import sys
import time
import json
import redis
import requests
import multiprocessing
from datetime import datetime

with open('jwt-abaco_admin', 'r') as f:
    JWT_DEFAULT = f.read()

HEADERS = {'X-Jwt-Assertion-DEV': JWT_DEFAULT}

#BASE = base_url
BASE = 'http://129.114.104.189:80'

def register_actor(idx):
    data = {'image': 'notchristiangarcia/wait:3.0', 'name': f'abaco_flops_test_{idx}'}
    rsp = requests.post(f'{BASE}/actors', data=data, headers=HEADERS)
    result = basic_response_checks(rsp)
    return result['id']

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

def _threaded_post(url_and_data):
    url, data = url_and_data
    try:
        rsp = requests.post(url, data=data, headers=HEADERS)
    except Exception as e:
        print(f"got exception trying to send message to {url}; exception: {e}")
    try:
        return rsp.json()['result']['id']
    except:
        return None

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

def redis2json(db):
    allDocs = []
    redisDB = redis.Redis(host='10.49.10.16', port=6979, db=db)
    for key in redisDB.scan_iter():
        key = key.decode('utf-8')
        jsonDict = json.loads(redisDB.get(key))
        jsonDict['_id'] = key
        allDocs.append(jsonDict)
    return allDocs


def main():
    num_nodes = int(sys.argv[1])
    num_actors = int(sys.argv[1])
    trial_num = int(sys.argv[2])
    num_workers_per_actor = 4000 #per actor
    num_messages_per_actor = num_workers_per_actor * 1

    autoscaling = False

    print(f'\nStarting run {trial_num}')
    POOL_SIZE = os.environ.get('POOL_SIZE', 16)
    print(f"using pool of size: {POOL_SIZE}")
    pool = multiprocessing.Pool(processes=POOL_SIZE)

    # Actors
    before_time = before_actors = float(datetime.utcnow().timestamp())
    print(f'Before Actors: {before_time}') 
    urls_and_data = [[f'{BASE}/actors', {'image': 'notchristiangarcia/wait:3.0'}]] * num_actors
    actor_ids = pool.map(_threaded_post, urls_and_data)

    if not autoscaling:
        # Workers
        before_workers = float(datetime.utcnow().timestamp())
        print(f'Before Workers: {before_time}') 
        urls_and_data = [[f'{BASE}/actors/{aid}/workers', {'num': num_workers_per_actor}] for aid in actor_ids]
        print(urls_and_data)
        pool.map(_threaded_post, urls_and_data)
        print(f'All {num_actors * num_workers_per_actor} workers requested')

    pool.close()
    pool.join()

    # Save Data
    time_to_wait = 600
    time_waited = float(datetime.utcnow().timestamp()) - before_time 
    while time_waited <= time_to_wait:
        time_waited = float(datetime.utcnow().timestamp()) - before_time 
        print(f"I've waited {time_waited} of {time_to_wait} seconds.", end='\r')
        time.sleep(1)
    print(f"I've waited {time_waited} of {time_to_wait} seconds.")

    r_workers_store_json = redis2json('2')
    times = []
    for actor in r_workers_store_json:
        for key in actor:
            if not key == '_id':
                try:
                     times.append(float(actor[key]['create_time']))
                except:
                     pass
    times_normalized = [x - before_time for x in times]
    times_normalized.sort()
    with open(f'newdata/data_scaling{autoscaling}_{num_nodes}nodes_{num_actors}actor_trial{trial_num}.txt', 'w') as file:
        for item in times_normalized:
            file.write(f'{item}\n')

if __name__ == '__main__':
    main()
