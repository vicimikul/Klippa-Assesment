# Import necessary modules
import os
import argparse
import json
from posixpath import normcase
from typing import NoReturn
import requests
import click
import concurrent.futures
from requests.models import Response

# Class to store the authentification key for the API
class KeyDictionary(argparse.Action):
    def __call__(self, initialParser, namespace, values, option_string=None) -> NoReturn:
        setattr(namespace, self.dest, {'X-Auth-Key' : values})


# Parser class
class Parser:
    # Define the parser 
    arguments = []

    def __init__(self) -> NoReturn:
        self.initialParser = argparse.ArgumentParser(description = 'CLI parser for the API flags',fromfile_prefix_chars='@')
        # Add the option of providing the API key
        self.initialParser.add_argument('-k','--key' , type=str, action = KeyDictionary, required = True, help = ' API key')
        # Add the option of providing a file, which can be either a document/file or URL
        docsParser = self.initialParser.add_mutually_exclusive_group(required = True)
        docsParser.add_argument('-d','--document', type = str, help = 'document to process')
        docsParser.add_argument('-u','--url', type=str, help = 'URL for the file to process')
        # Add the option of providing the template
        self.initialParser.add_argument('-t',  '--template', type = str, help = 'template of document')
        # Add the option of choosing between fast or full processing, fast is default
        self.initialParser.add_argument('-e', '--extraction', type = str, default = 'fast', choices = ['full','fast'], help = 'choose whether you want full or fast extraction')
        # Add the option of exporting results in a json file, default is False
        self.initialParser.add_argument('-j', '--exportToJson', type = bool, default = False, help = 'choose between seeing results in terminal or export them to a json')
        # Add the option to monitor a directory. The Parser will check if the given doc path is actually a directory
        self.initialParser.add_argument('-m', '--monitor', type = bool, default = False, help = 'choose the option to monitor a directory')
        self.arguments = self.initialParser.parse_args()

    # Get the arguments of the CLI
    def getArguments(self) -> list:
        return self.arguments

    # Get file type
    def getFileType(self) -> str:
        if self.arguments.url != None:
            return "url"
        elif os.path.isfile(self.arguments.document):
            return "doc"
        elif os.path.isdir(self.arguments.document):
            return "dir"

    # Check if export parameter is true
    def shouldExport(self) -> bool:
        if self.arguments.exportToJson == True:
            return True

    #Check if monitor parameter is true
    def shouldMonitor(self) -> bool:
        if self.arguments.monitor == True:
            return True

# Processing class
class Processer():
    # Initialize variables needed inside this class
    resultList = []
    responses = {}
    directoryName = ""

    def __init__(self, arguments) -> NoReturn:
        self.arguments = arguments

    # Function that returns the response of the URL process
    def processURL(self) -> Response:
        return requests.post("https://custom-ocr.klippa.com/api/v1/parseDocument", headers = self.arguments.key, data = vars(self.arguments))
    
    # Function that returns the response of the file process
    def processFile(self) -> Response:
        file = {'document' : open(self.arguments.document,'rb')}
        return requests.post("https://custom-ocr.klippa.com/api/v1/parseDocument", headers = self.arguments.key, data = vars(self.arguments), files = file)
    
    # Function to process a directory in a concurrent way
    def processDir(self) -> NoReturn:
        self.directoryName = self.arguments.document
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            executor.map(self.processDirFile, os.listdir(self.directoryName))
    
    # Function to process file in a dir 
    def processDirFile(self, item) -> NoReturn:
        arguments = self.arguments
        arguments.document = os.getcwd() + '/' + self.directoryName + '/' + item
        file = {'document' : open(arguments.document,'rb')}
        results =  requests.post("https://custom-ocr.klippa.com/api/v1/parseDocument", headers = arguments.key, data = vars(arguments), files = file)
        self.resultList.append(json.loads(results.text))
        self.responses[item] = results
    
    # Function that returns the statistics for a previously processed dir 
    def getResultsList(self) -> dict:
        totals = {'totalAmount': 0, 'totalAmountChange': 0, 'totalAmountShipping': 0, 'totalVatAmount': 0, 'totalAmountExVat': 0}
        for item in self.resultList:
            print(item)
            totals['totalAmount'] += item['data']['amount']
            totals['totalAmountChange'] += item['data']['amount_change']
            totals['totalAmountShipping'] += item['data']['amount_shipping']
            totals['totalVatAmount'] += item['data']['vatamount']
            totals['totalAmountExVat'] += item['data']['amountexvat']
        return totals
    
    # Function that returns the directory requests' responses
    def returnDirResponses(self) -> dict:
        return self.responses

# Export class
class Exporter:
    # Export URL results
    def exportToJsonURL(self, requestOutput: Response):
        f = open("url_results"  + ".json","w+")
        f.write(requestOutput.text)     

    # Export document results
    def exportToJsonFile(self, requestOutput: Response, docPath: str) -> NoReturn:
         # Get the filename
        splittedPath = docPath.split('/')
        filename = splittedPath[len(splittedPath) - 1]
        # Write the request's output to a json file
        f = open(filename + ".json","w+")
        f.write(requestOutput.text)

class Monitor():
    def __init__(self) -> NoReturn:
        pass

    def __call__(self, arguments) -> NoReturn:
        processer = Processer(arguments)
        exporter = Exporter()
        if arguments.url == None and os.path.isdir(arguments.document):
            dirName = arguments.document
            itemsInFolder = os.listdir(dirName)
            count = len(itemsInFolder)
            while True:
                currentItems = os.listdir(dirName)
                if len(currentItems) != count:
                    itemsDiff = [x for x in currentItems if x not in itemsInFolder]
                    for x in itemsDiff:
                        arguments.document = os.getcwd() + '/' + dirName + '/' + x
                        results = processer.processFile()
                        # Export to Json if that's the case
                        if arguments.exportToJson == True:
                            exporter.exportToJsonFile(results, arguments.document)
                        else:
                            print()
                            print(json.dumps(results.json(), indent = 2))
                            print()
                count = len(currentItems)
        # File is URL, so do not monitor
        elif arguments.url != None or os.path.isfile(arguments.document) == True:
            print("You are trying to monitor a URL/FILE. Unfortunately this is not possible, only directories can be monitored.")
            if click.confirm("Do you want to process the URL/FILE instead?", default=False):
                arguments.monitor = False
            else:
                quit()
 

if __name__ == '__main__':

    parser = Parser()
    arguments = parser.getArguments()

    if parser.shouldMonitor() == True:
        monitor = Monitor()
        monitor(arguments)
    else:
        processer = Processer(arguments)
        exporter = Exporter()
        docType = parser.getFileType()
        shouldExport = parser.shouldExport()

        if docType == "url":
            results = processer.processURL()
            if shouldExport:
                exporter.exportToJsonURL(results)
                quit()
            else:
                print(json.dumps(results.json(), indent=2))

        elif docType == "doc":
            results = processer.processFile()
            if shouldExport:
                exporter.exportToJsonFile(results, arguments.document)
                quit()
            else:
                print(json.dumps(results.json(), indent=2))

        elif docType == "dir":
            processer.processDir()
            results = processer.returnDirResponses()
            if shouldExport:
                for key in results:
                    result = results[key]
                    path = os.getcwd() + '/' + arguments.document + '/' + key
                    exporter.exportToJsonFile(result, path)
            else:
                for key in results:
                    print(json.dumps(results[key].json(), indent=2))
            statistics = processer.getResultsList()
            for item in statistics.items():
                print(item)
