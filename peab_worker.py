__author__ = 'samyu'

import requests
import random

class Individual:
    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.fitness = kwargs.get('fitness',{})
        self.chromosome = kwargs.get('chromosome',[])
        self.__dict__.update(kwargs)

    def __repr__(self):
        return self.id +":"+ str(self.fitness) +":" + str( self.chromosome)

    def as_dict(self):
        return self.__dict__

    def chromosome_map(self, f):
        return map(f,self.chromosome)




class PeabWorker(object):
    def __init__(self, server, space, workerid):
        self.server = server
        self.space = space
        #self.url = 'http://%s/%s/'%(self.server,self.space)
        self.url = 'http://%s/'%self.server
        self.headers = {'content-type': 'application/json'}
        self.json = {'params':{}, 'method':'', 'id':str(workerid)}

    # no use from now
    def delete(self):
        requests.delete(self.url)

    def initialize(self):
        self.json['method'] = 'initialize'
        requests.post(self.url, headers=self.headers, json=self.json)

    def post_individual(self,individual):
        self.json['method'] = 'putIndividual'
        self.json['params'] = individual
        requests.post(self.url, headers=self.headers, json=self.json)

    def get_individual(self, id ):
        if isinstance(id,int):
            id = str(id)
        self.json['method'] = 'getIndividual'
        self.json['params'] = {'id':id}
        r = requests.get(self.url+'individual/'+id)
        return Individual(**r.json())

    def post_subpop(self, pop):
        self.json['method'] = 'put_subpop'
        self.json['params'] = {'subpop':pop}
        r = requests.post(self.url, headers=self.headers, json=self.json)
        return r.text

    def put_sample(self,pop):
        self.json['method'] = 'putSample'
        self.json['params'] = {'sample':pop}
        r = requests.post(self.url, headers=self.headers, json=self.json)
        #r = requests.put(self.url+'sample', json=pop)
        return r.text

    def get_sample(self,n):
        if not isinstance(n, int):
            n = int(n)
        self.json['method'] = 'getSample'
        self.json['params'] = {'size':n}
        r = requests.post(self.url, headers=self.headers, json=self.json)
        #r = requests.get(self.url + 'sample/'+ n)
        if not r.json()['result']:
            # print r.json()['error']['message']
            # print "retry: get_sample"
            return self.get_sample(n)
        
        return r.json()['result']

    def found(self):
        self.json['method'] = 'found'
        self.json['params'] = {}
        r = requests.post(self.url, headers=self.headers, json=self.json)

    def isFound(self):
        self.json['method'] = 'isFound'
        self.json['params'] = {}
        r = requests.post(self.url, headers=self.headers, json=self.json)
        return r.json()['result']

    def getReunionTime(self):
        self.json['method'] = 'getReunionTime'
        self.json['params'] = {}
        r = requests.post(self.url, headers=self.headers, json=self.json)
        return r.json()['result']


def initialize( evospace_url, pop_name, dim, lb, ub, n ):
    worker = PeabWorker(evospace_url, pop_name)
    worker.delete()
    worker.initialize()
    init_pop = [{"chromosome": [random.uniform(lb,ub) for _ in range(dim)], "id": None, "fitness": {"DefaultContext": 0.0}} for _ in range(n)]
    worker.post_subpop(init_pop)






