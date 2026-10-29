# Accepts two arguments: 
# (1) file_path: The path to the file to be modified, including its name 
# (2) replacements: A dictionary which maps the original lines to their
#                   respective replacements
#                   e.g.: {
#                       'original_line_n':'modified_line_n',
#                       'original_line_m':'modified_line_m',
#                       ...
#                    }
#
# Modifies the file located at file_path and alters it using the 
# replacements dictionary. 
#
# Returns True if modifications were made to the file otherwise False
def modify_file(file_path:str, replacements:dict):

    # Boolean which gets set to true whenever a change is made to the 
    # original file located at file_path, indicating that the file 
    # was updated.
    updated = False

    try:
        # Open the target file
        with open(file_path, 'r+') as f:
            # Stores the updated file
            new_file=''
            # Go through each line of the file @ file_path, applying replacements when necessary
            for line in f.readlines():
                # Check if the current line should be replaced
                for key, replacement in replacements.items():
                    if line.startswith(key):
                        # Only replace if the replacement line/current line do not match
                        if line!=replacement:
                            # Update line
                            line=replacement
                            # Set updated to True
                            updated=True
                # Write the line to new_file
                new_file+=line

            # If modifications were made to the file, write new_file to file_path and return updated
            if updated:
                # Return to beginning of file
                f.seek(0)
                # Write the updated file
                f.write(new_file)
                # Remove any leftovers
                f.truncate()
            # Return updated
            return updated

    # Invalid Path
    except FileNotFoundError:
        print(f'Error: Cannot find file using path {file_path}')
    # Other errors
    except Exception as e:
        print(f'Error: {e}')



# Given a file located at file_path and a list of lines in check_lines, 
# this function returns True if all the lines in check_lines were found
# in the file otherwise false. 
def line_check(file_path:str, check_lines:list[str]):
    pass