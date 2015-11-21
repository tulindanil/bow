from subprocess import PIPE, Popen
from multiprocessing import Pool, Manager
import signal
from time import sleep
import sys
import re
import os
from os import listdir
from os.path import isfile, join
from enum import Enum

py_switches = ['py']
c_switches = ['cpp', 'cc', 'hpp', 'h', 'hxx', 'cxx', 'c']

class prj_type(Enum):
    c_type = 0
    py_type = 1

class config:

    @staticmethod
    def target():
        if config.t == prj_type.py_type: 
            return [sys.executable, config.executable]
        else:
            return './' + config.executable

def definePyMainFile(files):
    for e in files:
        f = open(e)
        if re.search('__name__', f.read()):
            return e
        
def defineCMainFile(files):
    for e in files:
       f = open(e)
       if re.search('main(*)', f.read()):
           return e

def defineProjectType():
    names = listdir('./');
    py = []
    c = []
    for name in names:
        s = name.split('.')
        e = ''
        try: e = s[-1]
        except: continue
        if e in py_switches: 
            py.append(name)
        elif e in c_switches:
            c.append(name)
    if len(c) > 0 and len(py) > 0:
        print 'Can\'t determinate your project\'s language'
        sys.exit(1)
    if len(c) == 0 and len(py) == 0:
        print 'Nothing to test'
        sys.exit(1)
    if len(py) > 0:
        config.t = prj_type.py_type
        config.executable = definePyMainFile(py)
    elif len(c) > 0:
        config.t = prj_type.c_type
        config.executable = defineCMainFile(c)

def getData(dirname):
    files = [join(dirname, f) for f in listdir(dirname) if isfile(join(dirname, f))]
    tests = [f for f in files if f.split('/')[-1][0] == 't']
    tests = sorted(tests, cmp=numeric_compare)
    answers = [f for f in files if f.split('/')[-1][0] == 'a']
    answers = sorted(answers, cmp=numeric_compare)
    if not len(answers) == len(tests):
        print 'Hmm...Test directory is not okay'
        sys.exit(0)
    return (tests, answers)


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[33m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class TimeError(Exception):
    pass

def _handle_timeout(*args):
    raise Exception 

def numeric_compare(x, y):
    x = re.findall('\d+', x)
    y = re.findall('\d+', y) 
    return int(x[0]) - int(y[0])

def print_colored((string, code)):
    sys.stdout.write('[' + code + string + bcolors.ENDC + ']')

class type(Enum):
    wa = 0
    ok = 1
    tl = 2

class test_result():

    def __init__(self, t, i, out=""):
        self.t = t
        self.index = i
        self.out = out

    def getDescription(self):
        if self.t == type.wa:
            return ('FAILED', bcolors.FAIL)
        elif self.t == type.ok:
            return ('PASSED', bcolors.OKGREEN)
        elif self.t == type.tl:
            return ('TIME LIMIT', bcolors.WARNING)

def proceed_ans(q, instance_ans, ans, i):
    if instance_ans == ans: 
        q.put(test_result(type.ok, i)) 
    else: 
        q.put(test_result(type.wa, i, out=instance_ans)) 

def test_target(args):
    target = args[0]
    results = args[1] 
    i = args[2]
    test = args[3] 
    answer = args[4]
    try: timeout = args[5]
    except: timeout = 1
    instance = Popen(target, stdin=PIPE, stdout=PIPE, bufsize=1)
    instance.stdin.write(test)
    signal.signal(signal.SIGALRM, _handle_timeout) 
    signal.alarm(timeout) 
    try: 
        instance_ans = instance.stdout.read() 
        proceed_ans(results, instance_ans, answer, i)
    except: 
        results.put(test_result(type.tl, i)) 
        instance.kill()
    finally: signal.alarm(0)

def proceed_test_res(res):
    sets = []
    index = 0
    current = res[0]
    for i in range(len(res)):
        if not res[i].t == current.t: 
            sets.append((index, i - 1, current))
            current = res[i]
            index = i
    sets.append((index, i, current))
    for s in sets:
        print_colored(s[2].getDescription())
        if s[1] - s[0] == 0:
            print ' Test #' + str(s[0] + 1)
        else:
            print ' Tests #' + str(s[0] + 1) + '..' + str(s[1] + 1)

def main():

    defineProjectType()

    tests, answers = getData('tests')

    manager = Manager()
    q = manager.Queue()

    if len(sys.argv) > 2 and (sys.argv[1] == '-t' or sys.argv[1] == '--test'):
        try: 
            tests = [tests[int(sys.argv[2]) - 1]]
        except: 
            print 'Wrong argument'
            sys.exit(1)

    args = [(config.target(), \
             q, \
             tests.index(f) ,\
             open(f).read(), \
             open(answers[tests.index(f)]).read()) \
             for f in tests] 

    p = Pool(len(tests))
    p.map(test_target, args)

    res = [i for i in range(q.qsize())]
    while not q.empty():
        r = q.get()
        res[r.index] = r

    proceed_test_res(res)

#if __name__ == '__main__':
#try:
main()
#except Exception as e:
    #print e
