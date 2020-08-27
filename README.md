# Qual code-visualizer

This repo contains a visualizer for a qualitatively coded dataset. Given a codebook and a set of tagged transcripts, it will produce a simple HTML-based visualization of your dataset you can open on any browser. Transcripts are human-readable and navigable by code, and codes are counted by occurrence.

This repo is templatable, so have at it.

## Setup

We'll run this tool in a python virtualenv. Ensure you have a python2 installation. Then:

```cli
virtualenv -p <path to your python2, for instance /usr/bin/python> py27
source py27/bin/activate
pip install -r requirements.txt
```

To deactivate the virtualenv:

```cli
deactivate
```

## Data

Place the codebook in your top-level directory. It should be a CSV should be formatted as:
```csv
   code1 , description1
   code2 , description2
   ...
   code3, description3
```
where codes are (possibly quote-surrounded) strings and descriptions are (possibly quote-delimited) strings. We will eat extra ',' appearing at end of lines.

Place your transcripts either in your top-level directory or in a directory (e.g. `csvs/`) at the top level. They should be CSVs formatted as:
```csv
Name: text , code1 , code2 , ...
```
where `Name: text` is a string for some text that Name has said, and each code is a string.

## Running codes

This repo contains a script (``code-extract.py``) that will process either a directory of transcripts or a list of transcripts. Usage is as follows:

```cli
python code-extract.py [update] <output directory> <codebook> [master.csv] [<csv1> <csv2>] ...
python code-extract.py [update] <output directory> <codebook> [master.csv] [<csv directory>] ...
```

`update` is optional, and specifies that the transcripts are already processed by `code-extract.py` previously. This will regenerate output HTML and CSVs by updating based on the CSVs included. All CSVs should be included if one wants to update.

`master.csv` is for doing updates. It contains all the quotes from all the interviews, and any other CSV is used to update values in that `master.csv`.

The script will produce a folder of HTML in the output directory specified. Open the resulting ``outputdir/index.html`` in a browser to navigate through your codes.
