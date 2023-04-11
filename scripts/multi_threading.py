import os
from scripts import user_input
from dotenv import load_dotenv, set_key
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from tqdm import tqdm
from scripts import misc


load_dotenv()

def multi_thread_test(func, *args):
    permission = user_input.user_input(f"Optimal thread count for load unknown. Test?", bool)
    if permission:
        num_cores = os.cpu_count() or 4
        print(f"Number of tests: {num_cores*2}")
        lowest_time = 99999
        fastest_thread_speed = num_cores
        for i in range(num_cores*2):
            print(f"Testing {i+1} threads.")
            modified_args = list(args)
            modified_args[0] = i+1
            start_time = time.time()
            func(*modified_args)
            end_time = time.time()
            current_time = end_time - start_time
            if current_time < lowest_time:
                lowest_time = current_time
                fastest_thread_speed = i+1
            print(f"{i+1} had a speed of {current_time}")
        print(f"Fastest thread number: {fastest_thread_speed} with time of {lowest_time}")
        max_workers = fastest_thread_speed
        set_key(".env","load_threads",str(max_workers))
        return max_workers
    else:
        return 4