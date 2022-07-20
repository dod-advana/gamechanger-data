import threading
from datetime import datetime
from gamechangerml.api.utils.redisdriver import CacheVariable
from gamechangerml.api.fastapi.settings import logger
# Process Keys
clear_corpus = "corpus: corpus_download"
corpus_download = "corpus: corpus_download"
delete_corpus = "corpus: delete_corpus"
s3_file_download = "s3: file_download"
s3_dependency = "s3: all_dependency_download"
loading_corpus = "training: load_corpus"
loading_data = "training: load_data"
training = "training: train_model"
reloading = "models: reloading_models "
ltr_creation = "training: ltr_creation"
topics_creation = "models: topics_creation"

running_threads = {}

# the dictionary that holds all the progress values
try:
    PROCESS_STATUS = CacheVariable("process_status", True)
    COMPLETED_PROCESS = CacheVariable("completed_process", True)
    thread_lock = threading.Lock()
    default_flags = {
        corpus_download: False,
        clear_corpus: False,
        training: False,
        loading_corpus: False,
        reloading: False,
        ltr_creation: False,
        topics_creation: False,
        s3_file_download: False,
        s3_dependency: False,
        loading_data: False

    }

except Exception as e:
    print(e)

if PROCESS_STATUS.value == None:
    PROCESS_STATUS.value = {"flags": default_flags}
if COMPLETED_PROCESS.value == None:
    COMPLETED_PROCESS.value = []


def update_status(name, progress=0, total=100, message="", failed=False, thread_id="", completed_max=20):

    thread_id = str(thread_id)
    try:
        if progress == total or failed:
            date = datetime.now()
            date_string = date.strftime("%Y-%m-%d %H:%M:%S")
            completed = {
                "process": name,
                "total": total,
                "message": message,
                "date": date_string,
            }
            with thread_lock:
                if thread_id in PROCESS_STATUS.value:
                    temp = PROCESS_STATUS.value
                    temp.pop(thread_id, None)
                    if name in temp["flags"]:
                        temp["flags"][name] = True
                    PROCESS_STATUS.value = temp
                    if thread_id in running_threads:
                        del running_threads[thread_id]
                    if failed:
                        completed['date'] = 'Failed'

                completed_list = COMPLETED_PROCESS.value
                completed_list.append(completed)

                if len(completed_list) >= completed_max:
                    completed_list = completed_list[-completed_max:]

                COMPLETED_PROCESS.value = completed_list
        else:
            status = {"progress": progress, "total": total}
            with thread_lock:
                status_dict = PROCESS_STATUS.value

                if thread_id not in status_dict:
                    status['process'] = name
                    status['category'] = name.split(':')[0]
                    status_dict[thread_id] = status
                else:
                    status_dict[thread_id].update(status)

                if name in status_dict["flags"]:
                    status_dict["flags"][name] = False
                PROCESS_STATUS.value = status_dict
    except Exception as e:
        print(e)


def set_flags(key, value):
    with thread_lock:
        status_dict = PROCESS_STATUS.values
        status_dict["flags"][key] = value
        PROCESS_STATUS.value = status_dict
