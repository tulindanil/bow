from subprocess import PIPE, Popen
import StringIO
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
judge_name = 'judge.cc'

class prj_type(Enum):
    c_type = 0
    py_type = 1

class Config:

    def compile(self):
        if not os.system('make test -s -i') == 0:
            print 'no makefile provided'
            if os.system('g++ -O2 -o test ' + self.cxx_mainfile):
                sys.exit(1)
            print 'compiled ' + self.cxx_mainfile

        if not 'test' in listdir('./'):
            print 'specify \'test\' output file in makefile\'s target judje'
            sys.exit(1)

        self.executable = 'test'
        self.compiled = True

    compiled = False

    def clean(self):
        if self.compiled:
            os.remove(self.executable)

    @property
    def target(self):
        if self.t == prj_type.py_type: 
            return [sys.executable, self.executable]
        else:
            if self.compiled == False: 
                self.compile()
            return './' + self.executable

config = Config()

def definePyMainFile(files):
    for e in files:
        f = open(e)
        if re.search('__name__ == \'__main__\'', f.read()):
            return e
        
def defineCMainFile(files):
    for e in files:
       if e == judge_name: continue
       f = open(e)
       if re.search(' main\(', f.read()):
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
        config.cxx_mainfile = defineCMainFile(c)

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

def getInstances(string):
    string = string.replace('\n', ' ')
    raw = string.split()
    instances = [] 
    for obj in raw:
        index = raw.index(obj)
        try: instances.append(float(obj))
        except Exception as e: 
            instances.append(obj)
    return instances

def proceed_ans(q, instance_ans, reference, i):
    if getInstances(instance_ans) == getInstances(reference): 
        q.put(test_result(type.ok, i)) 
    else: 
        q.put(test_result(type.wa, i, out=instance_ans)) 

class Judjement:

    def overall(self):
        return self.was + self.tls + self.oks

judje = Judjement()

def test_target(args):
    target = config.target
    results = args[0] 
    i = args[1]
    test = args[2] 
    answer = args[3]
    try: timeout = args[4]
    except: timeout = 1
    instance = Popen(target, stdin=PIPE, stdout=PIPE, bufsize=1)
    signal.signal(signal.SIGALRM, _handle_timeout) 
    signal.alarm(timeout) 
    try: 
        instance_ans, instance_err = instance.communicate(test) 
        proceed_ans(results, instance_ans, answer, i)
    except Exception as e: 
        results.put(test_result(type.tl, i)) 
        instance.kill()
    finally: 
        signal.alarm(0)

def countAnsOfType(res, t):
    return len([r for r in res if r.t == t])

def proceed_test_res(res):
    sets = []
    index = 0
    current = res[0]
    
    judje.was = countAnsOfType(res, type.wa)
    judje.oks = len([r for r in res if r.t == type.ok])
    judje.tls = len([r for r in res if r.t == type.tl])

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

def proceedDependecies(f, j_f):
    for line in f:
        if len(re.findall('#include "', line)) > 0:
            dependecy = line.split('"')[1]
            proceedDependecies(open(dependecy), j_f)
        else: j_f.write(line)

def collect():
    try: main_f = open(config.cxx_mainfile)
    except: 
        print 'unable to open main file'
        sys.exit(1)
    j_f = open(judge_name, 'w')
    proceedDependecies(main_f, j_f)

def main():

    if isfile(judge_name):
        print 'deleting your old ' + judge_name
        os.remove(judge_name)

    defineProjectType()

    tests, answers = getData('tests')
    manager = Manager()
    q = manager.Queue()

    if len(sys.argv) > 2 and (sys.argv[1] == '-t' or sys.argv[1] == '--test'):
        try: 
            tests = [tests[int(sys.argv[2]) - 1]]
            answers = [answers[int(sys.argv[2]) - 1]]
        except: 
            print 'Index is out of bounce'
            sys.exit(1)
    
    config.target
    args = [(q, \
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
    config.clean()

    if judje.overall() == judje.oks: 
        collect()
        print 'new ' + judge_name + ' is compiled'

if __name__ == '__main__':
    main()
