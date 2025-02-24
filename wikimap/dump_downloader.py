import os
import requests
from concurrent.futures import ThreadPoolExecutor
from bz2 import BZ2File
import time
from os import path
from tqdm import tqdm


class DumpDownloader:
    def __init__(self, url, num_threads=-1):
        self.url = url
        self.num_threads = num_threads
        # automatically set the number of threads based on the number of cores available
        if self.num_threads == -1:
            self.num_threads = os.cpu_count()
            print("Number of threads not specified. Using the number of cores available: ", self.num_threads)

    def singleThreadDownload(self, output_path):
        r = requests.get(self.url, stream=True)
        total_size = int(r.headers.get('content-length', 0))
        chunk_size = 1024

        print(f"Starting download from {self.url}")
        start_time = time.time()

        with open(output_path, 'wb') as f:
            for chunk in tqdm(r.iter_content(chunk_size), total=total_size // chunk_size, unit='KB', desc=output_path):
                if chunk:
                    f.write(chunk)

        elapsed_time = time.time() - start_time
        print(f"\nDownload completed in {elapsed_time:.2f} seconds")

    def download(self, output_path):
        # Get file size
        r = requests.head(self.url)
        total_size = int(r.headers.get('content-length', 0))
        if total_size == 0:
            raise ValueError("Unable to retrieve the file size.")
        
        # Ensure chunk sizes are precise
        chunk_size = (total_size + self.num_threads - 1) // self.num_threads  # Divide fairly
        
        # Create temporary files for each thread
        temp_files = [f"{output_path}.part{i}" for i in range(self.num_threads)]
        
        # Function for downloading a part of the file
        def download_part(start, end, temp_file, thread_index):
            headers = {"Range": f"bytes={start}-{end}"}
            max_retries = 5  # Limit retries to avoid infinite loops
            retry_delay = 1  # Default retry delay in seconds
            
            for attempt in range(max_retries):
                try:
                    response = requests.get(self.url, headers=headers, stream=True, timeout=10)
                    
                    # Check if the server responded with a retryable status code
                    if response.status_code == 503:
                        retry_after = response.headers.get("Retry-After")
                        retry_delay = int(retry_after) if retry_after else retry_delay
                        print(f"Thread {thread_index + 1} received 503. Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        continue
                    
                    response.raise_for_status()
                    
                    # Write the content to a temporary file
                    with open(temp_file, 'wb') as f, tqdm(
                        total=(end - start + 1) // 1024,
                        unit='KB',
                        desc=f"Thread {thread_index + 1}",
                        position=thread_index
                    ) as pbar:
                        for chunk in response.iter_content(1024):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk) // 1024)
                    return  # Exit after successful download
                
                except requests.exceptions.RequestException as e:
                    print(f"Thread {thread_index + 1} encountered an error: {e}")
                    if attempt < max_retries - 1:
                        print(f"Retrying in {retry_delay} seconds... (Attempt {attempt + 2}/{max_retries})")
                        time.sleep(retry_delay)
                    else:
                        print(f"Thread {thread_index + 1} failed after {max_retries} attempts.")
                        raise
        
        # Start downloading parts using threads
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = []
            for i in range(self.num_threads):
                start = i * chunk_size
                end = min(start + chunk_size - 1, total_size - 1)  # Avoid overshooting
                futures.append(executor.submit(download_part, start, end, temp_files[i], i))
            for future in futures:
                future.result()  # Ensure all threads complete
        
        # Combine parts into the final file
        with open(output_path, 'wb') as output_file:
            for temp_file in temp_files:
                with open(temp_file, 'rb') as part_file:
                    output_file.write(part_file.read())
                os.remove(temp_file)
        
        print(f"Download completed: {output_path}")

    def extract(self, output_path: str):
        decompressed_path = output_path.replace(".bz2", "")
        start_time = time.time()
        print(f"Extracting {output_path} to {decompressed_path}...")
        if not path.exists(output_path):
            print(f"File {output_path} does not exist.")
            return

        try:
            # .bz2 file extraction
            with BZ2File(output_path, 'rb') as file:
                content = file.read()
                with open(decompressed_path, 'wb') as decompressed_file:
                    decompressed_file.write(content)
            print(f"Extraction completed: {decompressed_path} in {time.time() - start_time:.2f} seconds")
        except OSError as e:
            print(f"Failed to extract {output_path}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while extracting {output_path}: {e}")
