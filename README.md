# Trading Management
This repository contains a Python-based script for managing trades in real-time. The script monitors live trades, checks risk parameters, and manages the trade lifecycle, including setting stop-loss and take-profit levels. It is designed to work in conjunction with a WebSocket connection for real-time market data and trade event handling.

## Features
- **Real-Time Trade Management**: Automatically detects new trades and starts managing them based on predefined risk parameters.
- **Stop-Loss and Take-Profit Calculations**: Dynamically calculates and adjusts stop-loss and take-profit levels to manage risk effectively.
- **WebSocket Integration**: Uses a WebSocket connection to listen for trade events and real-time market data.
- **Multi-Threaded Execution**: The script runs trade management and WebSocket listening concurrently using Python threads.
## Requirements
- Python 3.x
- Required Python packages:
  - websocket-client
  - requests
  - pandas
  - threading
  - math
  - Install the required packages using:

```bash
pip install websocket-client requests pandas
```
## Setup
Clone this repository:

```bash
git clone https://github.com/shubhneetgrover/Trading_Mangement.git
cd Trading_Mangement
```
## Usage
**The main script to manage trades is a1_aws_MangeTradeOnLiveData_multi_live.py. You can start it by running**:
   ```bash
   python ./a1_aws_MangeTradeOnLiveData_multi_live.py
   ```
   This will start the trade management process, including setting up the WebSocket connection and managing trades in real-time.


## Contributing
If you would like to contribute to this project, feel free to fork the repository and submit a pull request. Any contributions are welcome!

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Contact
For any questions or issues, please contact the repository owner via GitHub.

