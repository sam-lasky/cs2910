
# Standard Error Handler used across all scripts. 
# Arguments: 
#   (1) Calling script name (str, example 'script.py')
#   (2) Error Message (str)
#   (3) fatal (bool) [indicates whether or not program can recover, default set to True]
def handle_error(script_name:str, error_message:str,fatal:bool=True):
    # Print Error Message
    print('\n===============')
    print('\n[ERROR HANDLER]')
    print('\n===============')
    print(f'Error detected in: {script_name}')
    print(f'Error Message: {error_message}')
    print(f'Fatal Error: {fatal}')
    if fatal==True:
        print('Terminating Program...\n')
    # Recover
    else:
        pass