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
    
    try:
        # Index the document into Elasticsearch
        response = es.index(index=indexName, document=document)
        print(f"Data ingested successfully: {response}")
    except Exception as e:
        print(f"Failed to ingest data: {e}")

# Example usage:

def insertData(data):
    apiKey = os.getenv("elasticcloud")
    keyId = "ingester"
    endpoint = "https://071730c04c944f729330b0129af38419.us-central1.gcp.cloud.es.io:443"
    indexName = "nist-index"
    ingestData(
        indexName=indexName,
        text=f"{data}",
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
    return json.dumps(text)


def ingestList(files):
    print("New worker created")
    for file in files:
        data = extractTextFromPdfPage(os.path.join("full_pdf_dataset",file))
        insertData(data)
        print(f"data inserted{file}")
        with open('state.txt','a') as f:
            f.write(f"\n{file}--done")
        

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


def main():
    files = os.listdir("full_pdf_dataset")
    n = int(len(files)*.10)
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
