#!/usr/bin/python
# Some simple code to parse CSV files from coding.
# Usage is:
#    code-extract.py [update] outputdir codebook.csv [master.csv] [transcript1.csv transcript2.csv ...]
#
# update is optional, and specifies that the transcripts are already processed by code-extract.py previously. This will regenerate
# output HTML and CSVs by updating based on the CSVs included. All CSVs should be included if one wants to update.
#
# master.csv is for doing updates. It contains all the quotes from all the interviews, and any other CSV is used to update values
# in that master.csv
#
# outputdir specifies the directory where HTML files are output
#
# We assume codebook.csv has the form:
#   code , description
# where code is a (possibly quote-surrounded) string and description is a
# (possibly quote-deimited) string. We will eat extra ',' appearing at end of
# lines
#
# We assume transcript1.csv, transcript2.csv, ... has the form:
#   quote , codeword1, codeword2 , ...
# where quote is a (possibly quote-surrounded) string with prefix `Name: text'
# for some quoted speech text. Each codeword is a string.
#
# args[transcripts] can also take the form of a path, i.e. 'csv/'. The script will
# check for it and adjust accordingly. Note that only 1 directory is accepted for now.
#
# TODO: fix below
# The script processes the file, building a dictionary indexed by codeword and
# that contains `Name', 'text' pairs. It outputs this as a CSV to output.csv
# The format for output CSV is codeword
#

import os
import errno
import csv
#import unicodecsv
import argparse
import editdistance
from collections import namedtuple
#import lxml.html
#from lxml.html import builder as E
#from yattag import doc
import markup
import operator
from pathlib import Path


def urlSafe( string ):
  urlSafe = string.replace( '/', '_' )
  urlSafe = urlSafe.replace( '?', '_' )
  urlSafe = urlSafe.replace( ' ', '_' )
  return urlSafe


codeCorrections = {}

def mergeCodes( code, codes ):
  """ If an unrecognized code is found in a transcript file, check for nearby ones by edit distance. Prompt user to merge. """

  if( code in codeCorrections ):
    print "Using '" + codeCorrections[code] + "' instead of '" + code + "'"
    code = codeCorrections[code]
    return code

  #print "Unrecognized code: ", code
  distances = {}
  for possibleCode in codes:
    distances[editdistance.eval( code, possibleCode )] = possibleCode

  for i, key in enumerate(sorted(distances)):
    #if( i > 2 ):   # only bother the user to go through top 3 closest codes
    #  break
    #answer = raw_input("Should '" + code + "' have been '" + distances[key] + "'?  [y/N] ")
    #if( answer == 'y' or answer == 'Y' ):
    print "Replacing '"+ code +"' with '" + distances[key]
    codeCorrections[code] = distances[key]
    code = distances[key]
    return code  # It's always working well with edit distance, so let's just do it without asking

  return ''  # Signifies no suitable match found

class Quote(object):
  """ The Quote class contains all the data from a particular quote

      Attributes:
        speaker: person quoted
        quote: the actual quote
        note: any special markers made during coding
        codes: list of codes
  """

  def __init__(self, interview, quoteNum, speaker=' ', text=' ', codes=[]):
    """ Returns a Quote object """

    self.interview = interview
    #self.interviewFile = interviewFile
    #self.interviewName = interviewFile
    self.quoteID = quoteNum
    self.speaker = speaker
    self.text = text
    self.codes = codes  # Should be a tuple

  def printHTML(self, page, codeLinkTo='all' ):
    """ Prints a table row for quote """

    # codeLinkTo  specifies whether should link to code page for all interviews or code page for its interview
    page.tr( id=str(self.quoteID) )
    page.td( self.speaker )
    page.td.close()
    page.td( )
    page.a( self.text, href=self.interview.outFileBase + '.html#' + str(self.quoteID) )
    page.td.close()
    page.td(  )
    for i, code in enumerate(self.codes):
      if( i > 0 ):
        #page.add('&nbsp;&nbsp;-&nbsp;&nbsp;')
        page.br()
        page.br()
      if( codeLinkTo == 'all' ):
        page.a( code, href=urlSafe(code) + '.html' )
      elif( codeLinkTo == 'this_interview' ):
        page.a( code, href=urlSafe(code) + '_' + self.interview.name + '.html' )
      else:
        raise NameError('invalid parameter')

    page.td.close()
    page.tr.close()


################################################################################
# Class Interview
################################################################################
class Interview(object):
  """ The interview class contains all the data from a particular interview

      Attributes:
        name: the interviewee's name
        quotes: an array of note, quote, codes triples
  """

  def __init__(self, name, outFileDir ):
    """ Returns an Interview object whose name is name, whose output files have path prefix outFileDir, and whose basename should be outFileBase """

    self.name = name
    self.outFileDir = outFileDir
    self.outFileBase = name
    self.quotes = []
    self.codeHistogram = {}

  def addQuote(self, quote):
    """ Adds a line from the CSV to the quotes list """

    self.quotes.append(quote)

  def toHTML(self):
    """ Prints HTML for this interview to a file in output directory """

    with open( self.outFileDir + '/' + self.outFileBase+'.html', 'w' ) as outFile:   # Should be of form, e.g.,  Johnson.html
      header = "Interview with "  + self.name
      #footer = "This is the end."
      styles = ( 'layout.css' )

      page = markup.page()
      page.init( title=header, header=header, css=styles, charset='utf-8' )
      page.br()
      page.a( "Index", color="blue", href="index.html")
      page.br( )
      page.br( )
      page.br( )
      page.br( )

      page.table( style="width: 100%" )
      for quote in self.quotes:
        quote.printHTML(page, 'this_interview')

      page.table.close()

      #outFile.write( unicode(page, encoding='utf-8') )
      outFile.write( str(page) )

  def toCSV(self):
    """ Prints CSV for this interview to a file in output directory """

    with open( self.outFileDir + '/' + self.outFileBase+'.csv', 'w' ) as outFile:   # Should be of form, e.g.,  Johnson.html
      fields = ['interview','quoteID','speaker','text','code']
      writer = csv.writer( outFile, dialect='excel' )
      writer.writerow(fields)
      for quote in self.quotes:
        row = [quote.interview.name,quote.quoteID,quote.speaker,quote.text]
        row.extend(quote.codes)
        writer.writerow(row)



#  def toHTMLcode(self, code):
#    """ Returns string consisting of HTML for this interview """
#
#
#    with open( self.outFileDir + '/' + self.outFileBase+'_'+urlSafe(code)+'.html', 'w' ) as outFile:
#      header = "All references to "  + code + " in interview " + self.name
#      #footer = "This is the end."
#      styles = ( 'layout.css' )
#
#      page = markup.page()
#      page.init( title=header, header=header, css=styles, charset='utf-8' )
#      page.br( )
#      page.a( "Index", color="blue", href="index.html")
#      page.br( )
#      page.br( )
#      page.br( )
#      page.br( )
#
#      page.table( style="width: 100%" )
#      for quote in self.quotes:
#        if( code in quote.codes ):
#          quote.printHTML(page)
#
#      page.table.close()
#
#      outFile.write( str(page) )


def stripQuotesSpace( string ):
  if( len(string) < 2 ):
    return string.strip()
  if( string[0] == '"' and string[-1] == '"' ):
    return string[1:-1].strip()
  return string.strip()


def genIndex( interviews, outputdir, codes ):
  """ Generates an index linking to all the main pages """

  histogram = {}
  for code in codes:
    for interview in interviews:
      for quote in interview.quotes:
        if( code in quote.codes ):
          if( code in histogram ):
            histogram[code] += 1
          else:
            histogram[code] = 1

  freqSortedCodes = sorted(histogram.items(), key=operator.itemgetter(1), reverse=True )

  with open(outputdir + '/' + 'index.html', 'w') as outFile:
    with open(outputdir + '/code_counts.csv', mode="w+") as outCSV:
      header = "Interviews and codes"
      #footer = "This is the end."
      styles = ( 'layout.css' )

      page = markup.page()
      page.init( title=header, header=header, css=styles, charset='utf-8' )
      page.br()
      page.a( "Index", color="blue", href="index.html")
      page.add( "&nbsp;&nbsp;-&nbsp;&nbsp;" )
      page.a( "Histograms", color="blue", href="histograms.html")
      page.br()
      page.br()
      page.br()
      page.br()

      page.table( style="width: 100%" )
      page.tr()
      # Write interview list
      page.td(width="50%")
      for interview in interviews:
        page.a( interview.name, href=interview.outFileBase + '.html' )
        page.br()
      page.td.close()
      # Write sorted list of codes with frequencies, also CSV
      page.td(width="50%")
      freqs = "code,count\n"
      for codeFreqPair in freqSortedCodes:
        page.a( codeFreqPair[0], href=urlSafe(codeFreqPair[0]) + '.html' )
        page.add(' &nbsp;&nbsp;(' + str(histogram[codeFreqPair[0]]) + ')')
        freqs += codeFreqPair[0] + ',' + str(histogram[codeFreqPair[0]]) + '\n'
        page.br()
        #page.add('&nbsp;&nbsp;-&nbsp;&nbsp;')
      page.td.close()
      page.tr.close()
      page.table.close()

      outFile.write( str(page) )
      outCSV.write(freqs)

  return histogram

def genHistograms( interviews, outputdir, codes, codeCountsPerSpeaker ):
  """ Generates a page with various histograms """


  with open(outputdir + '/' + 'histograms.html', 'w') as outFile:
    header = "Interviews and codes"
    #footer = "This is the end."
    styles = ( 'layout.css' )

    page = markup.page()
    page.init( title=header, header=header, css=styles, charset='utf-8' )
    page.br()
    page.a( "Index", color="blue", href="index.html")
    page.br()
    page.br()
    page.br()
    page.br()

    page.table( style="width: 100%" )

    freqSortedCodeCounts = sorted(codeCountsPerSpeaker.items(), cmp=lambda x,y: cmp(len(x), len(y)), key=operator.itemgetter(1), reverse=True )
    page.table( style="width: 100%" )
    for codeListPair in freqSortedCodeCounts:
      page.tr()
      page.td( codeListPair[0] )
      page.td( str(len(codeListPair[1])) )
      page.td()
      for speaker in codeListPair[1]:
        page.add( speaker + '&nbsp;&nbsp;&nbsp;')
      page.td.close()
      page.tr.close()
    page.table.close()

    outFile.write( str(page) )




def genCodeHTML( interviews, outputdir, code ):
  """ Searches through all interviews and extracts all references to each code, writes to an HTML output """

  with open(outputdir + '/' + urlSafe(code) + '.html', 'w') as outFile:
    header = "All references to "  + code
    #footer = "This is the end."
    styles = ( 'layout.css' )

    page = markup.page()
    page.init( title=header, header=header, css=styles, charset='utf-8' )
    page.br()
    page.a( "Index", color="blue", href="index.html")
    page.br( )
    page.br( )
    page.br( )
    page.br( )

    page.table( style="width: 100%" )

    for interview in interviews:
      for quote in interview.quotes:
        if( code in quote.codes ):
          quote.printHTML(page)

    page.table.close()

    outFile.write( str(page) )

################################################################################
# Generate and read master CSVs. These contain all quotes from all interviews
# previously processed
################################################################################
def genMasterCSV( masterFilename, interviews ):
  """ Generates a single CSV with all quotes from all interviews """

  with open(masterFilename, 'w') as outFile:
    fields = ['interviewName','quoteID','speaker','text']
    writer = csv.writer( outFile, dialect='excel' )
    writer.writerow(fields)
    for interview in interviews:
      for quote in interview.quotes:
        row = [quote.interview.name,quote.quoteID,quote.speaker,quote.text]
        row.extend(quote.codes)
        writer.writerow(row)


def readMasterCSV( masterFilename, outputdir ):
  """ Generates a single CSV with all quotes from all interviews """

  with open(masterFilename, 'r') as inFile:
    interviewNames = []
    interviews = {}
    #fields = ['interview','quoteID','speaker','text','code']
    reader = csv.DictReader( inFile, dialect='excel', fieldnames=['interviewName','quoteID','speaker','text'], restkey='codes' )
    next(reader)
    for row in reader:

      interviewName = row['interviewName']
      if( interviewName not in interviews ):
        interviews[interviewName] = Interview( interviewName, outputdir )

      if 'codes' in row:
        quote = Quote( interviews[interviewName], row['quoteID'], row['speaker'], row['text'], row['codes'] )
      else:
        quote = Quote( interviews[interviewName], row['quoteID'], row['speaker'], row['text'] )

      interviews[interviewName].addQuote( quote )

    return interviews


################################################################################
# Gen and read CSV files, one for each
################################################################################
def genCodeCSV( interviews, outputdir, code ):
  """ Searches through all interviews and extracts all references to each code, writes to a CSV output """


  with open(outputdir + '/' + urlSafe(code) + '.csv', 'w') as outFile:
    fields = ['interview','quoteID','speaker','text','code']

    writer = csv.writer( outFile, dialect='excel' )

    writer.writerow(fields)

    for interview in interviews:
      for quote in interview.quotes:
        if( code in quote.codes ):
          row = [quote.interview.name,quote.quoteID,quote.speaker,quote.text]
          row.extend(quote.codes)
          writer.writerow(row)




def genCodePerTransHTML( interviews, outputdir, code ):
  """ For each interview, output a page for each code with all the quotes coded as such """

  for interview in interviews:
    with open(outputdir + '/' + urlSafe(code) + '_' + interview.name + '.html', 'w') as outFile:
      header = "All references to '"  + code + "' in interview '" + interview.name + "'"
      #footer = "This is the end."
      styles = ( 'layout.css' )

      page = markup.page()
      page.init( title=header, header=header, css=styles, charset='utf-8' )
      page.br()
      page.a( "Index", color="blue", href="index.html")
      page.br( )
      page.br( )
      page.br( )
      page.br( )

      page.table( style="width: 100%" )

      for quote in interview.quotes:
        if( code in quote.codes ):
          quote.printHTML(page)

      page.table.close()

      outFile.write( str(page) )


################################################################################
# Reading CSVs and generating internal data structures
################################################################################
def readGeneratedCSVs( masterFilename, transcripts, codes, outputdir, codeCountsPerSpeaker ):
  """ Reads in generated CSVs as output by genCodeCSV() """

  interviews = readMasterCSV(masterFilename, outputdir )

  numInterviews = 0
  numQuotes = 0
  lastPerson = ''
  for transcript in transcripts:
    with open(transcript,'r') as transFile:
      # Read in transcript, populate new Interview object and codeDict
      #transReader = unicodecsv.reader( transFile, dialect='excel', encoding='utf-8' )
      transReader = csv.DictReader( transFile, dialect='excel', fieldnames=['interviewName','quoteID','speaker','text'], restkey='codes' )
      next(transReader)
      for row in transReader:
        # format is [quote.interview.name,quote.quoteID,quote.speaker,quote.text]
        interviewName = row['interviewName']
        if( interviewName not in interviews ):
          print "Error: couldn't find interview " + interviewName + " for entry in " + transcript
        else:
          # Find quote within interview
          found = False
          for quote in interviews[interviewName].quotes:
            if( quote.quoteID == row['quoteID'] ):
              found = True
              quote.speaker = row['speaker']
              quote.text = row['text']
              if( 'codes' in row ):
                quote.codes = row['codes']
              else:
                quote.codes = []
          if( not found ):
            print "Error: couldn't find quote " + row['quoteID'] + " for entry in " + transcript

  #interviewList = interviews.values().sort(key=lambda x: x.name )
  interviewList = sorted(interviews.values(), key=lambda x: x.name)
  return interviewList


def readOriginalCSVs( transcripts, codes, outputdir, codeCountsPerSpeaker):
  """ Reads in CSVs in their original post-Google spreadsheet form """

  numInterviews = 0
  numQuotes = 0
  interviews = []
  lastPerson = ''
  for transcript in transcripts:
    with open(transcript,'r') as transFile:
      transcriptFileName = os.path.splitext(os.path.basename(transcript))[0]
      numInterviews += 1
      # Read in transcript, populate new Interview object and codeDict
      #transReader = unicodecsv.reader( transFile, dialect='excel', encoding='utf-8' )
      transReader = csv.reader( transFile, dialect='excel' )
      interview = Interview(transcriptFileName, outputdir )
      for row in transReader:
        # first value is note, second is quote, following fields are codes
        #note = stripQuotesSpace( row[0] )
        quote = stripQuotesSpace( row[0] )
        if( quote != '' ):
          numQuotes += 1
          # Check if we have a : to separate speaker from text
          if( ':' in quote ):
            (person,text) = quote.split(':', 1)
          else:
            #person = ''  # FIXME: before had quote assigned to person, and blank to text. Seemed wrong
            #text = quote
            #person = lastPerson # FIXME: before had quote assigned to person, and blank to text. Seemed wrong
            person = lastPerson
            text = quote # should just use the last person for this quote

          lastPerson = person

          quoteCodes = []
          for code in row[1:]:
            strippedCode = stripQuotesSpace( code )
            #print strippedCode
            if( strippedCode == '' ):
              continue
            if( strippedCode not in codes):
              correctedCode = mergeCodes( strippedCode, codes )
              if( correctedCode == '' ):
                print "Skipping unrecognized code in '" + strippedCode + "' in file " + transcript + " that could not be merged"
                continue
              strippedCode = correctedCode
            quoteCodes.append( strippedCode )
            codeCountsPerSpeaker[strippedCode].add( person )

          quote = Quote( interview, numQuotes, person, text, quoteCodes )
          interview.addQuote( quote )
      interviews.append(interview)

  return [interviews,codeCountsPerSpeaker]


################################################################################
# Main function
################################################################################
def main():
  parser = argparse.ArgumentParser(description='Process coded transcripts given a codebook.')
  parser.add_argument('-u', '--update', type=str, help="update the indicated master.csv")
  parser.add_argument('outputdir', metavar='outputdir', help="directory where outputs will be sent. If it doesn't exist it will be created")
  parser.add_argument('codebook', metavar='codebook', help='the codebook CSV file')
  parser.add_argument('transcripts', metavar='transcripts', help='one or more transcript CSV files, or a directory', nargs='+')
#parser.add_argument('output', metavar='output', help='the output, processed CSV file')
  args = vars(parser.parse_args())

  outputdir = args['outputdir']

# Check outputdir
  try:
    os.makedirs(outputdir)
  except OSError as exception:
    if exception.errno != errno.EEXIST:
      if( not os.path.isdir(outputdir) ):
        print "Error: outputdir specified as", outputdir, "exists but is not a directory"
        raise


  codes = []
  codeCountsPerSpeaker = {}
  with open(args['codebook'], 'r') as codeFile:
    # Read in the codes
    codeReader = csv.reader(codeFile, dialect='excel')
    for row in codeReader:
      # first value is code, second is description. We ignore description for now
      code = stripQuotesSpace( row[0] )
      if( code != '' ):
        codes.append( code )
        codeCountsPerSpeaker[code] = set()

    # Is this an update?
    if( args['update'] ):
      interviews = readGeneratedCSVs( args['update'], args['transcripts'], codes, outputdir, codeCountsPerSpeaker )
    else:
      transcripts_path = Path(args['transcripts'][0])
      # Are we analyzing an entire directory?
      if transcripts_path.is_dir():
        originalCSVs = [args['transcripts'][0] + path.name for path in Path(args['transcripts'][0]).glob('*.csv')]
        print originalCSVs
      else:
        originalCSVs = args['transcripts']
      interviews,codeCountsPerSpeaker = readOriginalCSVs( originalCSVs, codes, outputdir, codeCountsPerSpeaker )
      # Generate a histogram HTML page
      genHistograms( interviews, outputdir, codes, codeCountsPerSpeaker )

    # Write out a master CSV
    genMasterCSV( outputdir + '/master.csv', interviews )

    # Write out an interview HTML page
    for interview in interviews:
      interview.toHTML()

    # Write out individual HTML for each code
    for code in codes:
      genCodeHTML( interviews, outputdir, code )

    # Write out individual CSV's for each code
    for code in codes:
      genCodeCSV( interviews, outputdir, code )

    # Write out individual HTML for each code, interview pair
    for code in codes:
      genCodePerTransHTML( interviews, outputdir, code )

    # Generate the main index.html and writes
    genIndex( interviews, outputdir, codes )

    #for code in codes:
    #  print code
    #
    #  for quote in codeDict[code]:
    #    print quote.Speaker, " :    ", quote.Quote , "\n"
    #
    #  print '*'*80


    # Pretty print HTML of transcript
    #print interview.printHTML()

    # From each interview, print out quotes grouped by codes / interviews
    #
    # Print out quotes grouped by codes, from all interviews
    #
    # Counts across all the interviews, co-occurrence of codes
    #





if __name__ == '__main__':
  main()
