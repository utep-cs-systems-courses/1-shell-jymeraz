#! /usr/bin/env python3

import os, sys, time, re

pid = os.getpid()

# note that
#  fd #0 is "standard input" (by default, attached to kbd)
#  fd #1 is "standard ouput" (by default, attached to display)
#  fd #2 is "standard error" (by default, attached to display for error output)

while 1:
    strToPrint = f"{os.getcwd()} $ "
    os.write(1, strToPrint.encode())
    input = os.read(0, 10000).split()  # read up to 10k bytes
    if len(input) == 0: continue     # done if nothing read

    if input[0].decode("utf-8") == "exit":
        if len(input) > 1:
            print("Program terminated with exit code", input[1].decode("utf-8"))
            sys.exit(int(input[1]))
        print("Program terminated with exit code", input[0].decode("utf-8"))
        sys.exit(0)

    if input[0].decode("utf-8") == "cd":
        if len(input) > 1:
            try:
                os.chdir(input[1])
            except FileNotFoundError:
                print(f'{input[0].decode("utf-8")}: no such file or directory: {input[1].decode("utf-8")}')
        else:
            os.chdir(os.path.expanduser("~"))

    else:
        os.write(1, ("About to fork (pid:%d)\n" % pid).encode())

        rc = os.fork()

        if rc < 0:
            os.write(2, ("fork failed, returning %d\n" % rc).encode())
            sys.exit(1)

        elif rc == 0:                   # child
            os.write(1, ("Child: My pid==%d.  Parent's pid=%d\n" %
                         (os.getpid(), pid)).encode())
            args = [input[0]]
            for dir in re.split(":", os.environ['PATH']): # try each directory in the path
                program = "%s/%s" % (dir, args[0])
                os.write(1, ("Child:  ...trying to exec %s\n" % program).encode())
                try:
                    os.execve(program, args, os.environ) # try to exec program
                except FileNotFoundError:             # ...expected
                    pass                              # ...fail quietly

            os.write(2, ("Child:    Could not exec %s\n" % args[0]).encode())
            sys.exit(1)                 # terminate with error

        else:                           # parent (forked ok)
            os.write(1, ("Parent: My pid=%d.  Child's pid=%d\n" %
                         (pid, rc)).encode())
            childPidCode = os.wait()
            os.write(1, ("Parent: Child %d terminated with exit code %d\n" %
                         childPidCode).encode())
