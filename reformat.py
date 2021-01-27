#!/usr/bin/python3
import sys

if sys.version_info[0] != 3:
  print("This script requires Python version 3")
  sys.exit(1)

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
import csv

from util import urlSafe, mergeCodes, stripQuotesSpace


def sanitize(txt):
    # Hack for weird output problem on CSCW19
    # quotes = ["'", '"']
    # if len(txt) > 0:
    #     if (txt[0] in quotes and txt[1] == 'b' and txt[2] in quotes) or (txt[0] == 'b' and txt[1] in quotes):
    #         return sanitize(txt.replace('b', '', 1))
    #     elif txt[0] in quotes and txt[-1] in quotes:
    #         return sanitize(txt[1:-1])
    return txt


def add_line(line, outfile_name, num_codes, allCodes, codeCorrections):
    with open(outfile_name, mode="a+") as outfile:
        comma_split = line.strip().split(',')
        # Hacks for codes that contained commas for the Remote Clinic study
        if 'Consultant unfamiliarity with specific platforms' in line:
            i = comma_split.index('"Consultant unfamiliarity with specific platforms (e.g. Android vs. iOS')
            joined_code = " / ".join(comma_split[i:i+2])
            comma_split[i] = joined_code
            comma_split = comma_split[:i+1] + comma_split[i+2:]
        if 'Consultant unfamiliarity with specific apps' in line:
            i = comma_split.index('"Consultant unfamiliarity with specific apps / social media (e.g. Waze')
            joined_code = " / ".join(comma_split[i:i+4])
            comma_split[i] = joined_code
            comma_split = comma_split[:i+1] + comma_split[i+4:]
        # General code merging
        codes = comma_split[-num_codes:]
        merged_codes = list()
        for code in codes:
            if code == "":
                merged_code = ""
            else:
                strippedCode = urlSafe(stripQuotesSpace( code ))
                if strippedCode not in allCodes:
                    merged_code, codeCorrections = mergeCodes(strippedCode, allCodes, codeCorrections, skip=False)
                else:
                    merged_code = strippedCode
            merged_codes.append(merged_code)
        speaker = comma_split[0]
        utt = sanitize(",".join(comma_split[1:-num_codes]))
        if speaker != '' and utt != '':
            outfile_line = '{} =DELIM= {} =DELIM= '.format(speaker, utt)
            for merged_code in merged_codes:
                outfile_line += '{}, '.format(merged_code)
            outfile.write(outfile_line+'\n')
    outfile.close()
    return codeCorrections


def reformat(in_folder_name, out_folder_name, codes, codeCorrections):
    for filename in os.listdir(in_folder_name):
        participantID = filename[:-4]
        if filename == '.DS_Store':
            pass
        elif '.csv' not in filename:  # it's a directory, so recursively call
            reformat(in_folder_name + filename + '/', out_folder_name, codes, codeCorrections)
        else:  # it's a file
            infile_name = in_folder_name + filename
            with open(infile_name) as infile:
                num_codes = 0
                outfile_name = out_folder_name + \
                    urlSafe("{}.csv".format(participantID))
                with open(outfile_name, mode="w+") as outfile:
                    print("\ncreating " + outfile_name)
                outfile.close()
                for i, line in enumerate(infile):
                    if line.replace(',', '').strip() == '':
                        continue
                    elif i == 0:
                    # Use the first line to get the number of commas in the header row to get the variable number of tags.
                        num_codes = len(line.split(',')[1:]) - 1
                        print(outfile_name + ' num_codes: {}'.format(num_codes))
                    else:
                        codeCorrections = add_line(line, outfile_name, num_codes, codes, codeCorrections)
            infile.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Reformat coded data for use in code-extract.py.')
    parser.add_argument(
        '-i', type=str, help="directory where your raw data is housed")
    parser.add_argument(
        '-o', type=str, help="directory where the reformatted data will be sent. If it doesn't exist, it will be created.")
    parser.add_argument('-c', type=str, help="codebook to use for merging")

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
            if(not os.path.isdir(outputdir)):
                print("Error: outputdir specified as", outputdir, "exists but is not a directory")
                raise

    # Then the inputdir
    try:
        os.makedirs(inputdir)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            if(not os.path.isdir(outputdir)):
                print("Error: inputdir specified as", outputdir, "exists but is not a directory")
                raise

    # Then extract codes from the codebook
    codes = []
    codeCorrections = {}
    with open(args['c'], 'r') as codeFile:
        # Read in the codes
        codeReader = csv.reader(codeFile, dialect='excel')
        for row in codeReader:
        # first value is code, second is description. We ignore description for now
            code = urlSafe(stripQuotesSpace( row[0] ))
            if( code != '' ):
                codes.append( code )

    reformat(inputdir, outputdir, codes, codeCorrections)
