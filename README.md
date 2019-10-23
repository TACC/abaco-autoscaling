# Abaco Performance Benchmark Repository
Abaco (Actor BAsed COntainers) is an open source, distributed computing platform based on the Actor Model of concurrent computation and Linux containers funded by the National Science Foundation and hosted at the Texas Advanced Computing Center (TACC).

The goal of this repository is to act as the base of operations for the Abaco performance benchmark. This benchmark's intention is to test Abaco's likeness to the theoretical maximums of the testing hardware along with performance changes brought by Abaco's autoscaling functionality.

This repository holds two folders: deployment and the test suite.

## Deployment
The deployment folder contains utilities meant to bring up and setup the work environment that the test suite will be running on and consist of:
- Overstack scripts to interact with server front-ends
- Ansible-playbook scripts to interact with server back-ends
- Configuration files for Abaco initialization

## Test Suite
The test suite folder has files meant to actually run the performance study. These files consist of:
- Python scripts to run the Abaco performance tests
- A shell scripts to automate the running of the Python tests
- Dockerfiles and files neccessary to build the test images
- A data folder to store results

### Information
Instructions on deploying everything and running the suite of tests is inside their respective folder as continued readmes. These tests were ran at the Texas Advanced Computing Center facilities and as such, had access to some nifty machines. We begin with using TACC's self-service cloud system named Jetstream. This machine has 320 nodes, 7680 cores, and 40 TB of RAM, and operates with OpenStack. You will have to arrive at this point before you are able to "just run" the test suite, even still, you will have to work around any issues that you might face as your situation will not match ours.

### Licensing
This project utilizes the GNU General Public License.
