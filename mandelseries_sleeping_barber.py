# mandelseries_sleeping_barber.py
# Mandelbrot computation using Sleeping Barber synchronization pattern (threading)

import threading
import multiprocessing
from queue import Queue
from PIL import Image
from mandel import iterations_at_point, iteration_to_color
import time
import logging
import psutil
from tabulate import tabulate

# Correct Sleeping Barber synchronization using a bounded queue and threading.Condition

class SleepingBarberQueue:
    def __init__(self, maxsize):
        self.queue = []
        self.maxsize = maxsize
        self.lock = threading.Lock()
        self.not_empty = threading.Condition(self.lock)
        self.not_full = threading.Condition(self.lock)
    def put(self, item):
        with self.not_full:
            while len(self.queue) >= self.maxsize:
                self.not_full.wait()
            self.queue.append(item)
            self.not_empty.notify()
    def get(self):
        with self.not_empty:
            while not self.queue:
                self.not_empty.wait()
            item = self.queue.pop(0)
            self.not_full.notify()
            return item

def compute_chunk_sleeping_barber(start_row, end_row, xcenter, ycenter, scale, image_width, image_height, max_iter, sb_queue, summary_list, thread_id):
    chunk_start = time.time()
    for py in range(start_row, end_row):
        y = ycenter - scale + (2 * scale) * py / (image_height - 1)
        row = []
        for px in range(image_width):
            x = xcenter - scale + (2 * scale) * px / (image_width - 1)
            i = iterations_at_point(x, y, max_iter)
            row.append(iteration_to_color(i, max_iter))
        sb_queue.put((py, row))
    chunk_end = time.time()
    summary_list.append({'Thread': thread_id, 'Start Row': start_row, 'End Row': end_row, 'Time (s)': f"{chunk_end - chunk_start:.2f}"})
    sb_queue.put(None)

def write_image_sleeping_barber(img, sb_queue, num_producers):
    finished = 0
    while finished < num_producers:
        item = sb_queue.get()
        if item is None:
            finished += 1
            continue
        py, row = item
        for px, color in enumerate(row):
            img.putpixel((px, py), color)

def mandelbrot_sleeping_barber_sync(xcenter, ycenter, scale, image_width, image_height, max_iter, num_threads, filename):
    img = Image.new('RGB', (image_width, image_height))
    sb_queue = SleepingBarberQueue(maxsize=16)  # waiting room size
    threads = []
    rows_per_thread = image_height // num_threads
    summary_list = []
    for i in range(num_threads):
        start_row = i * rows_per_thread
        end_row = (i + 1) * rows_per_thread if i < num_threads - 1 else image_height
        t = threading.Thread(target=compute_chunk_sleeping_barber, args=(start_row, end_row, xcenter, ycenter, scale, image_width, image_height, max_iter, sb_queue, summary_list, i))
        threads.append(t)
        t.start()
    consumer = threading.Thread(target=write_image_sleeping_barber, args=(img, sb_queue, num_threads))
    consumer.start()
    for t in threads:
        t.join()
    consumer.join()
    img.save(filename)
    return summary_list

def process_wrapper(i, start_row, end_row, xcenter, ycenter, scale, image_width, image_height, max_iter, queue, process_times, process_summary):
    proc_start = time.time()
    compute_chunk_sleeping_barber(start_row, end_row, xcenter, ycenter, scale, image_width, image_height, max_iter, queue, process_summary, i)
    proc_end = time.time()
    process_times.append((i, start_row, end_row, proc_end - proc_start))
    # process_summary is already appended in compute_chunk_sleeping_barber

def mandelbrot_process_sleeping_barber_sync(xcenter, ycenter, scale, image_width, image_height, max_iter, num_processes, filename):
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
    consumer = threading.Thread(target=write_image_sleeping_barber, args=(img, queue, num_processes))
    consumer.start()
    for p in processes:
        p.join()
    consumer.join()
    img.save(filename)
    logging.info(f"Saved {filename}")
    return list(process_summary)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
    logging.info("Program started (Sleeping Barber version).")
    program_start = time.time()
    try:
        xcenter = 0
        ycenter = 0
        scale = 4
        image_width = 800
        image_height = 600
        max_iter = 1000
        num_threads = 4
        num_processes = 4

        logging.info("Running threaded Mandelbrot with Sleeping Barber synchronization...")
        start = time.time()
        thread_summary = mandelbrot_sleeping_barber_sync(xcenter, ycenter, scale, image_width, image_height, max_iter, num_threads, "mandelbrot_sleeping_barber_sync.png")
        end = time.time()
        logging.info(f"Threaded execution time: {end - start:.2f} seconds")

        print("\nThread Summary Table:")
        print(tabulate(thread_summary, headers="keys", tablefmt="grid"))

        logging.info("Running multiprocessing Mandelbrot with Sleeping Barber synchronization...")
        start = time.time()
        process_summary = mandelbrot_process_sleeping_barber_sync(xcenter, ycenter, scale, image_width, image_height, max_iter, num_processes, "mandelbrot_process_sleeping_barber_sync.png")
        end = time.time()
        logging.info(f"Multiprocessing execution time: {end - start:.2f} seconds")

        print("\nProcess Summary Table:")
        print(tabulate(process_summary, headers="keys", tablefmt="grid"))

        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=1)
        print(f"\nSystem Memory: {mem.percent}% used, {mem.available // (1024*1024)} MB available")
        print(f"CPU Usage: {cpu}%")

        program_end = time.time()
        logging.info(f"Program completed successfully in {program_end - program_start:.2f} seconds.")
    except Exception as e:
        program_end = time.time()
        logging.error(f"Program completed with errors in {program_end - program_start:.2f} seconds. Error: {e}")
