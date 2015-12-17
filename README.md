# judge

Perfect app for testing c++ and python programs

Create 'tests' directory:
```
mkdir tests
```
Create some tests with test in t{test number}.test and answer in a{test number}.test

Create 'shortcut' for launching the script
```
echo 'python -OO /path/to/test.py "$@"' > /usr/local/bin/judge
```

And simply run on program's dir
```
judge
```
