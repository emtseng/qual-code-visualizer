#!/usr/bin/python3
import sys

if sys.version_info[0] != 3:
  print("This script requires Python version 3")
  sys.exit(1)

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


import os
import errno
import csv
import argparse
from collections import namedtuple, defaultdict
import markup
import operator
from pathlib import Path

from util import urlSafe, stripQuotesSpace, mergeCodes
from generators import genIndex, genHistograms, genCodeHTML, genCodeCounts, genCodeCSV, genCodePerTransHTML, genHeaderMenu, genPosterHTML, genStylesheet


################################################################################
# Class Post
################################################################################
class Post(object):
  """ The Post class contains all the data from a particular post

      Attributes:
        thread <Thread>: the thread in which the post is contained
        postID <int>: the ID of the post within the thread, used for internal linking
        poster <Post>: the person who posted
        text <str>: the actual content of the post
        note <str>: any special markers made during coding
        codes <list>: list of codes
  """

  def __init__(self, thread, postID, poster=' ', text=' ', codes=[]):
    """ Returns a Post object """

    self.thread = thread
    self.postID = postID
    self.poster = poster
    self.text = text
    self.codes = codes  # Should be a tuple

  def printHTML(self, page, codeLinkTo='all' ):
    """ Prints a table row for a post """

    # codeLinkTo specifies whether should link to code page for all threads or code page for its thread
    page.tr( id=str(self.postID) )
    page.td( )
    page.a(self.poster, href="{}.html".format(urlSafe(self.poster)))
    page.td.close()
    page.td( )
    page.a( self.text, href=self.thread.outFileBase + '.html#' + str(self.postID) )
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
        page.a( code, href=urlSafe(code) + '_' + self.thread.title + '.html' )
      else:
        raise NameError('invalid parameter: codeLinkTo needs to be all or this_interview')

    page.td.close()
    page.tr.close()


################################################################################
# Class Thread
################################################################################
class Thread(object):
  """ The Thread class contains all the data from a particular thread

      Attributes:
        title <str>: the title of the thread
        posts <list>: a list of triples: (note, post, codes)
  """

  def __init__(self, title, outFileDir ):
    """ Returns a Thread object whose title is title, whose output files have path prefix outFileDir, and whose basename should be outFileBase """

    self.title = urlSafe(title)
    self.outFileDir = outFileDir
    self.outFileBase = urlSafe(title)
    self.posts = []
    self.codeHistogram = defaultdict(int)

  def addPost(self, post):
    """ Adds a line from the CSV to the posts list """

    self.posts.append(post)

  def toHTML(self):
    """ Prints HTML for this thread to a file in output directory """
    filename = "{}/html/{}.html".format(self.outFileDir, self.outFileBase)
    print('writing interview: ', filename)
    with open( filename, 'w' ) as outFile:   # Should be of form, e.g., Johnson.html
      header = self.outFileBase
      page = markup.page()
      page = genHeaderMenu(page, header)

      page.div(class_="num_posts")
      page.add("quotes={}".format(len(self.posts)))
      page.div.close()

      page.table( style="width: 100%" )

      page.tr(class_="table-header")
      page.th('speaker')
      page.th('quote')
      page.th('codes')
      page.tr.close()

      for post in self.posts:
        post.printHTML(page, 'this_interview')

      page.table.close()

      #outFile.write( unicode(page, encoding='utf-8') )
      outFile.write( str(page) )

  def toCSV(self):
    """ Prints CSV for this interview to a file in output directory """

    with open( self.outFileDir + '/csv/' + self.outFileBase + '.csv', 'w' ) as outFile:   # Should be of form, e.g.,  Johnson.html
      fields = ['interview','postID','poster','text','code']
      writer = csv.writer( outFile, dialect='excel' )
      writer.writerow(fields)
      for post in self.posts:
        row = [post.name, post.postID, post.poster, post.text]
        row.extend(post.codes)
        writer.writerow(row)

################################################################################
# Class Poster
################################################################################
class Poster(object):
  """ The Poster class contains all the data from a particular poster

      Attributes:
        name <str>: the username of the poster
        threads <set str>: the thread_titles for the Threads in which a poster has posted
        posts <list Post>: the posts a poster has posted
        codes <dict>: counts of the times a poster has posted something with a code:
          {
            code 1 <str>: count <int>
          }
  """

  def __init__(self, name=' '):
    """ Returns a Poster object """
    self.name = name
    self.threads = set()
    self.posts = list()
    self.codes = defaultdict(int)

  def addToThreads(self, thread_title):
    self.threads.add(thread_title)

  def addToPosts(self, post):
    self.posts.append(post)

  def addToCodeCounts(self, codes):
    for code in codes:
      self.codes[code] += 1


################################################################################
# Generate and read master CSVs. These contain all posts from all posts
# previously processed
################################################################################

def genMasterCSV( masterFilename, threads ):
  """ Generates a single CSV with all posts from all threads """

  with open(masterFilename, 'w') as outFile:
    fields = ['threadTitle', 'postID', 'poster', 'text']
    writer = csv.writer(outFile, dialect='excel')
    writer.writerow(fields)
    for thread in threads:
      for post in thread.posts:
        row = [thread.title, post.postID, post.poster, post.text]
        row.extend(post.codes)
        writer.writerow(row)


def readMasterCSV( masterFilename, outputdir ):
  """ Reads master CSV in to initiate update. TODO """

  with open(masterFilename, 'r') as inFile:
    threads = {}
    reader = csv.DictReader( inFile, dialect='excel', fieldnames=['threadTitle','postID','poster','text'], restkey='codes' )
    next(reader)
    for row in reader:

      threadTitle = row['threadTitle']
      if( threadTitle not in threads ):
        threads[threadTitle] = Thread( threadTitle, outputdir )

      if 'codes' in row:
        post = Post( threads[threadTitle], row['postID'], row['poster'], row['text'], row['codes'] )
      else:
        post = Post( threads[threadTitle], row['postID'], row['poster'], row['text'] )

      threads[threadTitle].addPost( post )

    return threads


################################################################################
# Reading CSVs and generating internal data structures
################################################################################
def readGeneratedCSVs( masterFilename, threads, codes, outputdir, codeCountsPerPoster ):
  """ Reads in generated CSVs as output by genCodeCSV() TODO """

  threads = readMasterCSV(masterFilename, outputdir)

  # numInterviews = 0
  # numQuotes = 0
  # lastPerson = ''
  for thread in threads:
    with open(thread,'r') as transFile:
      # Read in thread, populate new Interview object and codeDict
      #transReader = unicodecsv.reader( transFile, dialect='excel', encoding='utf-8' )
      transReader = csv.DictReader( transFile, dialect='excel', fieldnames=['threadTitle','postID','poster','text'], restkey='codes' )
      next(transReader)
      for row in transReader:
        threadTitle = row['threadTitle']
        if( threadTitle not in threads ):
          print("Error: couldn't find interview {} for entry in {}".format(threadTitle, thread.title))
        else:
          # Find post within thread
          found = False
          for post in threads[threadTitle].posts:
            if( post.postID == row['postID'] ):
              found = True
              post.poster = row['poster']
              post.text = row['text']
              if( 'codes' in row ):
                post.codes = row['codes']
              else:
                post.codes = []
          if( not found ):
            print("Error: couldn't find post " + row['postID'] + " for entry in " + thread.title)

  threadList = sorted(threads.values(), key=lambda x: x.title)

  return threadList


def readOriginalCSVs( originalCSVs, allCodes, outputdir, codeCounts ):
  """ Reads in CSVs in their original post-Google spreadsheet form """

  numThreads = 0
  numPosts = 0
  threads = []
  allCodeCorrections = {}
  allPosters = {}

  for originalCSV in originalCSVs:
    with open(originalCSV, 'r') as transFile:
      threadFileName = os.path.splitext(os.path.basename(originalCSV))[0]

      # Read in thread, populate new Thread object
      numThreads += 1
      thread = Thread(threadFileName, outputdir)

      for line in transFile:
        # Our reformatted threads have the format:
        # speaker =DELIM= utterance =DELIM= tag, tag, tag, ...
        (poster, text, tags) = line.split('=DELIM=')
        if (text != ''):
          numPosts += 1

          # Process post codes
          post_codes = tags.split(', ')
          strippedCodes = []
          for code in post_codes:
            strippedCode = urlSafe(stripQuotesSpace( code ))
            if( strippedCode == '' ):
              continue
            if( strippedCode not in allCodes):
              correctedCode, allCodeCorrections = mergeCodes( strippedCode, allCodes, allCodeCorrections, skip=True ) #set skip to false to correct codes to nearest code by edit distance
              if( correctedCode == '' ):
                print("Skipping unrecognized code in '" + strippedCode + "' in file " + thread.title + " that could not be merged")
                continue
              strippedCode = correctedCode
            strippedCodes.append( strippedCode )
            # Add the poster to the set of people who have said something with this code
            codeCounts[strippedCode]['posters'].add( poster )
            # Add the thread to the set of threads that have used this code
            codeCounts[strippedCode]['threads'].add( thread.title )
            # Increment the counter of posts with this code
            codeCounts[strippedCode]['posts'] += 1
            # Add this code to the thread's code histogram
            thread.codeHistogram[strippedCode] += 1

          post = Post(thread, numPosts, poster, text, strippedCodes)
          thread.addPost(post)

          # Process poster
          if poster not in allPosters:
            allPosters[poster] = Poster(poster)

          allPosters[poster].addToPosts(post)
          allPosters[poster].addToThreads(thread.title)
          allPosters[poster].addToCodeCounts(strippedCodes)

      threads.append(thread)

    transFile.close()

  return threads, codeCounts, allPosters


################################################################################
# Main function
################################################################################
def main():
  parser = argparse.ArgumentParser(description='Process coded transcripts given a codebook.')
  parser.add_argument('-u', '--update', type=str, help="update the indicated master.csv")
  parser.add_argument('project', metavar="project", help="name of project")
  parser.add_argument('outputdir', metavar='outputdir', help="directory where outputs will be sent. If it doesn't exist it will be created")
  parser.add_argument('codebook', metavar='codebook', help='the codebook CSV file')
  parser.add_argument('transcripts', metavar='transcripts', help='one or more transcript CSV files, or a directory', nargs='+')
#parser.add_argument('output', metavar='output', help='the output, processed CSV file')
  args = vars(parser.parse_args())

  outputdir = args['outputdir']
  if outputdir[-1] == '/':
    outputdir = outputdir[:-1]

  project_title = args['project']

  # Check outputdir, make subfolders
  try:
    os.makedirs(outputdir + '/html/')
    os.makedirs(outputdir + '/csv/')
  except OSError as exception:
    if exception.errno != errno.EEXIST:
      if( not os.path.isdir(outputdir) ):
        print("Error: outputdir specified as", outputdir, "exists but is not a directory")
        raise


  codes = []
  codeCounts = {}
  with open(args['codebook'], 'r') as codeFile:
    # Read in the codes
    codeReader = csv.reader(codeFile, dialect='excel')
    for row in codeReader:
      # first value is code, second is description. We ignore description for now
      code = urlSafe(stripQuotesSpace( row[0] ))
      if( code != '' ):
        codes.append( code )
        codeCounts[code] = {
          'posters': set(),
          'threads': set(),
          'posts': 0
        }

    # Is this an update?
    if( args['update'] ):
      threads = readGeneratedCSVs( args['update'], args['transcripts'], codes, outputdir, codeCounts )
    else:
      transcripts_path = Path(args['transcripts'][0])
      # Are we analyzing an entire directory?
      if transcripts_path.is_dir():
        originalCSVs = [args['transcripts'][0] + path.name for path in Path(args['transcripts'][0]).glob('*.csv')]
        print('Processing directory: ', originalCSVs)
      else:
        originalCSVs = args['transcripts']

      # Read the original CSVs
      threads, codeCounts, posters = readOriginalCSVs( originalCSVs, codes, outputdir, codeCounts )

      # Generate a histogram HTML page
      genHistograms( threads, outputdir, codeCounts, project_title )

      # Write code_counts.csv
      genCodeCounts( codeCounts, outputdir )

    # Write out a master CSV
    genMasterCSV( outputdir + '/csv/master.csv', threads )

    # Write out individual posters' pages. TODO: make it an instance method?
    genPosterHTML(posters, outputdir)

    # Write out an interview HTML page
    for interview in threads:
      interview.toHTML()

    # Write out individual HTML for each code
    for code in codes:
      genCodeHTML( threads, outputdir, code, project_title )

    # Write out individual CSV's for each code
    for code in codes:
      genCodeCSV( threads, outputdir, code )

    # Write out individual HTML for each code, interview pair
    for code in codes:
      genCodePerTransHTML( threads, outputdir, code )

    # Generate the main index.html
    genIndex( threads, outputdir, codeCounts, project_title )

    # Generate the stylesheet from the main one
    genStylesheet( outputdir )

    # Print a direct link to the index file for viewing
    print('\nDone! View output at: {}'.format(os.path.abspath(outputdir+'/html/index.html')))

if __name__ == '__main__':
  main()
