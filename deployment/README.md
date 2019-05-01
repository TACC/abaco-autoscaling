# semi-dynamic openstack instance deployment with ansible

__Note that this uses fairly generic node names. If you are sharing an openstack tenant with others, change the names so you don't step on their instances!__

Make sure your openstack credentials are loaded:

    . openrc
    Please enter your OpenStack Password for project abc as user xyz:
    ******


See dynamic inventory:

    ./get_inventory | jq

Use dynamic inventory (e.g. on just computes):

    ansible -i get_inventory computes -a uptime

## deploy instances

Spin up all hosts that don't already exist:

    ansible-playbook -i get_inventory instances_up.yml

Spin down all hosts that don't already exist:

    ansible-playbook -i get_inventory instances_down.yml
                                                              

## install docker 

    ansible-playbook -i get_inventory deploy-abaco.yml
