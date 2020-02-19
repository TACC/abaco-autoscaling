#!/bin/bash
# This runs a test from 89 nodes down to 1. You'll have to initialize the
# largest node size test you want to run, in this case I would initialize 89
# nodes. I would then change the python test I want to run, then run the
# script with "./run_tests.sh". 

# The script runs insts_check.py that checks for node amount, if there's too
# many it'll delete nodes to reach goal, if too few, it'll error. Then the db's
# are burnt and cooked, abaco is setup to make sure it's fresh, waits for 10
# seconds to allow initialization time, then runs the test. This occurs for
# each node count and finally all nodes are deleted.

for nodes in 100 90 80 70 60 50 40 30 20 10 5 2 1
do
    python3 insts_check.py $nodes
    for trial in 1 2 3 4 5
        do
	    cd ../deployment
            ./burn_mongo
            ./burn_web
	    ./burn_dbs
            ./down_abaco
            sleep 10
            ./down_abaco
	    ./up_abaco
	    cd ../test_suite
	    sleep 10
            ## Start performance test with:
            ## python3 performance_test.py #numNodes #trialNum #autoscaling
                                           #flopsOrhashrate #sizeOfMatrix or amoOfHashes
                                           #numWorkersPerActor #numMessagesPerWorker

            #python3 performance_test.py $nodes $trial false flops 8000 6 5
            #python3 performance_test.py $nodes $trial false flops 25000 1 1
            #python3 performance_test.py $nodes $trial false hashrate 3000000 6 6            
            #python3 performance_test.py $nodes $trial true flops 8000 6 5
            #python3 performance_test.py $nodes $trial true flops 25000 1 1
            #python3 performance_test.py $nodes $trial true hashrate 3000000 6 6

            ## Start worker creation test with:
	    #python3 worker_creation_test.py $nodes $trial
        done
done
