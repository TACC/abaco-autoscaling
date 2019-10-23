# Instructions for Running the Test Suite
In order to run the test suite you must first have the servers deployed and running Abaco. Following that you are then able to run the test suite. Below we will describe how to deploy the servers (also written in the deployment folder README.md) and then how to run the test suite.
## Description of the test suite.
In the test suite folder the most important things are the `run_tests.sh` file and the `tests` folder. 
### run_tests.sh script
This script runs one of the tests in the `tests` folder per execution, it's your job to uncomment the test that you want to run. This will run the test for each node amount given in the scripts `for` loop. Each node size change comes with checking the number of nodes currently running with insts_check.py and getting rid of nodes if neccessary, burning down the databases for fresh results, and re-upping abaco in order to reattach the databases. Once the tests are down the insts_check.py script will delete all instances to make sure none are left on accident.
### Tests folder
The tests folder contains all six tests that we did, this includes a scaled and non-scaled version of two differents types of flop/s tests and a hash test. The flop/s tests include one easier test that runs 30 times per actor which shows autoscaling performance well and a hard test that runs 1 time per actor and gets rid of some more overhead. The easy test does math on a 8000 x 8000 matrix, thus 8k in the name, and the hard test does math on a 25000 x 25000 matrix, thus the 25k. The hash test on the other hand does solves a block of a perscribed difficulty 36 times per actor.
#### Description of the tests
While each test has minor differences, they all share similar formatting and structure. The test creates actors equal to the amount of servers available for easy number scaling, this is the only argument required for the testing. Once the actor is created a set amount of workers per actor are created, this depends on which test is running; this is skipped in the case of the scaling tests as that's the point. The script checks for actor and worker readiness, once ready the actors are sent the specified amount of executions wanted, for example the 8k test sends 30 executions per actor.  Once done, the script waits for executions to complete, once complete their logs and data are taken to form a Pandas dataframe of times and results. This will run fives times total. Once everything is complete said dataframe is saved as a CSV under it's specifed name and folder in the data folder of the test_suite folder. 
## Getting servers ready for the test suite
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

## Running the test suite
Now that you know what is in the test suite folder and that you have the current amount of servers running, all you have to do is uncomment the test that you want to run in the `run_tests.sh` file and specify how many nodes you want to run the test for, this may be a list. Then run the script with:
```
./run_tests.sh
```
If the script is not yet executable, make it executable with the following and try again:
```
sudo chmod +x run_tests.sh
```
The tests should now run successfully, status updates will be printed to the CLI and results will be written to CSV's inside of the test_suite/data folder under the correct filename.
