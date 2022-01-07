#!/bin/bash

# Start the first process
./bot.py &

# Start the second process
./server.py &

# Wait for any process to exit
#wait -n
#
## Exit with status of process that exited first
#exit $?

