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

for nodes in 1
do
    python3 insts_check.py $nodes
    for trial in 1
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
	    python3 tests/worker_test.py $nodes $trial
        done
done
