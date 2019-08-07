# How to run the flops benchmark!   
##### Run all of this from perf
```
./deployment/up-instances
```
 Wait until ```os server list``` is completely done building

```
./deployment/up-abaco
```

```
./flops/flops_test.py (It'll ask you node count)
```

- Approx 10 minutes per run, 5 trials per run.
- Approx 30 seconds for messages to run in each trial (for large node size, 2 seconds for instances of 2 nodes).
- We start seeing extended wait times for message sending once we hit around 55 nodes. Intermittently in the 30's.
- Data is saved and organized by node size, trial, and run number inside of a /data folder (automatically created).

```
./deployment/down-instances
```

```
./deployment/burn-dbs
```
[repeat for each node size]

