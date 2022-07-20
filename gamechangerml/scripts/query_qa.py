import requests
from os import listdir
from os.path import isfile, isdir, join
import argparse
import json
import time

def open_search_results(fpath):

    with open(fpath, "rb") as f:
        content = json.load(f)

    return content

def format_search_context(search_results, context_type = 'all'):

    regular_context = [{"text": i['pageHits'][0]['snippet'].replace('<em>|</em>', ''), "source": i['display_title_s'], "type": "regular"} for i in search_results['saveResults']['regular']]
    qa_context = [{"text": i['text'], "source": i['filename'], "type": "qa_context"} for i in search_results['saveResults']['context']]

    if context_type == 'all':
        context = dict(zip(range(len(regular_context) + len(qa_context)), qa_context + regular_context))
    elif context_type == 'qa_only':
        context = dict(zip(range(len(qa_context)), qa_context))

    return context

def label_results(context, results):

    for i in results:
        index = i['context']
        i['filename'] = context[index]['source']
        i['source'] = context[index]['type']
    results = [i for i in results if i['text'] != '']

    return results

class QAResponse():

    def __init__(self, fpath, context_type):

        self.fpath = fpath
        self.context_type = context_type
        self.query, self.context, self.simple_context = self.parse_search_results()
        self.answers, self.time = self.send_qa()

    def parse_search_results(self):

        content = open_search_results(self.fpath)
        query = content['query']
        context = format_search_context(content, self.context_type)
        simple_context = [context[i]['text'] for i in context.keys()]

        return query, context, simple_context

    def send_qa(self):
    
        start = time.perf_counter()

        post = {
            "query": self.query,
            "search_context": self.simple_context
        }
        
        data = json.dumps(post).encode("utf-8")
        url = 'http://localhost:5000/questionAnswer'
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, data = data, headers = headers)

        end = time.perf_counter()

        took = f"{end-start:0.4f} seconds"

        results = response.json()['answers']

        labeled_results = label_results(self.context, results)

        return labeled_results, took


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Query QA Model")

    parser.add_argument(
        "--directory",
        "-d",
        dest="directory",
        type=str,
        help="path to directory with context files (also where qa_results.csv is saved)",
    )

    parser.add_argument(
        "--context_type",
        "-c",
        dest="context_type",
        type=str,
        help="what kind of results to use for context (options: ['all', 'qa_only'])",
    )

    args = parser.parse_args()

    onlyfiles = [join(args.directory, f) for f in listdir(args.directory) if isfile(join(args.directory, f))]
    results_csv = open(join(args.directory, "qa_results.csv"), "w")
    results_csv.write("question,answer,score,prob,filename,context_rank,answer_rank,source")
    for file in onlyfiles:
        try:
            qa_response = QAResponse(file, args.context_type)
            count = 0
            for answer in qa_response.answers:
                results = [
                    qa_response.query,
                    answer['text'].replace(',', ''),
                    answer['null_score_diff'],
                    answer['probability'],
                    answer['filename'].replace(',', ''),
                    answer['context'],
                    count,
                    answer['source']
                ]
                results = [str(i) for i in results]

                row = "\n" + ",".join(results)
                results_csv.write(row)
                count += 1
        except:
        	   print(f"Error with {file}")

