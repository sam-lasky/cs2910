import os

# Environment Variables
#
# Variable              Type   Description
# --------------------  -----  -------------------------------------------------------
# ENVIRONMENT           str    Execution environment (docker | aster_LAN_1 | aster_LAN_2)
# ENCRYPTED             str    Spines communication encryption mode (encrypted | plain)
# MAX_PO                int    Maximum number of pre-order requests in flight (> 0)
# NUM_REPLICAS          int    Number of Prime replicas (> 0)
# PATCH_APPLIED         str    Whether the patch in order.c is enabled (on | off)
# REBOOT                int    Set to 1 when a git update restarts the calling script, otherwise 0.
#
# [Aster-Specific Environment Variables]
# ASTER_MACHINES_USED   str    String containing all Aster machines being used
# REPLICA_ID            int    Unique identifier of the Prime replica
# ASTER_MACHINE_ID      int    Identifier of the Aster machine hosting the replica

# Creates the environment value & stores its associated value
def store_env(env_var_name:str, env_val:str):
    # Set environment variable
    os.environ[env_var_name]=env_val

# Retrieve the specified environment variable's value.
# Convert to the appropriate type before returning if necessary
def get_env(env_var_name:str):
    # check if the environment variable exists. if so return its value
    # and correct type, otherwise return none
    if env_var_name in os.environ:
        # str type, env vars stored by str by default
        if env_var_name in ['ENVIRONMENT','ENCRYPTED','PATCH_APPLIED']:
            return os.environ[env_var_name]
        # special case, need to return a list of aster machines used
        elif env_var_name in ['ASTER_MACHINES_USED']:
            return os.environ[env_var_name].split(',')
        # int, conversion required
        return int(os.environ[env_var_name])
    # does not exist, return none
    else:
        return None

# Returns True if ENCRYPTED=='encrypted' else False
def get_encryption_status():
    return True if os.environ['ENCRYPTED']=='encrypted' else False