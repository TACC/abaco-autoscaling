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

for nodes in 89 # 55 34 21 13 8 5 3 2 1
do
    python3 insts_check.py $nodes
    cd ../deployment
    ./burn_dbs
    ./up_abaco
    cd ../test_suite
    sleep 10
    #python3 tests/25k_flop_test.py $nodes
    #python3 tests/8k_flop_test.py $nodes
    python3 tests/hash_test.py $nodes
    #python3 tests/scaling_25k_flop_test.py $nodes
    #python3 tests/scaling_8k_flop_test.py $nodes
    #python3 tests/scaling_hash_test.py $nodes
done
#python3 insts_check.py 0
