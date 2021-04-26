__author__ = 'samyu'


from multiprocessing import Pool
import time
import ga_worker
import initGAWorker

RUNTIME = 10
INITIAL_INDIVIDUAL_SIZE = 128
WORKER_NUM = 3

REPORT_ALL = True

PEAB = False

if __name__=='__main__':


	if REPORT_ALL:
		Lst_SampleCount = []
		Lst_EvaCount = []
		Lst_TotalGen = []
		Lst_TimeUse = []

	for i in range(RUNTIME):

		print "-------------------------RUN:"+str(i)+"-------------------------"

		initGAWorker.initSomeWorker(INITIAL_INDIVIDUAL_SIZE)
		time.sleep(0.5)

		results = []
		pool = Pool(processes = WORKER_NUM)
		#startTime = time.clock()
		startTime = time.time()
		for i in range(WORKER_NUM):
			results.append(pool.apply_async(func=ga_worker.main))

		pool.close()
		pool.join()		# wait for all subprocess to finish
		#finishTime = time.clock()
		finishTime = time.time()


		print "Worker Result: "

		totalEva = 0
		totalSample = 0
		totalGen = 0
		j = 1
		print "-------Worker Num:"+str(len(results))+"-------"
		for res in results:
			print "-------Worker Info:"+str(j)+"-------"
			result = res.get()
			if result is None:
				continue
			totalEva += result['eva_count']
			totalSample += result['sample_takes']
			totalGen += result['generation_count']
			print result
			j = j+1

		print "  "
		print "Total time use: %f"%(finishTime-startTime)
		if PEAB:
			print "Total Reuntion Time:  %f" % initGAWorker.getTotalReunionTime()
 		print "totalSample: " + str(totalSample)
		print "totalEva: " + str(totalEva)
		print "totalGen: " + str(totalGen)

		if REPORT_ALL:
			Lst_SampleCount.append(totalSample)
			Lst_EvaCount.append(totalEva)
			Lst_TotalGen.append(totalGen)
			Lst_TimeUse.append((finishTime-startTime))

		time.sleep(2)


	if REPORT_ALL:
		print "============================Report_All==============================="
		print "totalSamples: "
		for item in Lst_SampleCount:
			print item,

		print "  "
		print "totalEvaluations: "
		for item in Lst_EvaCount:
			print item,

		print "  "
		print "totalGenerations: "
		for item in Lst_TotalGen:
			print item,

		print "  "
		print "totalTimeUse: "
		for item in Lst_TimeUse:
			print item,


