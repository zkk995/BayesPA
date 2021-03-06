from libbayespagibbs import *
import math
import scipy.io as sio
import numpy as np
import numpy.random as npr
import matplotlib.pyplot as plt
import os

m_K = 20
batchsize = 512
config = {  "num_topic"      :  m_K, 
            "batchsize"      :  batchsize,
            "alpha"        :  0.5,
            "beta"        :  0.45,
            "c"          :  1,
            "l"          :  164,
            "I"          :  1,
            "J"          :  3,
            "train_file"    :  "../../data/20ng_train.gml",
            "test_file"      :  "../../data/20ng_test.gml",
            "dic_file"      :   "../../data/dic.txt",
            "epoch"        :   1}
pamedlda = paMedLDAgibbs(config)

def read_gml(path):
  lines = file(path).readlines()
  labels = []
  docs = []
  for line in lines[1:]:
    line = line.replace('\n', '')
    line = line.split(' ')
    label = int(line[1])
    doc = [int(token) for token in line[2:]]
    labels += [label]
    docs += [doc]
  return (docs, labels)

# test the prediction accuracy on 20 newsgroup.
def acc_test():
  batch_size = 512
  (docs, labels) = read_gml('../../data/20ng_train.gml')
  (test_docs, test_labels) = read_gml('../../data/20ng_test.gml')
  allind = set(range(len(docs)))
  while len(allind) > 0:
    print len(allind)
    if len(allind) >= batchsize:
      ind = npr.choice(list(allind), batch_size, replace=False)
    else:
      ind = list(allind)
    allind -= set(ind)
    batch_doc = [docs[i] for i in ind]
    batch_label = [labels[i] for i in ind]
    pamedlda.train(batch_doc, batch_label)
  print 'infer'
  print pamedlda.infer(test_docs, test_labels, 100)
  print 'test accuracy = ', pamedlda.testAcc()

# gather topic representation along the time axis.
def evolving_topic():
  batch_size = 512
  (docs, labels) = read_gml('../../data/20ng_train.gml')
  (test_docs, test_labels) = read_gml('../../data/20ng_test.gml')
  allind = set(range(len(docs)))
  topics = [] 
  num_docs = []
  while len(allind) > 0:
    if len(allind) >= batchsize:
      ind = npr.choice(list(allind), batch_size, replace=False)
    else:
      ind = list(allind)
    allind -= set(ind)
    batch_doc = [docs[i] for i in ind]
    batch_label = [labels[i] for i in ind]
    pamedlda.train(batch_doc, batch_label)
    pamedlda.infer(test_docs, test_labels, 100)
    num_docs += [len(docs) - len(allind)]
    print 'processed %d docs, test accuracy = ' % (num_docs[-1]), pamedlda.testAcc()
    topics_now = []
    for ci in range(pamedlda.numLabel()):
      topics_now += [np.array(pamedlda.topicDistOfInference(ci))]
    topics += [topics_now]
  sio.savemat('topics.mat', {'topics': topics, 'labels':test_labels, 'docs':test_docs})
  print 'finished'

      


# visualize topic dist.
def visualize_topic(category_i):
  dir_name = 'visualize_dist_paMedLDAgibbs_%d'%(category_i)
  try:
      os.stat(dir_name)
  except:
      os.mkdir(dir_name)
  dic = file(config['dic_file']).readlines()
  num_category = 20
  periods = np.array([1,16,256,4096,11269])/batchsize
  label = pamedlda.labelOfInference()
  dist_all = list()
  topwords_all = list()
  elapsed = 0
  for period in periods:
    print 'period = ', period
    pamedlda.train(int(period)-elapsed)
    elapsed = period
    pamedlda.infer(100)
    print 'test acc = ', pamedlda.testAcc()
    mat = np.array(pamedlda.topicDistOfInference(category_i))
    topwords = np.array(pamedlda.topWords(category_i, 10))
    def ind2words(topwords, dic):
      topwords_list = list()
      for i in range(len(topwords)):
        row = list()
        for j in range(len(topwords[0])):
          row.append(dic[topwords[i][j]].replace('\n', ''))
        topwords_list.append(row)
      return topwords_list
    topwords = ind2words(topwords, dic)
    count = np.array([0]*20)
    dist = np.zeros((num_category, m_K))
    for ni in range(len(label)):
      mat[ni] = mat[ni]/sum(mat[ni])
      dist[label[ni]] = dist[label[ni]]+mat[ni]
      count[label[ni]] = count[label[ni]]+1
    for ci in range(num_category):
      dist[ci] = dist[ci]/float(count[ci])
      plt.clf()
      plt.bar(range(m_K), dist[ci])
      plt.savefig('%s/%d_%d.eps'%(dir_name, ci, period))
    # print dist
    dist_all.append(dist[ci])
    topwords_all.append(topwords)
  sio.savemat('%s/visualize_topic'%(dir_name), {'dist':dist_all})
  topwords_output = open('%s/topwords.txt'%(dir_name), 'w')
  for topwords in topwords_all:
    for row in topwords:
      topwords_output.write(' & '.join(row)+'\n')
    topwords_output.write('\n\n')
  topwords_output.close()
  
if __name__ == '__main__':
  # visualize_topic(0)
  # acc_test()
  evolving_topic()



