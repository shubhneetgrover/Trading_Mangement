# Trading Mangement
This script is used to do trade mangement. This script will automatically detect when a new trade has been placed, and will start mangeing the trade. Written in Python

This script is used to do Risk mangment of the live trades.
It listens to events on the user webscoket for trade activity. If a new trade is found, it start manging the trade, while also mainting required risk mangement.
All the edge cases have been covered. 
This is a working script deployed on AWS to mange some of my trading bot activity. 

## Deployment
Could be started easily with the help of python ./a1_aws_MangeTradeOnLiveData_multi_live.py
When deploying on aws, it is better to use nohup, so the terminal is non blocked and the script is launched in the background
