import os
import glob

path = '/path/to/your/directory'

# use glob to match the pattern 'file_*.pdf'
for filename in glob.glob(os.path.join(path, '*_*.pdf')):
    # Split the extension from the path and normalise it to lowercase.
    new_filename = os.path.splitext(filename)[0]
    # Remove the last underscore and the text after it
    new_filename = "_".join(new_filename.split('_')[:-1]) + '.pdf'
    # rename the file
    os.rename(filename, new_filename)