# mandelseries_philosophers.py
# Mandelbrot computation using Dining Philosophers synchronization pattern

import threading
import multiprocessing
from queue import Queue
from PIL import Image
from mandel import iterations_at_point, iteration_to_color
import time
import logging
import psutil
from tabulate import tabulate

# Dining Philosophers synchronization using threading.Lock for forks

def philosopher_worker(philosopher_id, left_fork, right_fork, start_row, end_row, xcenter, ycenter, scale, image_width, image_height, max_iter, queue, summary_list):
    chunk_start = time.time()
    for py in range(start_row, end_row):
        # Philosopher tries to pick up left and right forks (locks)
        with left_fork:
            with right_fork:
                y = ycenter - scale + (2 * scale) * py / (image_height - 1)
                row = []
                for px in range(image_width):
                    x = xcenter - scale + (2 * scale) * px / (image_width - 1)
                    i = iterations_at_point(x, y, max_iter)
                    row.append(iteration_to_color(i, max_iter))
                queue.put((py, row))
    chunk_end = time.time()
    summary_list.append({'Philosopher': philosopher_id, 'Start Row': start_row, 'End Row': end_row, 'Time (s)': f"{chunk_end - chunk_start:.2f}"})
    queue.put(None)

# Consumer function (unchanged)
def write_image_consumer(img, queue, num_philosophers):
    finished = 0
    while finished < num_philosophers:
        item = queue.get()
        if item is None:
            finished += 1
            continue
        py, row = item
        for px, color in enumerate(row):
            img.putpixel((px, py), color)

def mandelbrot_philosophers_sync(xcenter, ycenter, scale, image_width, image_height, max_iter, num_philosophers, filename):
    img = Image.new('RGB', (image_width, image_height))
    queue = Queue()
    philosophers = []
    forks = [threading.Lock() for _ in range(num_philosophers)]
    rows_per_philosopher = image_height // num_philosophers
    summary_list = []
    for i in range(num_philosophers):
        start_row = i * rows_per_philosopher
        end_row = (i + 1) * rows_per_philosopher if i < num_philosophers - 1 else image_height
        left_fork = forks[i]
        right_fork = forks[(i + 1) % num_philosophers]
        # To avoid deadlock, last philosopher picks up right fork first
        if i == num_philosophers - 1:
            t = threading.Thread(target=philosopher_worker, args=(i, right_fork, left_fork, start_row, end_row, xcenter, ycenter, scale, image_width, image_height, max_iter, queue, summary_list))
        else:
            t = threading.Thread(target=philosopher_worker, args=(i, left_fork, right_fork, start_row, end_row, xcenter, ycenter, scale, image_width, image_height, max_iter, queue, summary_list))
        philosophers.append(t)
        t.start()
    consumer = threading.Thread(target=write_image_consumer, args=(img, queue, num_philosophers))
    consumer.start()
    for t in philosophers:
        t.join()
    consumer.join()
    img.save(filename)
    return summary_list

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
    logging.info("Program started (Dining Philosophers version).")
    program_start = time.time()
    try:
        xcenter = 0
        ycenter = 0
        scale = 4
        image_width = 800
        image_height = 600
        max_iter = 1000
        num_philosophers = 5

        logging.info("Running Mandelbrot with Dining Philosophers synchronization...")
        start = time.time()
        summary_list = mandelbrot_philosophers_sync(xcenter, ycenter, scale, image_width, image_height, max_iter, num_philosophers, "mandelbrot_philosophers_sync.png")
        end = time.time()
        logging.info(f"Dining Philosophers execution time: {end - start:.2f} seconds")

        # Display summary table
        print("\nPhilosopher Summary Table:")
        print(tabulate(summary_list, headers="keys", tablefmt="grid"))

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
