# TCP Service Monitor
A service can be registered with these parameters:
- host
- port
- down_callback
- up_callback
- polling_frequency
- outage_start_time
- outage_end_time


## run program
`python main.py`

## run unit tests
`python -m unittest test.py`

## Sample TCP Server
A sample TCP server is written in utils.py that can be started and terminated to test main.py. 

`python utils.py` 

