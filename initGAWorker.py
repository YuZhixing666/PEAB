__author__ = 'samyu'


import os
import uuid
from ga_worker import GA_Worker

INITIAL_INDIVIDUAL_SIZE = 128



conf = {}
conf['function'] = 'FUNCTION' in os.environ and int(os.environ['FUNCTION']) or  4
conf['instance'] = 'INSTANCE' in os.environ and int(os.environ['INSTANCE']) or  1
conf['dim'] = 'DIM' in os.environ and int(os.environ['DIM']) or 2
conf['sample_size'] = 'SAMPLE_SIZE' in os.environ and int(os.environ['SAMPLE_SIZE']) or 32
conf['FEmax'] = 5000000
conf['evospace_url'] = 'EVOSPACE_URL' in os.environ and os.environ['EVOSPACE_URL'] or '127.0.0.1:3000/peab'
conf['pop_name'] = 'POP_NAME' in os.environ and os.environ['POP_NAME'] or 'pool'
conf['max_samples'] = 'MAX_SAMPLES' in os.environ and int(os.environ['MAX_SAMPLES']) or 1000
conf['benchmark'] = 'BENCHMARK' in os.environ
conf['NGEN'] = 'NGEN' in os.environ and int(os.environ['NGEN']) or 50
conf['experiment_id'] = 'EXPERIMENT_ID' in os.environ and int(os.environ['EXPERIMENT_ID']) or str(uuid.uuid1())
conf['bound'] = (-5,5)

def initSomeWorker(num):
    worker = GA_Worker(conf)
    worker.setup()
    worker.initialize(num)

def getTotalReunionTime():
    worker = GA_Worker(conf)
    return worker.getReunionTime()

if __name__ == "__main__":

    initSomeWorker(INITIAL_INDIVIDUAL_SIZE)

