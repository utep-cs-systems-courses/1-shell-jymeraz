#! /usr/bin/env python3

import os
import re
import sys

pid = os.getpid()

# note that
#  fd #0 is "standard input" (by default, attached to kbd)
#  fd #1 is "standard ouput" (by default, attached to display)
#  fd #2 is "standard error" (by default, attached to display for error output)

while 1:
    strToPrint = f"{os.getcwd()} $ "
    os.write(1, strToPrint.encode())
    user_input = os.read(0, 10000).split()  # read up to 10k bytes
    if len(user_input) == 0:
        continue  # done if nothing read

    # Built-in commands for exit and cd
    if user_input[0].decode() == "exit":
        if len(user_input) > 1:
            print("Program terminated with exit code", user_input[1].decode())
            sys.exit(int(user_input[1]))
        print("Program terminated with exit code", user_input[0].decode())
        sys.exit(0)

    if user_input[0].decode() == "cd":
        if len(user_input) > 1:
            try:
                os.chdir(user_input[1])
            except FileNotFoundError:
                print(f'{user_input[0].decode()}: No such file or directory: {user_input[1].decode()}')
        else:
            os.chdir(os.path.expanduser("~"))

    else:
        rc = os.fork()

        if rc < 0:
            sys.exit(1)

        elif rc == 0:  # child
            # Redirection
            # > goes into
            # < goes out of
            if b'>' in user_input:
                os.close(1)  # redirect child's stdout
                os.open(user_input[2], os.O_CREAT | os.O_WRONLY)
                os.set_inheritable(1, True)
                user_input = user_input[:1]

            elif b'<' in user_input:
                os.close(0) # close stdin
                os.open(user_input[2], os.O_RDONLY) # redirect stdin
                os.set_inheritable(0, True)
                user_input = user_input[:1]

            for directory in re.split(":", os.environ['PATH']):  # try each directory in the path
                # Check: why are items printing here even though they were already erased?
                program = "%s/%s" % (directory, user_input[0].decode())
                try:
                    os.execve(program, user_input, os.environ)  # try to exec program
                except FileNotFoundError:  # ...expected
                    pass  # ...fail quietly

            os.write(2, ("\nChild:    Could not exec %s\n" % user_input[0]).encode())
            sys.exit(1)  # terminate with error

        else:  # parent (forked ok)
            childPidCode = os.wait()

