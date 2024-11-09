import os
import pdfplumber
import json
from multiprocessing import Process, cpu_count
from elasticsearch import Elasticsearch

def ingestData(es, indexName, text):
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

def extractTextFromPdfPage(file_path):
    fileName = os.path.basename(file_path)
    pages = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            pages.append({"fileName": fileName, "pageNumber": page.page_number, "content": page.extract_text()})
    return json.dumps(pages)

def ingestList(files, indexName, esHost, apiKey):
    print("New worker created")
    # Initialize Elasticsearch client in the process
    es = Elasticsearch(
        esHost,
        api_key=apiKey,
        verify_certs=True
    )
    
    for file in files:
        data = extractTextFromPdfPage(os.path.join("full_pdf_dataset", file))
        ingestData(es, indexName, data)
        print(f"data inserted {file}")
    del es
        
    # Write completed files at once to reduce file I/O
    with open('state.txt', 'a') as f:
        f.write("\n".join([f"{file}--done" for file in files]) + "\n")

def splitList(input_list, n):
    chunk_size = len(input_list) // n
    remainder = len(input_list) % n
    
    splits = []
    start = 0
    for i in range(n):
        end = start + chunk_size + (1 if remainder > 0 else 0)
        splits.append(input_list[start:end])
        start = end
        remainder -= 1

    return splits

def main():
    files = os.listdir("full_pdf_dataset")
    num_processes = min(cpu_count(), len(files) // 10)  # Limit to number of CPU cores or fraction of files
    print(f"Total processes: {num_processes}")

    apiKey = os.getenv("elasticcloud")
    esHost = "https://071730c04c944f729330b0129af38419.us-central1.gcp.cloud.es.io:443"
    indexName = "nist-index"
    
    # Split files and create processes
    processes = []
    for chunk in splitList(files, num_processes):
        # Pass only simple data types and strings to the new process
        p = Process(target=ingestList, args=(chunk, indexName, esHost, apiKey))
        p.start()
        processes.append(p)
        
    for p in processes:
        p.join()

if __name__ == "__main__":
    main()

