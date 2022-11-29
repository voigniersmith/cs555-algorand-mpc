PyTeal Course Comands

// Initial venv setup
cd pyteal-course
python -m venv venv

// Continuing venv setup
source ./venv/bin/activate

// Setting up docker containers
./sandbox/sandbox up

// Close docker container
./sandbox/sandbox down

// Create contract handler
./build.sh contracts.counter.step_01

// Connecting to docker container
./sandbox enter <container name>

// Create application (smart contract) in container
goal app create --creator $ONE --approval-prog /data/build/approval.teal --clear-prog /data/build/clear.teal --global-byteslices 1 --global-ints 1 --local-byteslices 0 --local-ints 0

// check app info
goal app info --app-id <application index>

// Check the storage of application storage
goal app read --global --app-id <application index>

// Send a request to the smart contract
goal app call --app-id 8 --from $ONE --app-arg "str:inc"

// Stop a venv
deactivate

Meanings:

- Application Account -> Where the ALGOS (currency) go and are then from

- tt -> Teal Type, there are only 2
    - tt == 2 -> uint64
    - tt == 1 -> byteslice

Debugger:

While inside an application to generate a dry run for a debugger
goal app call --app-id 8 --from $ONE --app-arg "str:dec" --dryrun-dump -o tx.dr

tealdbg debug -d tx.dr --listen 0.0.0.0