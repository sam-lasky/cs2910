from .env_vars import store_env
from .error_handler import handle_error

# CLI Argument Definitions
#
# Flag  Parameter           Expected Value             Type
# ---- -----------------    -------------------------- ----
# -e   Environment          docker | aster_LAN_1 | aster_LAN_2    str
# -x   Encryption           <0 | 1>                    int
# -p   MAX_PO_IN_FLIGHT     integer > 0                int
# -r   NUM_REPLICAS         integer > 0                int

scripts = {
    'run': ['-e','-x','-p','-r']
}

all_flags = {
    # environment
    '-e': {
        'expected': '<docker|aster_LAN_1|aster_LAN_2>',
        'description': ['-e', 'Environment', 'docker | aster_LAN_1 | aster_LAN_2', 'str']
    },
    # encryption
    '-x': {
        'expected': '<encrypted|plain>',
        'description': ['-x', 'Encryption', '0|1', 'int']
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


# Parses CLI args from any py script (currently only run supported), ensuring consistent & standard
# argument definitions across scripts.
#
# Returns the dictionary arg_dict= {
#   'env':      <'docker' | 'aster_LAN_1' | 'aster_LAN_2'>,   
#   'encrypt':  <0|1>,
#   'max_po':   integer value > 0,
#   'num_replicas:   integer value > 0,
#   'patch':     <0|1> (optional)
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
        error_message=f'Missing required command line args for {script_name}.py: Expected {expected_num_args}, received {len(args)}'+usage()
        handle_error(script_name+'.py',error_message)

    # Returned dictionary of arguments
    arg_dict={}

    for i in range(0,len(args),2):
        # error msg initialized to None
        err_msg=None
        # get the current flag
        flag = args[i]

        # Using the current flag, check the adjacent position in the args array and
        # check if the input value is valid. If it is, create an environment variable for
        # it. Otherwise, call the error handler (print error, usage, terminate script)
        match flag:
            # Environment flag: Should be either <docker|aster_LAN_1|aster_LAN_2>
            case '-e':
                if args[i+1] in ['docker','aster_LAN_1','aster_LAN_2']:
                    arg_dict['env']=args[i+1]
                else: err_msg=f'Invalid argument given for {flag}: {args[i+1]}'
            # Encryption flag: Should be either <encrypted|plain>
            case '-x':
                if args[i+1] in ['0','1']:
                    arg_dict['encrypt']=int(args[i+1])
                else: err_msg=f'Invalid argument given for {flag}: {args[i+1]}'
            # MAX_PO_IN_FLIGHT flag: Should be an integer > 0
            case '-p':
                if args[i+1].isdecimal() and int(args[i+1])>0:
                    arg_dict['max_po']=int(args[i+1])
                else: err_msg=f'Invalid value given for {flag}: {args[i+1]}'
            # NUM_REPLICAS flag: Should be an integer > 0
            case '-r':
                if args[i+1].isdecimal() and int(args[i+1])>0:
                    if args[i+1]>20 and arg_dict['env'] in ['aster_LAN_1','aster_LAN_2']:
                        err_msg=f'Too many machines, there are only 20 available but {args[i+1]} were requested'
                    arg_dict['num_replicas']=int(args[i+1])
                else: err_msg=f'Invalid value given for {flag}: {args[i+1]}'
            # Patch: Should be <on|off>
            case '-f':
                if args[i+1] in ['0','1']:
                    arg_dict['patch']=int(args[i+1])
        # check if there is an error.
        if err_msg is not None:
            handle_error(script_name+'.py', err_msg+usage)
        # return the dictionary
    return arg_dict
