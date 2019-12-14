import re
import json
from unidecode import unidecode


def remove_non_ascii(text):
    return unidecode(text)

#sanitize the code for saving to a file on the OS
def get_valid_filename(s):

    """
    Stolen from Django, me thinks?
    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """

    s = str(s).strip().replace(' ', '_')

    return re.sub(r'(?u)[^-\w.]', '', s)

def json_write(filename, dictio):
    
    with open(f'{filename}', 'w') as outfile:
        json.dump(dictio, outfile)

#json write with sanitized filename
def json_write_san(filename, dictio):
    sanitized_filename = get_valid_filename(filename)
    
    json_write(sanitized_filename, dictio)

def json_read(filename):
    
    with open(f'{filename}') as json_file:
        data = json.load(json_file)
        
        return data