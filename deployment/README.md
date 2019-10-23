# Instructions for Deployment
The Abaco performance test suite runs on a series of OpenStack servers, I'll be detailing our exact setup, fell free to modify said set-up. The performance study repository is cloned onto it's own server where it will run the test suite and deployment scripts. We'll refer to it as perf, short for performance study. This is an OpenStack m1.quad server, thus it has 10 GBs of RAM, 20 GB of SSD storage, and 4 VCPUs. Along with the main perf server our testing included five additional servers to host Abaco and it's extremities, listed below.

## Abaco Main Servers
### ab-web
An OpenStack m1.medium server (16 GBs of RAM, 60 GB of SSD storage, and 6 VCPUs) that hosts the main Abaco processes, and on it we run a `docker-compose up` command with the docker-compose-web.yml file which has the following services: nginx, regs, mes, admin, and metrics.
### ab-db-prom
An OpenStack m1.quad server (10 GBs of RAM, 20 GB of SSD storage, and 4 VCPUs) that hosts prometheus, Abaco's monitoring system for worker status and analytics which allows for autoscaling when wanted. This server requires a simple `docker-compose up` command with the docker-compose-prom.yml file. The services started are prometheus and metrics; grafana is available, but not used in our case. This server is only needed in the case of wanting autoscaling for the second half of testing.
### ab-db-mdb
An OpenStack m1.quad server (10 GBs of RAM, 20 GB of SSD storage, and 4 VCPUs) that hosts Abaco's MongoDB database. Requires the `docker-compose up` of the docker-compose-mdb.yml file which runs the mongo service.
### ab-db-red
An OpenStack m1.quad server (10 GBs of RAM, 20 GB of SSD storage, and 4 VCPUs) that hosts Abaco's Redis database. Requires the `docker-compose up` of the docker-compose-red.yml file which runs the redis service.
### ab-db-rmq
An OpenStack m1.quad server (10 GBs of RAM, 20 GB of SSD storage, and 4 VCPUs) that hosts Abaco's RabbitMQ queue. Requires the `docker-compose up` of the docker-compose-rmq.yml file which runs the rabbit service.
#### Notice
It is possible to have RabbitMQ, Redis, and MongoDB running on the same server and that is the usual configuration, we however did our testing with three different servers in order to better diagnose slow-downs and resource consumption.

# Testing Servers and Scripts
The following section with outline the scripts in the deployment field and their purposes. Along with that the section will give instructions on what to do before running the test suite (This section will be repeated in the test suite folder to maintain coherence. A description of scripts is as follows.
## Scripts
### burn_dbs
Calls the burn_dbs.yml file with ansible on any servers named ab-perf-d*. This burns down all the databases and removes any saved files from Redis or Mongo.
### check_node_containers
 Calls 'docker ps' for each node and prints it to screen. This allows you to see container status on all the nodes
### del_workers
Calls the del_workers.yml file with ansible on any servers named "mpackard-computes*". This deletes all docker containers with "worker" in the name, thus getting rid of all workers.
### down_abaco
Runs the down_abaco.yml file with ansible on any node named "mpackard-computes*". Deletes all docker images on the node, allowing everything to start fresh again.
### down_instances
Deletes any node with "mpackard-computes" in the name. This deletes all compute nodes, you should do this before stepping away as computer resources are finite and other users might be in queue. Forgetting to do this might also throw your project over allocation bounds with XSEDE.
### get_error_logs
Runs the get_error_logs.yml file with ansible on all nodes named "mpackard-computes*". Get error level abaco logs from all nodes if the abaco.conf file has error logs printing.
### get_inventory
Sets up an inventory using information from openstack to allow for ansible to have server names, keys, and any extra information needed. Requires you to log in with your openstack credentials.
### length_inst
Counts the amount of nodes in the computes group of the inventory.
### up_abaco
Calls the up_abaco.yml file with ansible for all nodes named "mpackard_computes*".
### up_instances
Ask how many instances and initializes that many, placed in the "mpackard-computes" group and named "mpackard-computes#" where the # is the server's index. The image initialized is an image already built and ready, contains docker, docker images needed, and anything else to save building time. Should just work. Initializes OpenStack "m1.medium" nodes with given security key.
## Getting things ready for the test suite.
In our testing we created servers named "mpackard-computes#" where the # is the server's index, these servers are created with the up_instances script. In order to run the test suite you must have more or an equal amount of servers up that you're going to run the test on. This is due to the fact that the test suite does not add servers, it only deletes servers as this insures that any issues in bringing up the servers are seen by the user. If you wanted to run the test suite over 89 nodes, then you would do the following from the deployment folder:
```
./up_instances
```
when prompted enter '89' (or above (this is recommended as some servers might not be responsive and will need to be deleted. This gives some buffer room.)) as a response to the script.
A request will be made. Occassionally run the following to check on the building:
```
openstack server list
```
Once all servers are out of the building state and in the active state we must start the Abaco services on each server, do the following:
```
./up_abaco
```
If there are any errors due to servers not being responsive, run the command again (running the command twice fixes most issues). If there are still errors, delete these servers with:
```
os server delete <server_name_here>
```
You should now have the amount of servers you want. You are ready for the test suite.
