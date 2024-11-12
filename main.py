import os
import pdfplumber
import json
from multiprocessing import Process
from elasticsearch import Elasticsearch

def ingestData(indexName, text, esHost, apiKey=None):
    # Set up Elasticsearch client with API key
    es = Elasticsearch(
        esHost,
        api_key=apiKey,
        verify_certs=True
    )
    
    # Define the document body
    document = {
        "text": text
    }
    
    # Index the document into Elasticsearch
    response = es.index(index=indexName, document=document)
    print(f"Data ingested successfully: {response}")
    del es

# Example usage:

def insertData(data):
    apiKey = os.getenv("elasticcloud")
    keyId = "ingester"
    endpoint = "https://071730c04c944f729330b0129af38419.us-central1.gcp.cloud.es.io:443"
    indexName = "dc-index"#"dc-ecinf-index"#"nist-index"
    ingestData(
        indexName=indexName,
        text=data,
        esHost=endpoint,
        apiKey=apiKey
    )
#NIST.SP.800-12r1.pdf__page_number__5


def extractTextFromPdfPage(file_path):
    text = ""
    fileName = os.path.basename(file_path)
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = {"fileName":fileName, "pageNumber":page.page_number, "content":page.extract_text()}
            try:
                insertData(json.dumps(text))
            except Exception as e:
                return False
            print(f"file {fileName} Page number: {page.page_number} --done")
    return True


def fileScanned(file):
    isComplete = False
    with open("state.txt",'r') as f:
        if file in f.read():
            isComplete = True
        else:
            isComplete = False
    return isComplete

def ingestList(files):
    print("New worker created")
    failedRequests = []
    notComplete = False
    for file in files:
        sizes = extract_headings(os.path.join("full_pdf_dataset",file))
        input(sizes)
        if fileScanned(file):
            print(f"File is alredy uploded {file}")
            continue 
        print(file)
        state = extractTextFromPdfPage(os.path.join("full_pdf_dataset",file))
        if state:
            print(f"data inserted{file}")
            with open('state.txt','a') as f:
                f.write(f"\n{file}--done")
        else:
            notComplete = True
            failedRequests.append(file)
            print(f"The file was not sucessfull{file}--------------------")
    while notComplete:
        files = failedRequests
        for file in files:
            state = extractTextFromPdfPage(os.path.join("full_pdf_dataset",file))
            if state:
                failedRequests.remove(file)
                print(f"data inserted{file}")
                with open('state.txt','a') as f:
                    f.write(f"\n{file}--done")
            else:
                print(f"The file{file} failed to insert again")
        if len(failedRequests) <=0:
            notComplete = False
        

def splitList(input_list, n):
    chunk_size = len(input_list) // n
    remainder = len(input_list) % n
    
    splits = []
    start = 0
    for i in range(n):
        end = start + chunk_size + (1 if remainder > 0 else 0)
        splits.append(input_list[start:end])
        start = end
        remainder -= 1  # Decrease remainder as we adjust chunks

    return splits


def getSize(data):
    for page in data.pages:
        # Extract text with character-level information
        words = page.extract_text_lines(extra_attrs=['fontname','size'])
        sizes = {}
        wordCount = 0
        
        for word in words:
            wordCount+= len(word.get("text"))
            font = word.get('chars')[0].get("fontname")
            size = word.get('chars')[0].get("size")
            text = word.get('text')
            sizes[size]=sizes.get(size,0)+1
        text = max(sizes)
        sizes.pop(text)
        heading = max(sizes)
        print(f"Words: {wordCount}, Text: {text}, Heading: {heading}")

def extract_headings(pdf_path):
    headings = []
    
    # Open the PDF file
    with pdfplumber.open(pdf_path) as pdf:
        getSize(pdf)
        for page in pdf.pages:
            # Extract text with character-level information
            words = page.extract_text_lines(extra_attrs=['fontname','size'])
            
            for word in words:
                font = word.get('chars')[0].get("fontname")
                size = word.get('chars')[0].get("size")
                text = word.get('text')
                input(f"text: {text}, Font: {font}")
                # Adjust the font size threshold based on your document
                # Typically, headings have larger font sizes
                #if word['fontname'] in ("font_name_of_headings") and float(word['size']) > 10:  
                 #   headings.append(word['text'])
    
    return headings

def main():
    files = os.listdir("full_pdf_dataset")
    ingestList([files[1]])
    n = int(len(files)*.05)
    print(f"total process: {n}")
    processes = []
    for i in splitList(files, n):
        p = Process(target=ingestList, args=(i,))  # Pass each argument to the function
        p.start()  # Start the process
        processes.append(p)
    for p in processes:
        p.join()  # 




#--------------------------RUN CHECKER---------------------------------
if __name__=="__main__":
    main()
