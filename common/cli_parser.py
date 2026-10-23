from .env_vars import store_env

# CLI Argument Definitions
#
# Flag  Parameter           Expected Value             Type
# ---- -----------------    -------------------------- ----
# -e   Environment          docker | aster1 | aster2    str
# -x   Encryption           encrypted | plain          str
# -p   MAX_PO_IN_FLIGHT     integer > 0                int
# -r   NUM_REPLICAS         integer > 0                int
# -f   Patch                on | off                   str
# -d   Update Distribution  integer > 0                int
# -u   Prints Usage         none                       none

scripts = {
    'run': ['-e','-x','-p','-r','-f','-d']
}

all_flags = {
    # environment
    '-e': {
        'expected': '<docker|aster1|aster2>',
        'description': ['-e', 'Environment', 'docker | aster1 | aster2', 'str']
    },
    # encryption
    '-x': {
        'expected': '<encrypted|plain>',
        'description': ['-x', 'Encryption', 'encrypted | plain', 'str']
    },
    # MAX_PO_IN_FLIGHT
    '-p': {
        'expected': '<MAX_PO_IN_FLIGHT>',
        'description': ['-p', 'MAX_PO_IN_FLIGHT', 'integer > 0', 'int']
    },
    # NUM_REPLICAS
    '-r': {
        'expected': '<NUM_REPLICAS>',
        'description': ['-r', 'NUM_REPLICAS', 'integer > 0', 'int']
    },
    # Patch
    '-f': {
        'expected': '<on|off>',
        'description': ['-f', 'Patch', 'on | off', 'str']
    },
    # Update Distribution
    '-d': {
        'expected': '<UPDATE_DISTRIBUTION>',
        'description': ['-d', 'Update Distribution', 'integer > 0', 'int']
    }
}

# Name of the script 
script_name=None

# Prints the usage of the passed script
def usage():
    # get all flags associated with the script
    script_flags = scripts[script_name]

    # build usage message
    usage_msg=f'\n[USAGE]\npython {script_name}.py'
    for flag in script_flags:
        usage_msg+=f" {flag} {all_flags[flag]['expected']}"

    # build flags used descriptions message
    flags_used_descriptions_msg='\n'
    for flag in script_flags:
        # list of flag's description
        d = all_flags[flag]['description']
        # append to flags
        flags_used_descriptions_msg+=f'Flag: {d[0]} Parameter: {d[1]} Expected Value: <{d[2]}> Type: {d[3]}\n'

    # return as a str: the usage message & a detailed description of each flag used
    return usage_msg + flags_used_descriptions_msg +'\n'


# Parses CLI args from any py script, ensuring consistent & standard
# argument definitions across scripts.
def cli_parse_args(args:list[str], calling_script_name:str):
    # set the global script name variable 
    global script_name
    script_name=calling_script_name

    # remove script name from argument list
    args = args[1:]

    # the expected number of arguments based on the calling script [length of all the flags multiplied by 2 to account for values]
    expected_num_args = len(scripts[script_name])*2

    # Check if the expected number of arguments was passed based on the calling script
    if len(args) != expected_num_args:
        cli_error(f'Missing required command line args for {script_name}.py: Expected {expected_num_args}, received {len(args)}')

    for i in range(0,len(args),2):
        # error msg initialized to None
        err_msg=None
        # get the current flag
        flag = args[i]

        # Using the current flag, check the adjacent position in the args array and
        # check if the input value is valid. If it is, create an environment variable for
        # it. Otherwise, call the error handler (print error, usage, terminate script)
        match flag:
            # Environment flag: Should be either <docker|aster1|aster2>
            case '-e':
                if args[i+1] in ['docker','aster1','aster2']:
                    store_env(env_var_name='ENVIRONMENT',env_val=args[i+1])
                else: err_msg=f'Invalid argument given for {flag}: {args[i+1]}'
            # Encryption flag: Should be either <encrypted|plain>
            case '-x':
                if args[i+1] in ['encrypted','plain']:
                    store_env(env_var_name='ENCRYPTED',env_val=args[i+1])
                else: err_msg=f'Invalid argument given for {flag}: {args[i+1]}'
            # MAX_PO_IN_FLIGHT flag: Should be an integer > 0
            case '-p':
                if args[i+1].isdecimal() and int(args[i+1])>0:
                    store_env(env_var_name='MAX_PO',env_val=args[i+1])
                else: err_msg=f'Invalid value given for {flag}: {args[i+1]}'
            # NUM_REPLICAS flag: Should be an integer > 0
            case '-r':
                if args[i+1].isdecimal() and int(args[i+1])>0:
                    store_env(env_var_name='NUM_REPLICAS',env_val=args[i+1])
                else: err_msg=f'Invalid value given for {flag}: {args[i+1]}'
            # Patch: Should be <on|off>
            case '-f':
                if args[i+1] in ['on','off']:
                    store_env(env_var_name='PATCH_APPLIED',env_val=args[i+1])
            # Update Distribution: Should be an integer > 0
            case '-d':
                if args[i+1].isdecimal() and int(args[i+1])>0:
                    store_env(env_var_name='UPDATE_DISTRIBUTION',env_val=args[i+1])
                else: err_msg=f'Invalid value given for {flag}: {args[i+1]}'
        # check if there is an error.
        if err_msg is not None: cli_error(err_msg)

# Print error message, print usage for the script being used, print flag details, exit.
def cli_error(err_msg: str):
    # add a newline at the start of the msg for cleaner readability
    err_msg='\n[CLI ERROR]\n'+err_msg
    # get the error message & usage 
    err_msg+=usage()
    # print 
    print(err_msg+'<<<TERMINATING>>>\n')
    # terminate the script with error exit code
    exit(1)