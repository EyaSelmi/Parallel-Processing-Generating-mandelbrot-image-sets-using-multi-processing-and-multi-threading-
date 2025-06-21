# mandelseries_sync.py
# Synchronized Mandelbrot computation using Producer/Consumer (threading & multiprocessing)

import threading
import multiprocessing
from queue import Queue
from PIL import Image
from mandel import iterations_at_point, iteration_to_color
import time
import logging
import psutil
from tabulate import tabulate

# Producer function for threading

def compute_chunk_thread_producer(start_row, end_row, xcenter, ycenter, scale, image_width, image_height, max_iter, queue):
    xmin = xcenter - scale
    xmax = xcenter + scale
    ymin = ycenter - scale
    ymax = ycenter + scale
    for py in range(start_row, end_row):
        y = ymin + (ymax - ymin) * py / (image_height - 1)
        row = []
        for px in range(image_width):
            x = xmin + (xmax - xmin) * px / (image_width - 1)
            i = iterations_at_point(x, y, max_iter)
            row.append(iteration_to_color(i, max_iter))
        queue.put((py, row))
    queue.put(None)  # Signal end of production

# Consumer function for threading

def write_image_thread_consumer(img, queue, num_producers):
    finished = 0
    while finished < num_producers:
        item = queue.get()
        if item is None:
            finished += 1
            continue
        py, row = item
        for px, color in enumerate(row):
            img.putpixel((px, py), color)

# Producer function for multiprocessing

def compute_chunk_process_producer(start_row, end_row, xcenter, ycenter, scale, image_width, image_height, max_iter, queue):
    xmin = xcenter - scale
    xmax = xcenter + scale
    ymin = ycenter - scale
    ymax = ycenter + scale
    for py in range(start_row, end_row):
        y = ymin + (ymax - ymin) * py / (image_height - 1)
        row = []
        for px in range(image_width):
            x = xmin + (xmax - xmin) * px / (image_width - 1)
            i = iterations_at_point(x, y, max_iter)
            row.append(iteration_to_color(i, max_iter))
        queue.put((py, row))
    queue.put(None)

# Consumer function for multiprocessing

def write_image_process_consumer(img, queue, num_producers):
    finished = 0
    while finished < num_producers:
        item = queue.get()
        if item is None:
            finished += 1
            continue
        py, row = item
        for px, color in enumerate(row):
            img.putpixel((px, py), color)

# Example usage for threading

def mandelbrot_threaded_sync(xcenter, ycenter, scale, image_width, image_height, max_iter, num_threads, filename):
    img = Image.new('RGB', (image_width, image_height))
    queue = Queue()
    threads = []
    rows_per_thread = image_height // num_threads
    for i in range(num_threads):
        start_row = i * rows_per_thread
        end_row = (i + 1) * rows_per_thread if i < num_threads - 1 else image_height
        t = threading.Thread(target=compute_chunk_thread_producer, args=(start_row, end_row, xcenter, ycenter, scale, image_width, image_height, max_iter, queue))
        threads.append(t)
        t.start()
    consumer = threading.Thread(target=write_image_thread_consumer, args=(img, queue, num_threads))
    consumer.start()
    for t in threads:
        t.join()
    consumer.join()
    img.save(filename)
    print(f"Saved {filename}")

# Example usage for multiprocessing

def process_wrapper(i, start_row, end_row, xcenter, ycenter, scale, image_width, image_height, max_iter, queue, process_times, process_summary):
    proc_start = time.time()
    compute_chunk_process_producer(start_row, end_row, xcenter, ycenter, scale, image_width, image_height, max_iter, queue)
    proc_end = time.time()
    process_times.append((i, start_row, end_row, proc_end - proc_start))
    process_summary.append({'Process': i, 'Start Row': start_row, 'End Row': end_row, 'Time (s)': f"{proc_end - proc_start:.2f}"})

def mandelbrot_process_sync(xcenter, ycenter, scale, image_width, image_height, max_iter, num_processes, filename):
    img = Image.new('RGB', (image_width, image_height))
    queue = multiprocessing.Queue()
    processes = []
    rows_per_process = image_height // num_processes
    process_times = multiprocessing.Manager().list()
    process_summary = multiprocessing.Manager().list()
    for i in range(num_processes):
        start_row = i * rows_per_process
        end_row = (i + 1) * rows_per_process if i < num_processes - 1 else image_height
        p = multiprocessing.Process(target=process_wrapper, args=(i, start_row, end_row, xcenter, ycenter, scale, image_width, image_height, max_iter, queue, process_times, process_summary))
        processes.append(p)
        logging.info(f"Process {i} started for rows {start_row} to {end_row}")
        p.start()
    consumer = threading.Thread(target=write_image_process_consumer, args=(img, queue, num_processes))
    consumer.start()
    for p in processes:
        p.join()
    consumer.join()
    img.save(filename)
    logging.info(f"Saved {filename}")
    return list(process_summary)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
    logging.info("Program started.")
    program_start = time.time()
    try:
        xcenter = -0.5
        ycenter = 0.0
        scale = 1.5
        image_width = 800
        image_height = 600
        max_iter = 100
        num_threads = 4
        num_processes = 4

        logging.info("Running threaded Mandelbrot with synchronization...")
        start = time.time()
        mandelbrot_threaded_sync(xcenter, ycenter, scale, image_width, image_height, max_iter, num_threads, "mandelbrot_threaded_sync.png")
        end = time.time()
        logging.info(f"Threaded execution time: {end - start:.2f} seconds")

        logging.info("Running multiprocessing Mandelbrot with synchronization...")
        start = time.time()
        process_summary = mandelbrot_process_sync(xcenter, ycenter, scale, image_width, image_height, max_iter, num_processes, "mandelbrot_process_sync.png")
        end = time.time()
        logging.info(f"Multiprocessing execution time: {end - start:.2f} seconds")

        # Display summary table
        print("\nProcess Summary Table:")
        print(tabulate(process_summary, headers="keys", tablefmt="grid"))

        # System stats
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=1)
        print(f"\nSystem Memory: {mem.percent}% used, {mem.available // (1024*1024)} MB available")
        print(f"CPU Usage: {cpu}%")

        program_end = time.time()
        logging.info(f"Program completed successfully in {program_end - program_start:.2f} seconds.")
    except Exception as e:
        program_end = time.time()
        logging.error(f"Program completed with errors in {program_end - program_start:.2f} seconds. Error: {e}")
