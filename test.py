from subprocess import PIPE, Popen
from multiprocessing import Pool, Manager
import signal
from time import sleep
import sys
import re
from os import listdir
from os.path import isfile, join

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[33m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def _handle_timeout(*args):
    raise ValueError 

def numeric_compare(x, y):
    x = re.findall('\d+', x)
    y = re.findall('\d+', y) 
    return int(x[0]) - int(y[0])

def print_colored((string, code)):
    sys.stdout.write('[' + code + string + bcolors.ENDC + ']')

def proceed_test_res(res):
    sets = []
    index = 0
    current = res[0]
    for i in range(len(res)):
        if not res[i][1] == current[1]: 
            sets.append((index, i - 1, current))
            current = res[i]
            index = i

    sets.append((index, i, current))

    for s in sets:
        print_colored(s[2][1:])

        if s[1] - s[0] == 0:
            print ' Test #' + str(s[0] + 1)
        else:
            print ' Tests #' + str(s[0] + 1) + '..' + str(s[1] + 1)

def test_target(args):
    target = args[0]
    results = args[1] 
    i = args[2]
    test = args[3] 
    answer = args[4]
    
    try:
        timeout = args[5]
    except:
        timeout = 1

    instance = Popen(target, stdin=PIPE, stdout=PIPE, bufsize=1)
    instance.stdin.write(test)

    signal.signal(signal.SIGALRM, _handle_timeout) 
    signal.alarm(timeout) 
    try: 
        instance_answer = instance.stdout.read() 
        if instance_answer == answer: 
            results.put((i, "PASSED", bcolors.OKGREEN)) 
        else: 
            results.put((i, "FAILED", bcolors.FAIL)) 
    except ValueError: 
        results.put((i, "TIME LIMIT", bcolors.WARNING)) 
        instance.kill()
    finally: 
        signal.alarm(0)

def main():

    if len(sys.argv) < 3:
        print 'test test_file directory'

    dirname = sys.argv[2]

    files = [join(dirname, f) for f in listdir(dirname) if isfile(join(dirname, f))]
    
    tests = [f for f in files if f.split('/')[-1][0] == 't']
    tests = sorted(tests, cmp=numeric_compare)
    
    answers = [f for f in files if f.split('/')[-1][0] == 'a']
    answers = sorted(answers, cmp=numeric_compare)

    if not len(answers) == len(tests):
        print 'Hmm...Test directory is not okay'
        sys.exit(0)

    target = sys.argv[1]

    manager = Manager()
    q = manager.Queue()

    args = []

    for f in tests:

        test = open(f).read()
        index = tests.index(f)
        answer = open(answers[index]).read()
        args.append((target, q, index, test, answer)) 

    p = Pool(len(tests))
    p.map(test_target, args)


    res = [i for i in range(q.qsize())]
    while not q.empty():
        r = q.get()
        res[r[0]] = r

    proceed_test_res(res)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print e
