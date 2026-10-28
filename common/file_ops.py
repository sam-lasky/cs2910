# Accepts two arguments: 
# (1) file_path: The path to the file to be modified, including its name 
# (2) replacements: A dictionary where the key is the target line/lines 
#                   to be modified in the file, the value is the modification
#                   to be made to these lines. 
#
# Modifies the file located at file_path and alters it using the 
# replacements dictionary. 
def modify_file(file_path:str, replacements:dict):

    try:
        # Open the target file
        with open(file_path, 'w') as f:
            pass
    # Invalid Path
    except FileNotFoundError:
        print(f'Error: Cannot find file using path {file_path}')
    # Other errors
    except Exception as e:
        print(f'Error: {e}')