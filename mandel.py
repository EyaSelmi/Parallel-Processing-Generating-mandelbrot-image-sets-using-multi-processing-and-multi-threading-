import argparse
import threading
from PIL import Image
import time
import logging
import psutil
from tabulate import tabulate

def iteration_to_color(i, max_iter):
    gray = int(255 * i / max_iter)
    return (gray, gray, gray)

def iterations_at_point(x, y, max_iter):
    x0, y0 = x, y
    iter = 0
    while (x*x + y*y <= 4) and (iter < max_iter):
        xt = x*x - y*y + x0
        yt = 2*x*y + y0
        x, y = xt, yt
        iter += 1
    return iter

def compute_image(args):
    img, xmin, xmax, ymin, ymax, max_iter, start_row, end_row, summary = args
    start = time.time()
    width, height = img.size
    for j in range(start_row, end_row):
        for i in range(width):
            x = xmin + i * (xmax - xmin) / width
            y = ymin + j * (ymax - ymin) / height
            iters = iterations_at_point(x, y, max_iter)
            color = iteration_to_color(iters, max_iter)
            img.putpixel((i, j), color)
    elapsed = time.time() - start
    summary.append({'Fractal': f'Rows {start_row}-{end_row-1}', 'Time (s)': f'{elapsed:.3f}', 'Status': 'Completed'})

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
    parser = argparse.ArgumentParser(description='Generate Mandelbrot set image (sequential).')
    parser.add_argument('-m', type=int, default=1000, help='Max iterations per point')
    parser.add_argument('-x', type=float, default=0, help='X center')
    parser.add_argument('-y', type=float, default=0, help='Y center')
    parser.add_argument('-s', type=float, default=4, help='Scale')
    parser.add_argument('-W', type=int, default=500, help='Image width')
    parser.add_argument('-H', type=int, default=500, help='Image height')
    parser.add_argument('-o', type=str, default='mandel.png', help='Output file')
    args = parser.parse_args()

    logging.info('Program started.')
    img = Image.new('RGB', (args.W, args.H))
    summary = []
    start_time = time.time()
    error_occurred = False
    try:
        compute_image((img, args.x - args.s, args.x + args.s, args.y - args.s, args.y + args.s, args.m, 0, args.H, summary))
        img.save(args.o)
        logging.info(f'Saved image to {args.o}')
    except Exception as e:
        error_occurred = True
        logging.error(f'Error occurred: {e}')
    elapsed = time.time() - start_time
    print('\nSummary:')
    print(tabulate(summary, headers='keys', tablefmt='grid'))
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=1)
    print(f'\nSystem Memory: {mem.percent}% used, {mem.available // (1024*1024)} MB available')
    print(f'CPU Usage: {cpu}%')
    if error_occurred:
        logging.info(f'Program completed with errors. Total execution time: {elapsed:.3f} seconds')
    else:
        logging.info(f'Program completed successfully. Total execution time: {elapsed:.3f} seconds')

if __name__ == "__main__":
    main()
