#! /usr/bin/env python3

import os
import re
import sys

pid = os.getpid()

# note that
#  fd #0 is "standard input" (by default, attached to kbd)
#  fd #1 is "standard output" (by default, attached to display)
#  fd #2 is "standard error" (by default, attached to display for error output)

def exec(user_input):
    for directory in re.split(":", os.environ['PATH']):  # try each directory in the path
        program = "%s/%s" % (directory, user_input[0])
        try:
            os.execve(program, user_input, os.environ)  # try to exec program
        except FileNotFoundError:  # ...expected
            pass  # ...fail quietly

def pipe(user_input):
    pr, pw = os.pipe()
    rc = os.fork()

    if rc < 0:
        print("fork failed, returning %d\n" % rc, file=sys.stderr)
        sys.exit(1)

    if rc == 0: # writing
        os.close(1) # close standard output
        os.dup(pw)
        os.set_inheritable(1, True)

        for fd in (pr, pw):
            os.close(fd)

        user_input = user_input[0:user_input.index("|")]
        exec(user_input)

        os.write(2, ("\nChild:    Could not exec %s\n" % user_input[0]).encode())
        sys.exit(1)

    elif rc > 0: # reading
        os.close(0) # close standard input
        os.dup(pr)
        os.set_inheritable(0, True)

        for fd in (pr, pw):
            os.close(fd)

        user_input = user_input[user_input.index("|") + 1:]
        exec(user_input)

        os.write(2, ("\nChild:    Could not exec %s\n" % user_input[0]).encode())
        sys.exit(1)


while True:
    strToPrint = f"{os.getcwd()} $ "
    os.write(1, strToPrint.encode())
    user_input = os.read(0, 10000).decode().split()  # read up to 10k bytes
    if len(user_input) == 0:
        continue  # done if nothing read

    # Built-in commands for exit and cd
    elif user_input[0] == "exit":
        if len(user_input) > 1:
            print("Program terminated with exit code", user_input[1])
            sys.exit(int(user_input[1]))
        print("Program terminated with exit code", user_input[0])
        sys.exit(0)

    elif user_input[0] == "cd":
        if len(user_input) > 1:
            try:
                os.chdir(user_input[1])
            except FileNotFoundError:
                print(f'{user_input[0]}: No such file or directory: {user_input[1]}')
        else:
            os.chdir(os.path.expanduser("~"))


    elif '|' in user_input:
        pipe(user_input)

    else:

        rc = os.fork()

        if rc < 0:
            sys.exit(1)

        elif rc == 0:  # child
            # Redirection
            # > goes into
            # < goes out of
            if '>' in user_input:
                os.close(1)  # redirect child's stdout
                os.open(user_input[2], os.O_CREAT | os.O_WRONLY)
                os.set_inheritable(1, True)
                user_input = user_input[:1]

            elif '<' in user_input:
                os.close(0)  # close stdin
                os.open(user_input[2], os.O_RDONLY)  # redirect stdin
                os.set_inheritable(0, True)
                user_input = user_input[:1]

            exec(user_input)

            os.write(2, ("\nChild:    Could not exec %s\n" % user_input[0]).encode())
            sys.exit(1)  # terminate with error

        else:  # parent (forked ok)
            childPidCode = os.wait()
