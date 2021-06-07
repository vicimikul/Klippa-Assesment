# Import necessary modules
import os
import argparse
import json
import requests
import click
import concurrent.futures

# Global variable for the directory statistics feature
resultList = []

# Class to store the authentification key for the API
class KeyDictionary(argparse.Action):
    def __call__(self, initialParser, namespace, values, option_string=None):
        setattr(namespace, self.dest, {'X-Auth-Key' : values})

# Export URL results to json
def exportToJsonURL(requestOutput, url):
    f = open(url + ".json","w+")
    f.write(requestOutput.text)

# Export file results to json
def exportToJson(requestOutput, docPath):
    # Get the filename
    splittedPath = docPath.split('/')
    filename = splittedPath[len(splittedPath) - 1]
    # Write the request's output to a json file
    f = open(filename + ".json","w+")
    f.write(requestOutput.text)

# Process a URL
def processURL(arguments):
    return requests.post("https://custom-ocr.klippa.com/api/v1/parseDocument", headers = arguments.key, data = vars(arguments))

# Process a file
def processFile(arguments):
    file = {'document' : open(arguments.document,'rb')}
    return requests.post("https://custom-ocr.klippa.com/api/v1/parseDocument", headers = arguments.key, data = vars(arguments), files = file)

# Special function to process files inside directory in a concurrent way
def processDirFile(item):
    arguments = directoryArguments
    arguments.document = os.getcwd() + '/' + directoryName + '/' + item
    file = {'document' : open(arguments.document,'rb')}
    results =  requests.post("https://custom-ocr.klippa.com/api/v1/parseDocument", headers = arguments.key, data = vars(arguments), files = file)
    values = json.loads(results.text)
    resultList.append(values)
    if arguments.exportToJson == True:
        arguments.document = os.getcwd() + '/' + directoryName + '/' + item
        exportToJson(results, arguments.document)
    else:
        print()
        print(json.dumps(results.json(), indent = 2), flush=True)
        print()

# Process directory
def processDir(arguments):
    global directoryName 
    directoryName = arguments.document   
    global directoryArguments
    directoryArguments = arguments
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(processDirFile, os.listdir(directoryName))

# Compute statistics for directories
def computeResults(listResults):
    totalAmount = 0
    totalAmountChange = 0
    totalAmountShipping = 0
    totalVatAmount = 0
    totalAmountExVat = 0
    for item in listResults:
        totalAmount += item['data']['amount']
        totalAmountChange += item['data']['amount_change']
        totalAmountShipping += item['data']['amount_shipping']
        totalVatAmount += item['data']['vatamount']
        totalAmountExVat += item['data']['amountexvat']
    print("totalAmount: " + str(totalAmount))
    print("totalAmountChange: " + str(totalAmountChange))
    print("totalAmountShipping: " + str(totalAmountShipping))
    print("totalVatAmount: " + str(totalVatAmount))
    print("totalAmountExVat: " + str(totalAmountExVat))



# Define the parser 
initialParser = argparse.ArgumentParser(description = 'CLI parser for the API flags', fromfile_prefix_chars='@')
# Add the option of providing the API key
initialParser.add_argument('-k','--key' , type=str, action = KeyDictionary, required = True, help = ' API key')
# Add the option of providing a file, which can be either a document/file or URL
docsParser = initialParser.add_mutually_exclusive_group(required = True)
docsParser.add_argument('-d','--document', type = str, help = 'document to process')
docsParser.add_argument('-u','--url', type=str, help = 'URL for the file to process')
# Add the option of providing the template
initialParser.add_argument('-t',  '--template', type = str, help = 'template of document')
# Add the option of choosing between fast or full processing, fast is default
initialParser.add_argument('-e', '--extraction', type = str, default = 'fast', choices = ['full','fast'], help = 'choose whether you want full or fast extraction')
# Add the option of exporting results in a json file, default is False
initialParser.add_argument('-j', '--exportToJson', type = bool, default = False, help = 'choose between seeing results in terminal or export them to a json')
# Add the option to monitor a directory. The Parser will check if the given doc path is actually a directory
initialParser.add_argument('-m', '--monitor', type = bool, default = False, help = 'choose the option to monitor a directory')


arguments = initialParser.parse_args()

### Sending requests
if arguments.monitor == True: 
    # Check if the 'document' is a file, URL or directory

    # The monitor function ignores any item in the directory at the moment of start and only automatically process the files that are added during its run
    if arguments.url == None and os.path.isdir(arguments.document):
        dirName = arguments.document
        itemsInFolder = os.listdir(dirName)
        count = len(itemsInFolder)
        while True:
            currentItems = os.listdir(dirName)
            if len(currentItems) != count:
                itemsDiff = [x for x in currentItems if x not in itemsInFolder]
                for x in range(len(itemsDiff)):
                    arguments.document = os.getcwd() + '/' + dirName + '/' + itemsDiff[0]
                    results = processFile(arguments)
                    # Export to Json if that's the case
                    if arguments.exportToJson == True:
                        exportToJson(results, arguments.document)
                    else:
                        print()
                        print(json.dumps(results.json(), indent = 2))
                        print()
    # File is URL, so do not monitor
    elif arguments.url != None:
        print("You are trying to monitor a URL. Unfortunately this is not possible, only directories can be monitored.")
        if click.confirm("Do you want to process the URL instead?", default=False):
            arguments.monitor = False
        else:
            quit()
    # File is document so do not monitor
    elif os.path.isfile(arguments.document):
        print("You are trying to monitor a FILE. Unfortunately this is not possible, only directories can be monitored.")
        if click.confirm("Do you want to process the FILE instead?", default=False):
            arguments.monitor = False
        else:
            quit()


# In case the monitor flag is False, run the program just once with the given data
if arguments.monitor == False:
    # File is URL
    if arguments.url != None:
        results = processURL(arguments)
        # Export to Json if that's the case
        if arguments.exportToJson == True:
            exportToJsonURL(results, arguments.url)
        else:
            print(json.dumps(results.json(), indent = 4))      
        quit()    
    # File is document
    elif os.path.isfile(arguments.document):
        results = processFile(arguments)
        # Export to Json if that's the case
        if arguments.exportToJson == True:
            exportToJson(results, arguments.document)
        else:
            print(json.dumps(results.json(), indent = 4))
        quit()
    
    #File is directory. use concurrency to batch process the files in parallel
    elif os.path.isdir(arguments.document):
        processDir(arguments)
        computeResults(resultList)
