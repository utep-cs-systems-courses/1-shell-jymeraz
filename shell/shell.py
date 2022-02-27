#! /usr/bin/env python3

import os
import re
import sys

pid = os.getpid()

if 'PS1' not in os.environ:
    os.environ['PS1'] = "$"


# note that
#  fd #0 is "standard input" (by default, attached to kbd)
#  fd #1 is "standard output" (by default, attached to display)
#  fd #2 is "standard error" (by default, attached to display for error output)

def command_exec(exec_input):
    for directory in re.split(":", os.environ['PATH']):  # try each directory in the path
        program = "%s/%s" % (directory, exec_input[0])
        try:
            os.execve(program, exec_input, os.environ)  # try to exec program
        except FileNotFoundError:  # ...expected
            pass  # ...fail quietly
    print(f"{exec_input[0]}: command not found.")


def pipe(pipe_input, pipe_wait):
    pr, pw = os.pipe()
    rc_1 = os.fork()  # call first fork to write

    if rc_1 < 0:  # fork failed
        sys.exit(1)

    elif rc_1 == 0:  # writing
        os.close(1)  # close standard output
        os.dup(pw)
        os.set_inheritable(1, True)

        for fd in (pr, pw):
            os.close(fd)

        pipe_input = pipe_input[0:pipe_input.index("|")]
        command_exec(pipe_input)
        sys.exit(1)

    else:  # parent (forked ok)
        rc_2 = os.fork()  # call second fork to read

        if rc_2 < 0:  # fork failed
            sys.exit(1)

        elif rc_2 == 0:  # reading
            os.close(0)  # close standard input
            os.dup(pr)
            os.set_inheritable(0, True)

            for fd in (pr, pw):
                os.close(fd)

            pipe_input = pipe_input[pipe_input.index("|") + 1:]
            command_exec(pipe_input)
            sys.exit(1)
        else:
            if pipe_wait:
                os.wait()
        for fd in (pr, pw):
            os.close(fd)
        if pipe_wait:
            os.wait()


while True:
    wait = True
    strToPrint = f"{os.getcwd()} {os.environ['PS1']} "
    os.write(1, strToPrint.encode())
    user_input = os.read(0, 10000).decode().split()  # read up to 10k bytes
    if len(user_input) == 0:
        continue  # done if nothing read

    if "&" in user_input:  # background tasks
        user_input.remove("&")
        wait = False
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
        pipe(user_input, wait)

    else:
        rc = os.fork()

        if rc < 0:  # fork failed
            sys.exit(1)

        elif rc == 0:  # child
            # Redirection
            if '>' in user_input:  # > goes into
                os.close(1)  # redirect child's stdout
                os.open(user_input[2], os.O_CREAT | os.O_WRONLY)
                os.set_inheritable(1, True)
                user_input = user_input[:1]

            elif '<' in user_input:  # < goes out of
                os.close(0)  # close stdin
                os.open(user_input[2], os.O_RDONLY)  # redirect stdin
                os.set_inheritable(0, True)
                user_input = user_input[:1]

            command_exec(user_input)
            sys.exit(1)  # terminate with error

        else:  # parent (forked ok)
            if wait:
                os.wait()
