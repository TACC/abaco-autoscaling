import subprocess
import json
import sys


def insts_check():
    cmd_res = subprocess.run(['./length_inst'], stdout=subprocess.PIPE, cwd='../', shell=True)
    return int(cmd_res.stdout) 


def delete_insts(goal_count, insts_count):
    inventory_res = subprocess.run(['../get_inventory', '|', 'jq'], stdout=subprocess.PIPE)
    inventory_dict = json.loads((inventory_res.stdout.decode('UTF-8')))
    insts_names = inventory_dict['computes']['hosts']
    
    del_amo = insts_count - goal_count
    print(f'Deleting {del_amo} instance(s)')
    del_list = insts_names[0:del_amo]

    del_res = subprocess.run(['openstack', 'server', 'delete'] + del_list, stdout=subprocess.PIPE, shell=False)
    print(del_res)


def main():
    goal_count = int(sys.argv[1])
    insts_count = insts_check()
    print(f'Have {insts_count} - Want {goal_count}')
    if goal_count < insts_count:
        delete_insts(goal_count, insts_count)
    elif goal_count > insts_count:
        raise ValueError('Not enough instances currently running')

if __name__ == "__main__":
    main()
