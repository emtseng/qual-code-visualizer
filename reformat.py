"""
reformat.py
-----------

This reformats the raw transcript data into a CSV that the code extractor can read.

Inputs: tagged data in a given directory
Outputs: reformatted data in a given directory

"""

import os
import errno
import argparse

from util import urlSafe

def sanitize(txt):
    # quotes = ["'", '"']
    # if len(txt) > 0:
    #     if (txt[0] in quotes and txt[1] == 'b' and txt[2] in quotes) or (txt[0] == 'b' and txt[1] in quotes):
    #         return sanitize(txt.replace('b', '', 1))
    #     elif txt[0] in quotes and txt[-1] in quotes:
    #         return sanitize(txt[1:-1])
    return txt

def add_line(line, outfile_name, num_codes):
    with open(outfile_name, mode="a+") as outfile:
        comma_split = line.strip().split(',')
        tags = comma_split[-num_codes:]
        quote = ",".join(comma_split[:-num_codes])
        colon_split = quote.split(': ')
        speaker = colon_split[0]
        utt = sanitize(":".join(colon_split[1:]))
        if speaker != '' and utt != '': 
            outfile_line = '{} =DELIM= {} =DELIM= '.format(speaker, utt)
            for tag in tags:
                outfile_line += '{}, '.format(tag)
            outfile.write(outfile_line+'\n')
    outfile.close()

def reformat(in_folder_name, out_folder_name):
    for filename in os.listdir(in_folder_name):
        participantID = filename[:-4]
        if filename == '.DS_Store':
            pass
        elif '.csv' not in filename: # it's a directory, so recursively call
            reformat(in_folder_name + filename + '/', out_folder_name)
        else: # it's a file
            infile_name = in_folder_name + filename
            with open(infile_name) as infile:
                num_codes = 0
                outfile_name = out_folder_name + urlSafe("{}.csv".format(participantID))
                with open(outfile_name, mode="w+") as outfile:
                    print 'creating ' + outfile_name
                outfile.close()
                for i, line in enumerate(infile):
                    if line.replace(',', '').strip() == '':
                        continue
                    elif i == 0:
                    # Use the first line to get the number of commas in the header row to get the variable number of tags.
                        num_codes = len(line.split(',')[1:]) - 1
                        print outfile_name + ' num_codes: {}'.format(num_codes)
                    else:
                        add_line(line, outfile_name, num_codes)
            infile.close()


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Reformat coded data for use in code-extract.py.')
    parser.add_argument('-i', type=str, help="directory where your raw data is housed")
    parser.add_argument('-o', type=str, help="directory where the reformatted data will be sent. If it doesn't exist, it will be created.")

    args = vars(parser.parse_args())
    inputdir = args['i']
    if inputdir[-1] != '/':
        inputdir = inputdir + '/'
    outputdir = args['o']
    if outputdir[-1] != '/':
        outputdir = outputdir + '/'

    # First check the outputdir
    try:
        os.makedirs(outputdir)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            if( not os.path.isdir(outputdir) ):
                print "Error: outputdir specified as", outputdir, "exists but is not a directory"
                raise
    
    # Then the inputdir
    try:
        os.makedirs(inputdir)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            if( not os.path.isdir(outputdir) ):
                print "Error: inputdir specified as", outputdir, "exists but is not a directory"
                raise
    
    reformat(inputdir, outputdir)
