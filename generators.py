#!/usr/bin/python3
import sys

if sys.version_info[0] != 3:
	print("This script requires Python version 3")
	sys.exit(1)

from collections import defaultdict
import operator
import markup
import csv
import shutil

from util import urlSafe

################################################################################
# HTML generators
################################################################################


def genIndex(threads, outputdir, codeCounts, project_title):
	""" Generates an index linking to all the main pages.
			Inputs:
				threads <list>: list of thread objects
				outputdir <str>: directory for output specified in arguments
				codeCounts <dict>: counts per code, processed in readOriginalCSVs
					{
						code1: {
							'threads': <set> of the distinct titles of threads with this code,
							'posts': <int> count of number of posts for this code,
							'posters': <set> of the distinct posters who said something with this code,
						}
						...
					}
				project_title <str>: used to generate the page title in the format "<project_title>: Coded Transcripts"
			Outputs:
				Writes index to file, does not return
	"""

	freqSortedCodes = sorted(codeCounts.items(), key=lambda tup: len(tup[1]['threads']), reverse=True)

	with open(outputdir + '/html/' + 'index.html', 'w') as outFile:
		header = "{}: Coded Transcripts".format(project_title)
		page = markup.page()
		page = genHeaderMenu(page, header)

		page.table(style="width: 100%")

		# Write codes header
		page.tr()
		page.td(class_="index-header")
		page.add('<h1>codes (n={})</h1>'.format(len(freqSortedCodes)))
		page.td.close()
		page.tr.close()

		# Write sorted list of codes with frequencies
		page.tr()
		page.td(class_="index-codes")
		for codeFreqPair in freqSortedCodes:
			code = codeFreqPair[0]
			post_count = codeFreqPair[1]['posts']
			thread_count = len(codeFreqPair[1]['threads'])
			page.div(class_="index-code")
			page.a(code, href=urlSafe(code) + '.html')
			page.add(' &nbsp;&nbsp;(quotes={}, interviews={})'.format(
														post_count, thread_count))
			page.div.close()
			#page.add('&nbsp;&nbsp;-&nbsp;&nbsp;')
		page.td.close()
		page.tr.close()

		num_posts = 0
		for thread in threads:
			num_posts += len(thread.posts)

		# Write threads header
		page.tr()
		page.td(class_="index-header")
		page.add('<h1>interviews (n={}, quotes={})</h1>'.format(len(threads), num_posts))
		page.td.close()
		page.tr.close()

		# Write sorted list of threads
		page.tr()
		page.td(class_="index-threads")
		sorted_threads = sorted(threads, key=lambda x: x.title)
		for thread in sorted_threads:
			page.a(thread.title, href=thread.outFileBase + '.html')
			page.br()
		page.td.close()
		page.tr.close()

		page.table.close()

		outFile.write(str(page))
	outFile.close()


def genHistograms(threads, outputdir, codeCounts, project_title):
	""" Generates an index linking to all the main pages.
			Inputs:
				threads <list>: list of thread objects
				outputdir <str>: directory for output specified in arguments
				codeCounts <dict>: counts per code, processed in readOriginalCSVs
					{
						code1: {
							'threads': <set> of the distinct titles of threads with this code,
							'posts': <int> count of number of posts for this code,
							'posters': <set> of the distinct posters who said something with this code,
						}
						...
					}
				project_title <str>: used to generate the page title in the format "<project_title>: Coded Transcripts"
			Outputs:
				Writes index to file, does not return
	"""
	freqSortedCodeCounts = sorted(
		codeCounts.items(), key=lambda tup: len(tup[1]['threads']), reverse=True)

	with open(outputdir + '/html/' + 'histograms.html', mode='w+') as outFile:
		header = "{}: Histograms".format(project_title)
		page = markup.page()
		page = genHeaderMenu(page, header)

		page.table(style="width: 100%", id_="histograms-table")

		page.tr(class_="table-header")
		page.th('code')
		page.th('# distinct interviews')
		page.th('# distinct quotes')
		page.th('# distinct speakers')
		page.th('speakers')
		page.tr.close()
		for freqSortedCodeCount in freqSortedCodeCounts:
			code = freqSortedCodeCount[0]
			posters = freqSortedCodeCount[1]['posters']
			threads = freqSortedCodeCount[1]['threads']
			post_count = freqSortedCodeCount[1]['posts']
			page.tr()
			page.td()
			page.a(code, href="{}.html".format(urlSafe(code)))
			page.td.close()
			page.td(str(len(threads)))
			page.td(str(post_count))
			page.td(str(len(posters)))
			page.td(class_="histogram-posters")
			for poster in posters:
				page.a(poster, href="{}.html".format(urlSafe(poster)))
			page.td.close()
			page.tr.close()
		page.table.close()

		outFile.write(str(page))
	outFile.close()

# Generators for code page


def genCodePostsHTML(threads, outputdir, code, project_title):
	""" Generates the posts tab of a code page """

	with open("{}/html/{}.html".format(outputdir, urlSafe(code)), mode="w") as outFile:
		header = "All quotes in {} tagged with {}".format(project_title, code)
		page = markup.page()
		page = genHeaderMenu(page, header)

		page.div(class_="submenu")
		page.a("quotes", color="blue", href="{}.html".format(urlSafe(code)))
		page.add("&nbsp;&nbsp;-&nbsp;&nbsp;")
		page.a("interviews", color="blue",
					 href="{}_interviews.html".format(urlSafe(code)))
		page.div.close()

		page.table(style="width: 100%; table-layout: fixed; max-width: 90vw")

		page.tr(class_="table-header")
		page.th('speaker', width="15%")
		page.th('quote', width="50%")
		page.th('codes', width="20%")
		page.tr.close()

		for thread in threads:
			for post in thread.posts:
				if(code in post.codes):
					post.printHTML(page)

		page.table.close()

		outFile.write(str(page))


def genCodePostsHTMLReddit(threads, outputdir, code, project_title):
	""" Generates the posts tab of a code page """

	with open("{}/html/{}.html".format(outputdir, urlSafe(code)), mode="w") as outFile:
		header = "All posts in {} tagged with {}".format(project_title, code)
		page = markup.page()
		page = genHeaderMenu(page, header)

		page.div(class_="submenu")
		page.a("quotes", color="blue", href="{}.html".format(urlSafe(code)))
		page.add("&nbsp;&nbsp;-&nbsp;&nbsp;")
		page.a("interviews", color="blue",
					 href="{}_interviews.html".format(urlSafe(code)))
		page.div.close()

		page.table(style="width: 100%; table-layout: fixed; max-width: 90vw")

		page.tr(class_="table-header")
		page.th('speaker', width="15%")
		page.th('text', width="50%")
		page.th('codes', width="20%")
		page.tr.close()

		for thread in threads:
			for post in thread.posts:
				if(code in post.codes):
					post.printHTML(page)

		page.table.close()

		outFile.write(str(page))


def genCodeThreadsHTML(threads, outputdir, code, project_title):
	""" Generates the threads tab of a code page """

	with open("{}/html/{}_interviews.html".format(outputdir, urlSafe(code)), mode="w") as outFile:
		header = "All threads in {} tagged with {}".format(project_title, code)
		page = markup.page()
		page = genHeaderMenu(page, header)

		sorted_threads = sorted([thread for thread in threads if code in thread.codeHistogram], key=lambda thread: thread.codeHistogram[code], reverse=True)

		page.div(class_="submenu")
		page.a("quotes", color="blue", href="{}.html".format(urlSafe(code)))
		page.add("&nbsp;&nbsp;-&nbsp;&nbsp;")
		page.a("interviews (n={})".format(len(sorted_threads)),
					 color="blue", href="{}_interviews.html".format(urlSafe(code)))
		page.div.close()

		page.table(style="width: 100%; table-layout: fixed; max-width: 90vw")

		page.tr(class_="table-header")
		page.th('interview', width="50%")
		page.th('# quotes with this code', width="15%")
		page.tr.close()

		for thread in sorted_threads:
			page.tr()
			# Thread title
			page.td()
			page.a(thread.title, href="{}_{}.html".format(urlSafe(code), thread.title))
			page.td.close()
			# Posts with this code
			page.td(thread.codeHistogram[code])
			page.tr.close()

		page.table.close()

		outFile.write(str(page))


def genCodeHTML(threads, outputdir, code, project_title):
	""" Searches through all threads and extracts all references to each code, writes to an HTML output """
	genCodePostsHTML(threads, outputdir, code, project_title)
	genCodeThreadsHTML(threads, outputdir, code, project_title)


def genCodeHTMLReddit(threads, outputdir, code, project_title):
	""" Searches through all threads and extracts all references to each code, writes to an HTML output """
	genCodePostsHTMLReddit(threads, outputdir, code, project_title)
	genCodeThreadsHTML(threads, outputdir, code, project_title)


def genCodePerTransHTML(threads, outputdir, code):
	""" For each thread, output a page for each code with all the posts coded as such """

	for thread in threads:
		with open(outputdir + '/html/' + urlSafe(code) + '_' + thread.title + '.html', 'w') as outFile:
			header = "All references to {} in interview {}".format(code, thread.title)
			page = markup.page()
			page = genHeaderMenu(page, header)

			page.table(style="width: 100%")

			for post in thread.posts:
				if(code in post.codes):
					post.printHTML(page)

			page.table.close()

			outFile.write(str(page))

################################################################################
# Poster page generators
################################################################################


def genPosterCodesHTML(poster, outputdir):
	""" For a given poster, generate their codes page """
	username = urlSafe(poster.name)
	with open("{}/html/{}.html".format(outputdir, username), mode="w+") as outfile:
		header = "All coded activity for poster {}".format(username)
		page = markup.page()
		page = genHeaderMenu(page, header)

		page.div(class_="submenu")
		page.a("codes", color="blue", href="{}.html".format(username))
		page.add("&nbsp;&nbsp;-&nbsp;&nbsp;")
		page.a("interviews", color="blue", href="{}_interviews.html".format(username))
		page.add("&nbsp;&nbsp;-&nbsp;&nbsp;")
		page.a("quotes", color="blue", href="{}_quotes.html".format(username))
		page.div.close()

		page.table(style="width: 100%; table-layout: fixed")

		# First write a block for all the codes the poster engages with, and how often they posted something with that code

		page.tr(class_="table-header")
		page.add("<h1>codes (n={})</h1>".format(len(poster.codes)))
		page.tr.close()

		page.tr(class_="table-header")
		page.th("code")
		page.th("count")
		page.tr.close()

		freq_sorted_code_counts = sorted(poster.codes.items(), key=lambda tup: tup[1], reverse=True)

		for code, count in freq_sorted_code_counts:
			page.tr(class_="poster-code")
			page.td()
			page.a(code, href="{}.html".format(code))
			page.td.close()
			page.td(count)
			page.tr.close()

		page.table.close()
		outfile.write(str(page))
	outfile.close()


def genPosterThreadsHTML(poster, outputdir):
	""" For a given poster, generate their threads page """
	username = urlSafe(poster.name)
	with open("{}/html/{}_interviews.html".format(outputdir, username), mode="w+") as outfile:
		header = "All coded activity for poster {}".format(username)
		page = markup.page()
		page = genHeaderMenu(page, header)

		page.div(class_="submenu")
		page.a("codes", color="blue", href="{}.html".format(username))
		page.add("&nbsp;&nbsp;-&nbsp;&nbsp;")
		page.a("interviews", color="blue", href="{}_interviews.html".format(username))
		page.add("&nbsp;&nbsp;-&nbsp;&nbsp;")
		page.a("quotes", color="blue", href="{}_quotes.html".format(username))
		page.div.close()

		page.table(style="width: 100%; table-layout: fixed")

		# First write a block for all the codes the poster engages with, and how often they posted something with that code

		page.tr(class_="table-header")
		page.add("<h1>interviews (n={})</h1>".format(len(poster.threads)))
		page.tr.close()

		for thread_title in poster.threads:
			page.tr(class_="poster-thread")
			page.td()
			page.a(thread_title, href="{}.html".format(urlSafe(thread_title)))
			page.td.close()
			page.tr.close()

		page.table.close()
		outfile.write(str(page))
	outfile.close()


def genPosterPostsHTML(poster, outputdir):
	""" For a given poster, generate their posts page """
	username = urlSafe(poster.name)
	with open("{}/html/{}_quotes.html".format(outputdir, username), mode="w+") as outfile:
		header = "All coded activity for poster {}".format(username)
		page = markup.page()
		page = genHeaderMenu(page, header)

		page.div(class_="submenu")
		page.a("codes", color="blue", href="{}.html".format(username))
		page.add("&nbsp;&nbsp;-&nbsp;&nbsp;")
		page.a("interviews", color="blue", href="{}_interviews.html".format(username))
		page.add("&nbsp;&nbsp;-&nbsp;&nbsp;")
		page.a("quotes", color="blue", href="{}_quotes.html".format(username))
		page.div.close()

		page.table(style="width: 100%; table-layout: fixed")

		# First write a block for all the codes the poster engages with, and how often they posted something with that code

		page.tr(class_="table-header")
		page.add("<h1>quotes (n={})</h1>".format(len(poster.threads)))
		page.tr.close()

		for post in poster.posts:
			post.printHTML(page, codeLinkTo="this_interview")

		page.table.close()
		outfile.write(str(page))
	outfile.close()


def genPosterHTML(posters, outputdir):
	""" For each poster, output a page showing their codes, threads and posts """
	for poster_name, poster in posters.items():
		genPosterCodesHTML(poster, outputdir)
		genPosterThreadsHTML(poster, outputdir)
		genPosterPostsHTML(poster, outputdir)


################################################################################
# CSV generators
################################################################################

def genCodeCSV(threads, outputdir, code):
	""" Searches through all threads and extracts all references to each code, writes to a CSV output """

	with open(outputdir + '/csv/' + urlSafe(code) + '.csv', 'w') as outFile:
		fields = ['thread', 'postID', 'speaker', 'text', 'code']

		writer = csv.writer(outFile, dialect='excel')

		writer.writerow(fields)

		for thread in threads:
			for post in thread.posts:
				if(code in post.codes):
					row = [thread.title, post.postID, post.poster, post.text]
					row.extend(post.codes)
					writer.writerow(row)


def genCodeCounts(codeCounts, outputdir):
	""" Generates code_counts.csv """

	with open(outputdir + '/csv/code_counts.csv', mode="w") as outfile:
		outfile.write('code,interview_count,quote_count,speaker_count\n')
		freq_sorted_code_counts = sorted(codeCounts.items(), key=lambda tup: len(tup[1]), reverse=True)
		for code, counts in freq_sorted_code_counts:
			interview_count = len(counts['threads'])
			quote_count = counts['posts']
			speaker_count = len(counts['posters'])
			outfile.write("{},{},{},{}\n".format(
											code, interview_count, quote_count, speaker_count))
	outfile.close()

################################################################################
# HTML formatting generators
################################################################################


def genStylesheet(outputdir):
	""" Copies the main stylesheet into the output's html folder """
	master_layout_file = 'layout.css'
	print('writing stylesheet from master: {}'.format(master_layout_file))

	output_file = "{}/html/{}".format(outputdir, "layout.css")

	shutil.copyfile(master_layout_file, output_file)


def genHeaderMenu(page, header):
	""" Writes the header and menu to the top of each page. Returns the page instance.
	"""
	styles = ('layout.css')
	page = markup.page()
	page.init(title=header, css=styles, charset='utf-8')
	page.div(id_="index-header")
	page.add("<h1>{}</h1>".format(header))
	page.div(id_="index-menu")
	page.a("index", color="blue", href="index.html")
	page.add("&nbsp;&nbsp;-&nbsp;&nbsp;")
	page.a("histograms", color="blue", href="histograms.html")
	page.div.close()
	page.div.close()
	return page
