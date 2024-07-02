import os
from  datetime  import datetime

def check_existing_file(file_path):
    '''Check if a file already exists. If it does, ask if we want to overwrite it.'''
    if os.path.isfile(file_path):
        while True:
            response = input(f"File {os.path.basename(file_path)} already exists. Do you want to overwrite it? (y/n): ")
            if response.lower() == 'y':
                return True
            elif response.lower() == 'n':
                return False
            else:
                print("Invalid response. Please enter 'y' or 'n'.")
    else:
        return True
    
    
def check_existing_folder(folder_path):
    '''Check if a folder already exists. If it doesn't, ask if we want to create it.'''
    if os.path.exists(folder_path) == False :
        while True:
            response = input(f"{os.path.basename(folder_path)} doesn't exists. Do you want to create it? (y/n): ")
            if response.lower() == 'y':
                return True
            elif response.lower() == 'n':
                return False
            else:
                print("Invalid response. Please enter 'y' or 'n'.")
    else:
        return False
    
def mv_existing_file_archive(mypath):
    '''Check if a file already exists. If it does, move it to archive.'''
    if os.path.exists(mypath) == True :
        try: 
            onlyfiles = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
        except FileExistsError:
            # no files to move
            return
    # there are files to move. Make archive if it doesn't exist
    archive = os.path.join(mypath,'archive')
    if not os.path.exists(archive):
        os.mkdir(archive)
    for f in onlyfiles:
        file = os.path.join(mypath, f)
        new_file = os.path.join(mypath,'archive',f+datetime.today().strftime('%Y%m%d%H%M%S'))
        os.rename(file, new_file)