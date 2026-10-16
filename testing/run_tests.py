import sys, subprocess, time, os
from pathlib import Path
from datetime import datetime

# creates the results file and stores it in the correct directory
def create_results_file(test_parameters):
    # get the name of the correct subdirectory where the tests are stored
    if test_parameters['environment']=='Docker':test_environment='docker_tests/'
    else: test_environment = 'aster_tests/'

    # create a new results file and place it in the correct directory
    i=1
    filename = None
    while True:
        if Path(test_environment+f'results_{i}').exists():
            i+=1
        else: 
            filename = f'{test_environment}results_{i}'
            break

    # get MAX_PO_IN_FLIGHT
    max_po = None
    with open("../prime/src/def.h") as f:
        for line in f:
            if line.startswith("#define MAX_PO_IN_FLIGHT"):
               max_po=line.split(" ")[2]
               break

    with open(filename,"a") as f:
        f.write("=================================================================================================\n")
        f.write(f"{'Test Start Time:':<45}{datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')}\n")
        f.write(f"{'Total updates per trial run:':<45}{test_parameters['total_updates']}\n")
        f.write(f"{'Bandwidth limitations used:':<45}{test_parameters['bandwidth_limit']}\n")
        f.write(f"{'Number of Trials per Test Configuration:':<45}{test_parameters['num_trials']}\n")
        f.write(f"{'Maximum Outstanding Preorder Requests:':<45}{max_po}\n")
        f.write(f"{'Test Environment used:':<45}{test_parameters['environment']}\n")
        f.write(f"{'Number of Prime Replicas used:':<45}{test_parameters['num_replicas']}\n")
        f.write("=================================================================================================\n")

    return filename

# alter outgoing bandwidth limitations for all replicas 
# action 1: 'initialize' --> delete existing configuration & apply a new one only if a non-None limit exists 
# action 2: 'replace'    --> change the link speed    
def alter_bandwidth_limit(action, test_environment, limits):
    # initialize
    if action=='init':
        pass


def run_tests(test_environment):
    test_parameters = {
        'total_updates':                25000,
        'bandwidth_limit':              [None,100,250,500,750],
        'num_emulated_clients':         [1,5,10,15,20,25,30,50,100],
        'num_trials':                   5,
        'environment':                  'Docker' if test_environment=='d' else 'Aster',
        'num_replicas':                 6
    }
    # get total number of tests for progress printing
    total_tests = len(test_parameters['bandwidth_limit'])*len(test_parameters['num_emulated_clients'])*test_parameters['num_trials']
    # create the results file
    filename = create_results_file(test_parameters)

    # # # # # # # # # # # # # # # 
    # # # Begin the Tests! # # # #
    # # # # # # # # # # # # # # # 

    # initialize bandwidith emulation configuration


    # iterate over and apply each bandwidth limitation
    for bandwidth_limit in test_parameters["bandwidth_limit"]:
        pass
    


# d gets passed if the test is in docker 
# a gets passed if the test is in aster
def main():
    if len(sys.argv)<2 or sys.argv[1] not in ['d','a']:
        print('Usage: python run_tests.py <d|a> (d=Docker, a=Aster)')
        exit(1)

    run_tests(sys.argv[1])
    


if __name__ == "__main__":
    main()