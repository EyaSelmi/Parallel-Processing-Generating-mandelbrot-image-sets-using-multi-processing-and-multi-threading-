import sys
import math
import multiprocessing
import threading
import logging
import psutil
import time
from PIL import Image
from tabulate import tabulate

def iteration_to_color(i, max_iter):
    if i == max_iter:
        return (0, 0, 0)
    hue = int(255 * i / max_iter)
    return (hue, hue, 255)

def iterations_at_point(x, y, max_iter):
    i = 0
    cx, cy = x, y
    while i < max_iter:
        if x*x + y*y > 4.0:
            break
        x, y = x*x - y*y + cx, 2*x*y + cy
        i += 1
    return i

def compute_chunk(start_row, end_row, xcenter, ycenter, scale, image_width, image_height, max_iter, queue):
    xmin = xcenter - scale
    xmax = xcenter + scale
    ymin = ycenter - scale
    ymax = ycenter + scale
    chunk_data = []
    for py in range(start_row, end_row):
        row = []
        y = ymin + (ymax - ymin) * py / (image_height - 1)
        for px in range(image_width):
            x = xmin + (xmax - xmin) * px / (image_width - 1)
            i = iterations_at_point(x, y, max_iter)
            row.append(iteration_to_color(i, max_iter))
        chunk_data.append((py, row))
    queue.put(chunk_data)

def process_wrapper(i, start_row, end_row, xcenter, ycenter, scale, image_width, image_height, max_iter, queue, process_times, process_summary):
    proc_start = time.time()
    compute_chunk(start_row, end_row, xcenter, ycenter, scale, image_width, image_height, max_iter, queue)
    proc_end = time.time()
    process_times.append((i, start_row, end_row, proc_end - proc_start))
    process_summary.append({'Process': i, 'Start Row': start_row, 'End Row': end_row, 'Time (s)': f"{proc_end - proc_start:.2f}"})

def multiprocessing_mandelbrot(filename, xcenter, ycenter, scale, image_width, image_height, max_iter, nproc):
    img = Image.new("RGB", (image_width, image_height))
    queue = multiprocessing.Queue()
    rows_per_proc = image_height // nproc
    processes = []
    manager = multiprocessing.Manager()
    process_times = manager.list()
    process_summary = manager.list()
    for i in range(nproc):
        start_row = i * rows_per_proc
        end_row = image_height if i == nproc - 1 else (i + 1) * rows_per_proc
        p = multiprocessing.Process(target=process_wrapper, args=(i, start_row, end_row, xcenter, ycenter, scale, image_width, image_height, max_iter, queue, process_times, process_summary))
        processes.append(p)
        logging.info(f"Process {i} started for rows {start_row} to {end_row}")
        p.start()
    for _ in range(nproc):
        chunk_data = queue.get()
        for py, row in chunk_data:
            for px, color in enumerate(row):
                img.putpixel((px, py), color)
    for p in processes:
        p.join()
    img.save(filename)
    logging.info(f"Saved {filename}")
    return list(process_summary)

def compute_chunk_thread(start_row, end_row, xcenter, ycenter, scale, image_width, image_height, max_iter, result_list, img, semaphore):
    xmin = xcenter - scale
    xmax = xcenter + scale
    ymin = ycenter - scale
    ymax = ycenter + scale
    chunk_data = []
    for py in range(start_row, end_row):
        row = []
        y = ymin + (ymax - ymin) * py / (image_height - 1)
        for px in range(image_width):
            x = xmin + (xmax - xmin) * px / (image_width - 1)
            i = iterations_at_point(x, y, max_iter)
            row.append(iteration_to_color(i, max_iter))
        chunk_data.append((py, row))
    # Synchronize writing to the image buffer
    semaphore.acquire()
    try:
        for py, row in chunk_data:
            for px, color in enumerate(row):
                img.putpixel((px, py), color)
    finally:
        semaphore.release()
    result_list.append(chunk_data)

def multithreading_mandelbrot(filename, xcenter, ycenter, scale, image_width, image_height, max_iter, nthreads):
    img = Image.new("RGB", (image_width, image_height))
    rows_per_thread = image_height // nthreads
    threads = []
    results = []
    semaphore = threading.Semaphore(1)
    for i in range(nthreads):
        start_row = i * rows_per_thread
        end_row = image_height if i == nthreads - 1 else (i + 1) * rows_per_thread
        t = threading.Thread(target=compute_chunk_thread, args=(start_row, end_row, xcenter, ycenter, scale, image_width, image_height, max_iter, results, img, semaphore))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    img.save(filename)
    print(f"Saved {filename}")

def main():
    if len(sys.argv) <= 2:
        print("\nUsage: python mandelseries.py <n> <mode>\n<mode>: mp for multiprocessing, mt for multithreading\n")
        sys.exit(1)
    n = int(sys.argv[1])
    mode = sys.argv[2]
    xcenter = 0.265000
    ycenter = 0.003500
    scale = 2
    image_width = 500
    image_height = 500
    max_iter = 1000
    import time
    if mode == 'mp':
        filename = "mandelbrot_mp.png"
        start = time.time()
        process_summary = multiprocessing_mandelbrot(filename, xcenter, ycenter, scale, image_width, image_height, max_iter, n)
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
    elif mode == 'mt':
        filename = "mandelbrot_mt.png"
        start = time.time()
        multithreading_mandelbrot(filename, xcenter, ycenter, scale, image_width, image_height, max_iter, n)
        end = time.time()
        logging.info(f"Multithreading execution time: {end - start:.2f} seconds")
    else:
        print("Invalid mode. Use 'mp' for multiprocessing or 'mt' for multithreading.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
    logging.info("Program started.")
    program_start = time.time()
    try:
        xcenter = 0
        ycenter = 0
        scale = 4
        image_width = 800
        image_height = 600
        max_iter = 1000
        nproc = 4
        logging.info("Running multiprocessing Mandelbrot...")
        start = time.time()
        process_summary = multiprocessing_mandelbrot("mandelbrot_mp.png", xcenter, ycenter, scale, image_width, image_height, max_iter, nproc)
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
