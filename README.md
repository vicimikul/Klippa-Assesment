# CLI for Klippa's OCR API
This tool aims to automate the interaction of users with the OCR API by providing an easy to use command line interface and a lot of useful features. Users can simply send requests using the default settings or provide one or all of the arguments, if desired. They can also make use of the `config.txt` file, which aims to ease the input of parameters and allow users to run the script as simple as running any other one. 

## Setup
You need Python 3 in order to run this tool. 

## Features
- Provide the API key
- Provide the docs template
- Choose between fast or full text extraction
- Choose a file/URL to process
- View the results directly in terminal
- Export the results to a json file
### Extras
- Choose a directory to process & batch process all the files inside
-  Directory statistics based on files inside 
-  Monitor a directory and automatically process newly added files
- Concurrency for batch processing in folders
- Multi threading for the monitor feature, as it does not stop monitoring when processing a file #TODO
- Provide arguments for the CLI using the `config.txt` file


## How to run
### Directly from the CLI
`python3 parser.py -k 'Your API key' -d 'directory' -m True -j True -e full`

### Using the config.txt file
`python3 parser.py @config.txt`

### Mandatory arguments:
`-k`/`--key` The authentication key for the API\
`-d`/`--document`The name of the document/directory\
`-u`/`--url`The URL of the file\
\
NOTE: You can either provide a document/directory or a URL, but not both

### Optional arguments:
`-t`/`--template` The document's template\
`-e`/`--extraction`Choose between `fast (default)` or `full`extraction\
`-j`/`--exportToJson`Choose whether to display the results in terminal (default) or export to a json file\
`-m`/`--monitor`Monitor a given directory. Does not wok with files or URLs


License
----

 MIT License



