from datetime import datetime
import json
import argparse
from elasticsearch import Elasticsearch
from tqdm import tqdm
import time
import es_query
import pandas as pd
import random
import logging
import os
import multiprocessing as mp
ES_HOST = "https://vpc-gamechanger-iquxkyq2dobz4antllp35g2vby.us-east-1.es.amazonaws.com"
INDEX = "gamechanger"
MAX_CYCLE = 100
NUM_JOBS = 5

search_df = pd.read_csv("../data/SearchPdfMapping.csv")
search_df.search.str.replace("&quot;", "", regex=True)
search_df.search.str.replace("/", "", regex=True)
search_data = search_df.search.unique()

class StressTest():
    def __init__(self,):
        self.es = Elasticsearch([ES_HOST], max_size=100)

    def check_health(self,es):
        health = es.cluster.health()
        if health['status'] != "green":
            print("CLUSTER HEALTH NOT GREEN")
            return False
        return True
    def run_test(self, query_type):
        cycle_start_time = time.time()
        num_complete = 0
        cpu_list = []
        for cycle in tqdm(range(0,MAX_CYCLE)):
            query = es_query.query(random.choice(search_data),query_type)
            start_time = time.time()
            res = self.es.search(index= INDEX, body = query)
            if res:
                num_complete += 1
            stats = self.es.nodes.stats()
            nodes = list(stats['nodes'].keys())
            total_cpu = 0
            for i in nodes:
                process = stats['nodes'][i]['process']
                cpu_percent = process['cpu']['percent']
                total_cpu += cpu_percent
            # print("Total CPU usage: %s" % total_cpu)
            # print("--- search took %s seconds ---" % (time.time() - start_time))
            cpu_list.append(total_cpu)
            if not self.check_health(self.es):
                break
        max_cpu = max(cpu_list)
        name = mp.current_process().name
        print("Process Name: ", name)
        print(f"Max CPU: %s" % max_cpu)
        print("Num of results complete: %s" % num_complete)
        print("--- Full Cycle: %s seconds ---" % (time.time() - cycle_start_time))
    def write_stats(self):
        with open(f"stats_{round(time.time())}.json", 'w') as f:
            json.dump(self.es.nodes.stats(),f)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="ES Stress Testing")
    parser.add_argument(
        "--jobs",
        "-j",
        dest="num_jobs",
        default=NUM_JOBS,
        type=int,
        help="number of jobs to run",
    )
    parser.add_argument(
        "--cycles",
        "-c",
        dest="cycles",
        default=MAX_CYCLE,
        type=int,
        help="number of requests each job makes",
    )

    parser.add_argument(
        "--host",
        "-es",
        dest="es_host",
        default=ES_HOST,
        type=str,
        help="elasticsearch host",
    )

    args = parser.parse_args()
    
    tester = StressTest()
    jobs = []
    MAX_CYCLE = args.cycles
    for process in range(args.num_jobs):
        p1 = mp.Process(target=tester.run_test, args=('no_aggs',))
        p1.name = "P1"
        jobs.append(p1)
        p1.start()
        p2 = mp.Process(target=tester.run_test, args=(None,))
        p2.name = "P2"
        jobs.append(p2)
        p2.start()
        p3 = mp.Process(target=tester.run_test, args=('no_highlight',))
        p3.name = "P3"
        jobs.append(p3)
        p3.start()

    tester.write_stats()
