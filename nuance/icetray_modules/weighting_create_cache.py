from os import mkdir
from os.path import expandvars, isdir, join
import cPickle
from icecube import weighting


list_of_datasets = [10649]
cache = weighting.SimprodNormalizations()
for dataset in list_of_datasets:
    cache.refresh(dataset)
    cache_dir = expandvars('$I3_BUILD/weighting/resources/')
    if not isdir(cache_dir):
        mkdir(cache_dir)
    cPickle.dump(cache, open(join(cache_dir, 'dbcache.pickle'), 'wb'))
