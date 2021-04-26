__author__ = 'samyu'

# WORKER_NUM = 1
INITIAL_INDIVIDUAL_SIZE = 128
#POOL_SIZE = INITIAL_INDIVIDUAL_SIZE*4
POOL_SIZE = 256

STARVATION_SIZE = 64

# number of best individual every Client's subpopulation
BEST_IND_NUMBER = 2
# the number of the best individuals duplication, better set by the number of workers
MIGRATION_RATE = 1
# reunion interval trigger by the times of Client return, better set by the number of workers
REUNION_INTERVAL = 8

# reunion trigger
TRIGGER_STRAVATION = True
TRIGGER_INTERVAL = False

# Residual percentage record
RECORD_RESIDUAL = False

# Pool Size record
RECORD_POOLSIZE = False
# Reunion Time record
RECORD_REUNIONTIME = False

HOST="127.0.0.1"
PORT=6379

import os, redis, random

##REDISCLOUD
import urlparse
import time


if os.environ.get('REDISTOGO_URL'):
    url = urlparse.urlparse(os.environ.get('REDISTOGO_URL'))
    r = redis.Redis(host=url.hostname, port=url.port, password=url.password)
#LOCAL
else:
    r = redis.Redis(host=HOST, port=PORT)


#for list.sort(), combine by tuple and sort by the second element
def takeSecond(elem):
    return elem[1]


class Individual:
    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.fitness = kwargs.get('fitness',{})
        self.chromosome = kwargs.get('chromosome',[])
        self.__dict__.update(kwargs)


    #put itself into a particular population
    def put(self, population):
        #use pipeline can be more efficient when there are many data.
        pipe = r.pipeline()
        if pipe.sadd( population, self.id ):        #here put the id in that population
            pipe.set( self.id , self.__dict__ )     #here put all the individual in that id
            pipe.execute()
            return True
        else:
            return False

    #get itself form the population and return
    def get(self, as_dict = False):
        if r.get(self.id):
            #eval function to excute a expression
            _dict = eval(r.get(self.id))
            self.__dict__.update(_dict)
        else:
            raise LookupError("Key Not Found: "+self.id)

        if as_dict:
            return self.__dict__
        else:
            return self

    def getFitness(self):
        return self.get(as_dict=True)['fitness']['DefaultContext']

    def __repr__(self):
        return self.id +":"+ str(self.fitness) +":" + str( self.chromosome)


    def as_dict(self):
        return self.__dict__


class Population:
    def __init__(self, name = "pool" ):

        # name='pop' and the buffer both story the id of the individuals only
        # all info of the individuals are store in the set named 'individual'
        self.name = name
        self.sample_counter = self.name+':sample_count'
        self.individual_counter = self.name+':individual_count'
        # we don't need this thing
        # if a worker lost, the sample will always in the buffer
        #self.sample_queue = self.name+":sample_queue"       # to store the redis-id of the samples
        self.returned_counter = self.name+":returned_count"
        self.reunion_counter = self.name+':reunion_count'

        self.buffer = self.name+':buffer'
        self.buffer_best = self.name+':buffer_best'

        self.reunion_lock = self.name+":reunion_lock"

        # counting client response from last reunion
        self.reunion_trigger = 0


        # for Residual percentage computing
        if RECORD_RESIDUAL:
            self.initPopSize = INITIAL_INDIVIDUAL_SIZE
            self.initPopIdSet = set()
            self.residualRecord = self.name+":residualRecord"

        # for Pool Size computing
        if RECORD_POOLSIZE:
            #self.popchange_counter =self.name+':popchange_count'
            self.poolSizeRecord = self.name+":poolSizeRecord"

        # for Reunion Time record
        if RECORD_REUNIONTIME:
            self.reunionTimeRecord = self.name+":reunionRecord"

    def get_returned_counter(self):
        return int( r.get(self.returned_counter))


    def individual_next_key(self):
        key = r.incr(self.individual_counter)
        return self.name+":individual:%s" % key

    #get the population size
    def size(self):
        return r.scard(self.name)


    def initialize(self):
        pattern = "%s*" % self.name
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)

        r.flushall()
        # setnx: set when the key not exist
        r.setnx(self.sample_counter,0)
        r.setnx(self.individual_counter,0)
        r.setnx(self.returned_counter,0)
        r.setnx(self.reunion_counter,0)

        r.setnx(self.reunion_lock,0)
        #r.setnx(self.respawn_counter,0)
        r.setnx(self.name+":found",0)

        if RECORD_RESIDUAL:
            r.hset(self.residualRecord,"Sample_0",self.initPopSize)

        if RECORD_POOLSIZE:
            r.hset(self.poolSizeRecord,time.clock(),r.scard(self.name))

    def check_reunion(self):
        if int(r.get(self.reunion_lock))==0:
            return True     #can use
        else:
            return False

    def lock_reunion(self):
        r.set(self.reunion_lock, 1)

    def unlock_reunion(self):
        r.set(self.reunion_lock, 0)


    def get_sample(self, size):

        # trigger reunion
        if TRIGGER_STRAVATION and (r.scard(self.name) <= STARVATION_SIZE or r.scard(self.name) < size):
            print '--------stravation---------'
            if self.check_reunion():
                self.lock_reunion()
                self.reunion()
                self.unlock_reunion()
            else:
                print "!!!!!!!!crash and skip the reunion,,,need to recalibrate the starvation size"
                return None     #not enough individuals

        r.incr(self.sample_counter) #the single number id

        #Only get the key of the individuals
        #spop: pop a set of member from the set ramdomly,
        sample = [r.spop(self.name) for i in range(size)]

        #If there is no member in pool
        if None in sample:
            sample = [s for s in sample if s]
            if not sample:
                return None

        r.sadd(self.buffer, *sample)

        if RECORD_RESIDUAL and len(self.initPopIdSet) > 0:
            self.initPopIdSet = self.initPopIdSet - set(sample)
            r.hset(self.residualRecord,"Sample_"+r.get(self.sample_counter),len(self.initPopIdSet))

        # if RECORD_POOLSIZE:
        #     #counter = r.incr(self.popchange_counter)
        #     r.hset(self.poolSizeRecord,time.clock(),r.scard(self.name))

        try:
            result =  {'sample':   [Individual(id=key).get(as_dict=True) for key in sample ]}
        except:
            return None
        return result


    def read_pop_keys(self):
        sample = r.smembers(self.name)
        #convert tuples to lists
        sample = list(sample)
        result =  { 'sample': sample }
        return result


    def read_all(self):
        sample = r.smembers(self.name)
        result =  { 'sample':   [Individual(id=key).get(as_dict=True) for key in sample]}
        return result


    def put_individual(self, location, **kwargs):
        if kwargs['id'] is None:
            kwargs['id'] = self.name+":individual:%s" % r.incr(self.individual_counter)
        ind = Individual(**kwargs)
        ind.put(location)
        return kwargs['id']


    # always put in the pool
    def put_subpopulation(self, subpop):
        for ind in subpop:
            if ind['id'] is None:
                ind['id'] = self.name+":individual:%s" % r.incr(self.individual_counter)
            self.put_individual(self.name, **ind)

            if RECORD_RESIDUAL:
                self.initPopIdSet.add(ind['id'])

        if RECORD_POOLSIZE:
            #counter = r.incr(self.popchange_counter)
            r.hset(self.poolSizeRecord,time.clock(),r.scard(self.name))

        return {}

    # always put in the buffer
    def put_sample(self, sample):
        #isinstance: whether an object is of a known type
        if not isinstance(sample,dict):
            raise TypeError("Samples must be dictionaries")

        r.incr(self.returned_counter)
        self.reunion_trigger += 1

        samples = sample['sample']
        samples_best = samples[:BEST_IND_NUMBER]
        samples_others = samples[BEST_IND_NUMBER:]

        for member in samples_best:
            if member['id'] is None:
                member['id'] = self.name+":individual:%s" % r.incr(self.individual_counter)
            self.put_individual(self.buffer_best, **member)

        for member in samples_others:
            if member['id'] is None:
                member['id'] = self.name+":individual:%s" % r.incr(self.individual_counter)
            self.put_individual(self.buffer, **member)

        if RECORD_POOLSIZE:
            #counter = r.incr(self.popchange_counter)
            r.hset(self.poolSizeRecord,time.clock(),r.scard(self.name))

        # trigger reunion
        # really need the inflation check?
        if TRIGGER_INTERVAL and self.reunion_trigger >= REUNION_INTERVAL:
            print '--------Interval---------'
            if self.check_reunion():
                self.lock_reunion()
                self.reunion()
                self.unlock_reunion()
            else:
                print "!!!!!!!!crash and skip the reunion"



    def isFound(self):
        return r.get(self.name+":found")

    def found_it(self):
        r.set(self.name+":found",1)



    # reunion have done:
    # 1. recombine the buffer zone and pool zone
    # 2. control the size of the pool
    # 3. execute the 'Migration' of the best individuals
    def reunion(self):
        print "--------reunion---------"

        if RECORD_REUNIONTIME:
            start_time = time.clock()

        self.reunion_trigger = 0

        num_pool = r.scard(self.name)
        num_best = r.scard(self.buffer_best)
        num_others = r.scard(self.buffer)

        print "num_pool: "+ str(num_pool)
        print "num_best: "+str(num_best)
        print "num_others: "+str(num_others)

        totalpop = num_pool+num_best+num_others

        #combine population, done in the redis
        if totalpop <= POOL_SIZE:
            print "1. combline and reserve all individuals"
            r.sunionstore(self.name, self.name, self.buffer_best, self.buffer)
        elif num_best <= POOL_SIZE < totalpop:
            print "2. remove some individual"
            r.sunionstore(self.name, self.name, self.buffer_best)
            num_remain = POOL_SIZE - (num_pool + num_best + num_best*MIGRATION_RATE)   # number of individuals still need to combine
            print "num_remain: " + str(num_remain)
            print "remove num: " + str(num_others - num_remain)

            member_others = r.smembers(self.buffer)
            fitness_lst_evaluated = []
            fitness_lst_not_evaluated = []
            for member_id in member_others:
                fit = Individual(id=member_id).getFitness()
                if fit==-1:
                    fitness_lst_not_evaluated.append((member_id,fit))
                else:
                    fitness_lst_evaluated.append((member_id,fit))

            fitness_lst_evaluated.sort(key=takeSecond, reverse=True)    # descending order

            if len(fitness_lst_not_evaluated) >= num_remain:    #It doesn't happen normally
                for i in range(num_remain):
                    r.smove(self.buffer, self.name, fitness_lst_not_evaluated[i][0])
            else:
                for i in range(len(fitness_lst_not_evaluated)):
                    r.smove(self.buffer, self.name, fitness_lst_not_evaluated[i][0])
                for i in range(num_remain-len(fitness_lst_not_evaluated)):
                    r.smove(self.buffer, self.name, fitness_lst_evaluated[i][0])

        else:
            print "3. warning: unusual...."
            r.sunionstore(self.name, self.name, self.buffer_best, self.buffer)  #reserve all not worst individuals

        #migration
        members_best = r.smembers(self.buffer_best)
        for i in range(MIGRATION_RATE):
            for member in members_best:
                # bug: menber here just the id of the individual
                newInd = Individual(id=member).get(as_dict=True)
                newInd['id'] = None
                newId = self.put_individual(self.name, **newInd)

        #clean the buffer zone
        r.delete(self.buffer_best)
        r.delete(self.buffer)

        r.incr(self.reunion_counter)

        if RECORD_POOLSIZE:
            #counter = r.incr(self.popchange_counter)
            r.hset(self.poolSizeRecord,time.clock(),r.scard(self.name))

        if RECORD_REUNIONTIME:
            finish_time = time.clock()
            total_time = finish_time - start_time
            r.hset(self.reunionTimeRecord,r.get(self.reunion_counter),total_time)

        print "--------finish reunion---------"
    

    def getReunionTime(self):
        if RECORD_REUNIONTIME:
            timeRecords = r.hgetall(self.reunionTimeRecord)
            totalTime = 0
            for value in timeRecords.values():
                totalTime = totalTime + float(value)
            return totalTime
        else:
            return 0



def init_pop( populationSize, bits = 256):
    server = Population('pool')
    server.initialize()
    for individual in range(populationSize):
        chrome = [random.randint(0,1) for _ in range(bits)]
        individual = {"id":None,"fitness":{"DefaultContext":0.0 },"chromosome":chrome}
        server.put_individual('pool', **individual)


if __name__ == "__main__":
    init_pop(256)
