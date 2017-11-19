# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import math, nltk, random, operator
from collections import defaultdict
from nltk.corpus import wordnet as wn
plt.style.use('ggplot')

def gen_data(network=defaultdict(set)):
    words, target = wn.words(), wn.synset('mammal.n.01')
    targets = set(open('data/targets.txt').read().split('\n'))
    nouns = {noun for word in words for noun in wn.synsets(word,pos='n') if noun.name() in targets}
    for noun in nouns:
        for path in noun.hypernym_paths():
            if not target in path: continue
            for i in range(path.index(target),len(path)-1):
                if not path[i].name() in targets: continue
                network[noun.name()].add(path[i].name())
    with open('data/mammal_subtree.tsv','w') as out:
        for key,vals in network.iteritems():
            for val in vals: out.write(key+'\t'+val+'\n')

class Poincare(object):
    eps = 1e-6
    def __init__(self,num_iter=10,num_negs=10,lr1=0.2,lr2=0.01,dp='data/mammal_subtree.tsv'): # dim=2
        self.dim = 2
        self.num_iter = num_iter
        self.num_negs = num_negs
        self.lr1, self.lr2 = lr1, lr2
        self.pdata = map(lambda l:l.split('\t'),filter(None,open(dp).read().split('\n')))
        self.pdict = {w:i for i,w in enumerate(set(reduce(operator.add,self.pdata)))}
        self.pembs = [np.random.uniform(low=-0.001,high=0.001,size=(2,)) for i in range(len(self.pdict))]
    def add_clip(self,c,u,v,thresh=1.-eps):
        uu, uv, vv = (u**2).sum(), (u*v).sum(), (v**2).sum(); C = uu+2*c*uv+c*c*vv
        scale = thresh/C**0.5 if C>thresh**2 else 1.
        return (u+c*v)*scale
    def acosh(self,x):
        return math.log(x+(x**2-1)**0.5)
    def dists(self,u,v):
        uu, uv, vv = (u**2).sum(), (u*v).sum(), (v**2).sum()
        alpha, beta = max(self.eps,1-uu), max(self.eps,1-vv)
        gamma = max(1.,1+2*(uu-2*uv+vv)/alpha/beta)
        return self.acosh(gamma), (u,v,uu,uv,vv,alpha,beta,gamma)
    def backward(self,gdo,env):
        c = gdo; u,v,uu,uv,vv,alpha,beta,gamma = env
        if gamma == 1: return None, None
        c *= 4./(gamma**2-1)**0.5/alpha/beta
        cu, cv = c*alpha**2/4., c*beta**2/4.
        gdu = cu*((vv-2*uv+1)/alpha*u-v)
        gdv = cv*((uu-2*uv+1)/beta*v-u)
        return gdu, gdv
    def train(self):
        lp = range(len(self.pdict))
        for epoch in xrange(self.num_iter):
            print epoch; random.shuffle(self.pdata)
            r = 1.*epoch/self.num_iter; lr = (1-r)*self.lr1+r*self.lr2
            for w1,w2 in self.pdata:
                i1,i2 = self.pdict[w1],self.pdict[w2]
                d,env = self.dists(self.pembs[i1],self.pembs[i2])
                exp_neg_dists = [(i1,i2,math.exp(-d),env)]
                for _ in xrange(self.num_negs):
                    s1,s2 = random.choice(lp),random.choice(lp)
                    d,env = self.dists(self.pembs[s1],self.pembs[s2])
                    exp_neg_dists.append((s1,s2,math.exp(-d),env))
                Z = sum(map(operator.itemgetter(2),exp_neg_dists))
                for i,(i1,i2,d,env) in enumerate(exp_neg_dists):
                    gl,gr = self.backward(1.*(i==0)-d/Z,env)
                    if gl is not None: self.pembs[i1] = self.add_clip(-lr,self.pembs[i1],gl)
                    if gr is not None: self.pembs[i2] = self.add_clip(-lr,self.pembs[i2],gr)
        self.plot()
    def plot(self):
        fig = plt.figure(figsize=(10,10)); ax = plt.gca(); ax.cla()
        ax.set_xlim((-1.1,1.1)); ax.set_ylim((-1.1,1.1))
        ax.add_artist(plt.Circle((0,0),1.,color='black',fill=False))
        for w,i in self.pdict.iteritems():
            c0,c1 = self.pembs[i]
            ax.plot(c0,c1,'o',color='y')
            ax.text(c0+.01,c1+.01,w,color='b')
        fig.savefig('data/mammal.png',dpi=fig.dpi); # plt.show()

if __name__ == '__main__':
    Poincare(num_iter=200).train()
