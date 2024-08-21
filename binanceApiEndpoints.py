import time
import asyncio
from binance.client import Client
# from binance import ThreadedWebsocketManager, AsyncClient, BinanceSocketManager
from config import *
from binance.enums import *
from binance.helpers import round_step_size
import json
from binance.error import ClientError
from binance.exceptions import *
import logging

# client = Client(api_key_futures, api_secret_futures, testnet=True)
client = Client(api_key_futures_real, api_secret_futures_real)
KELLY = 18

print("Live at binance Client!")
currency_config ={
    "BTCUSDT" :
    {
        "quantity": 0.002,
        "step_size": 0.1,
        "quantity_step_size": 0.001,
        "leverage":KELLY,
        "notional_limit":500
    },
    "ETHUSDT" :
    {
        "quantity": 0.02,
        "step_size": 0.01,
        "quantity_step_size": 0.001,
        "leverage":KELLY,
        "notional_limit":500
    },
    "OPUSDT" :
    {
        "quantity": 3,
        "step_size": 0.0001,
        "quantity_step_size": 0.1,
        "leverage":KELLY,
        "notional_limit":500
    },
    "DOGEUSDT" :
    {
        "quantity": 33,
        "step_size": 0.00001,
        "quantity_step_size": 1,
        "leverage":KELLY,
        "notional_limit":50000
    },
    "BNBUSDT" :
    {
        "quantity": 0.01,
        "step_size": 0.01,
        "quantity_step_size": 0.01,
        "leverage":KELLY,
        "notional_limit":50000
    },
    "FETUSDT" :
    {
        "quantity": 2,
        "step_size": 0.0001,
        "quantity_step_size": 1,
        "leverage":KELLY,
        "notional_limit":13200
    },
    "RNDRUSDT" :
    {
        "quantity": 0.5,
        "step_size": 0.0001,
        "quantity_step_size": 0.1,
        "leverage":KELLY,
        "notional_limit":35700
    },
    "AGIXUSDT" :
    {
        "quantity": 5,
        "step_size": 0.0001,
        "quantity_step_size": 1,
        "leverage":KELLY,
        "notional_limit":4700
    },
    "1000SHIBUSDT" :
    {
        "quantity": 211,
        "step_size": 0.000001,
        "quantity_step_size": 1,
        "leverage":KELLY,
        "notional_limit":51000
    },
    "DYDXUSDT" :
    {
        "quantity": 2.4,
        "step_size": 0.001,
        "quantity_step_size": 0.1,
        "leverage":KELLY,
        "notional_limit":5100
    },
    "GALAUSDT" :
    {
        "quantity": 110,
        "step_size": 0.00001,
        "quantity_step_size": 1,
        "leverage":KELLY,
        "notional_limit":9300
    },
    "DARUSDT" :
    {
        "quantity": 34.8,
        "step_size": 0.0001,
        "quantity_step_size": 0.1,
        "leverage":KELLY,
        "notional_limit":567
    },
    "BNTUSDT" :
    {
        "quantity": 8,
        "step_size": 0.0001,
        "quantity_step_size": 1,
        "leverage":KELLY,
        "notional_limit":741
    },
    "BONDUSDT" :
    {
        "quantity": 1.7,
        "step_size": 0.001,
        "quantity_step_size": 0.1,
        "leverage":KELLY,
        "notional_limit":466
    },
    "KASUSDT" :
    {
        "quantity": 45,
        "step_size": 0.00001,
        "quantity_step_size": 1,
        "leverage":KELLY,
        "notional_limit":1500
    },
    "MASKUSDT" :
    {
        "quantity": 2,
        "step_size": 0.001,
        "quantity_step_size": 1,
        "leverage":KELLY,
        "notional_limit":3700
    },
    "QTUMUSDT" :
    {
        "quantity": 1.4,
        "step_size": 0.001,
        "quantity_step_size": 0.1,
        "leverage":KELLY,
        "notional_limit":2000
    },
    "XRPUSDT" :
    {
        "quantity": 9.6,
        "step_size": 0.0001,
        "quantity_step_size": 0.1,
        "leverage":KELLY,
        "notional_limit":38400
    },
    "LINKUSDT" :
    {
        "quantity": 1.44,
        "step_size": 0.001,
        "quantity_step_size": 0.01,
        "leverage":KELLY,
        "notional_limit":14400
    },
    "ORDIUSDT" :
    {
        "quantity": 0.2,
        "step_size": 0.001,
        "quantity_step_size": 0.1,
        "leverage":KELLY,
        "notional_limit":44300
    },
    "WLDUSDT" :
    {
        "quantity": 1,
        "step_size": 0.0001,
        "quantity_step_size": 1,
        "leverage":KELLY,
        "notional_limit":81500
    },
    "ETCUSDT" :
    {
        "quantity": 0.71,
        "step_size": 0.001,
        "quantity_step_size": 0.01,
        "leverage":KELLY,
        "notional_limit":14900
    },

}

def buy_future(symbol = "BTCUSDT", quantity = 1):
    try:
        details = client.futures_ticker(symbol=symbol)
        price =float(details["lastPrice"])
        last_price = round_step_size(price, 0.1)
        buy_order = client.futures_create_order(
            symbol=symbol,
            side=Client.SIDE_BUY,
            type=Client.FUTURE_ORDER_TYPE_LIMIT,  # Market order
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=quantity,
            price=last_price,            
            positionSide = "LONG"
        )
        logging.info(f"Buy order placed: {json.dumps(buy_order, indent=2)}")

    except Exception as e:
        logging.info(f"Error placing orders: {e}")
    return buy_order

def buy_future_as_TP(order_info, quantity = 0.0):
    
    global currency_config
    try:
        symbol = order_info["order"]["symbol"]
        current_config = currency_config[symbol]

        if float(quantity) >0:
            logging.info(f"partially filled order, quantity {quantity}")
        else:
            quantity = order_info["order"]["origQty"]
        last_price = float(order_info["order"]["price"])
        order_side = order_info["order"]["side"]
        tp_percentage = 0.75  # Adjust as needed for longs

        take_profit = last_price * (1 - tp_percentage/100)
        take_profit_price = round_step_size(take_profit, current_config["step_size"])
        positionSide = "SHORT"

        buy_order = client.futures_create_order(
            symbol=symbol,
            side=Client.SIDE_BUY,
            type=Client.FUTURE_ORDER_TYPE_LIMIT,  # Market order
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=quantity,
            price=take_profit_price,            
            positionSide = positionSide
            # reduceOnly = True
        )
        logging.info(f"Take Profit order placed: {json.dumps(buy_order, indent=2)}")

    except ValueError as e:
        logging.info("caught value error in buy_future_as_TP")
        return None

    
    except BinanceAPIException as e:
        logging.info(f"Caught BinanceAPIException in buy_future_as_TP. status: {e.status_code}, error code: {e.code}, error message: {e.message}")
        if(e.code == -2021 and e.message =="Order would immediately trigger."):
            try:
                buy_order = client.futures_create_order(
                symbol=symbol,
                side=Client.SIDE_BUY,
                type=Client.FUTURE_ORDER_TYPE_MARKET,  # Market order
                # timeInForce=TIME_IN_FORCE_GTC,
                quantity=quantity,
                # price=take_profit_price,            
                positionSide = positionSide
                # reduceOnly = True
                )
                logging.info(f"Take Profit order placed: {json.dumps(buy_order, indent=2)}")

            except Exception as e:
                logging.info(f"Error placing immediate MARKET TP order: {e}")
                return None
            
            logging.info(f"Take profit MARKET done in buy_future_as_TP : {json.dumps(buy_order, indent=2)}")
            return 1
        else:
            return None
    
    except ClientError as e:
        logging.info(f"Caught ClientError in buy_future_as_TP. status: {e.status_code}, error code: {e.error_code}, error message: {e.error_message}")            
        return None
    
    except Exception as e:
        logging.info(f"Error placing in buy_future_as_TP orders: {e}")
        return 
    return buy_order

def sell_future(symbol = "BTCUSDT", quantity = 0.005):
    try:
        details = client.futures_ticker(symbol=symbol)
        price =float(details["lastPrice"])
        last_price = round_step_size(price, 0.1)
        sell_order = client.futures_create_order(
            symbol=symbol,
            side=Client.SIDE_SELL,
            type=Client.FUTURE_ORDER_TYPE_LIMIT,  # Market order
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=quantity,
            price=50000,
            positionSide = "SHORT"
        )
        logging.info(f"sell order placed: {json.dumps(sell_order, indent=2)}")
    except Exception as e:
        logging.info(f"Error placing orders: {e}")
    return sell_order

def sell_future_withSetprice(price, symbol = "BTCUSDT", quantity = None):
    global currency_config
    current_config = currency_config[symbol]
    # price(currency_config)
    if(quantity == None):
        quantity = current_config["quantity"]
    try:
        
        last_price = round_step_size(price, current_config["step_size"])
        sell_order = client.futures_create_order(
            symbol=symbol,
            side=Client.SIDE_SELL,
            type=Client.FUTURE_ORDER_TYPE_LIMIT,  # Market order
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=quantity,
            price=last_price,
            positionSide = "SHORT"
        )
        logging.info(f"sell order placed: {json.dumps(sell_order, indent=2)}")
    except Exception as e:
        logging.info(f"Error placing orders: {e}")
        return
    return sell_order

def buy_future_with_tpsl(symbol = "BTCUSDT", quantity = 0.005, tp_percentage = 0.75, sl_percentage = 0.3):
    try:
        details = client.futures_ticker(symbol=symbol)
        price =float(details["lastPrice"])

        last_price = round_step_size(price, 0.1)
        buy_order = client.futures_create_order(
            symbol=symbol,
            side=Client.SIDE_BUY,
            type=Client.FUTURE_ORDER_TYPE_LIMIT,  # Market order
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=quantity,
            price=last_price
        )
        logging.info(f"Buy order placed: {json.dumps(buy_order, indent=2)}")

        # Calculate Take Profit price
        take_profit = float(last_price) * (1 + tp_percentage/100)
        take_profit_price = round_step_size(take_profit, 0.1)

        tp_order = client.futures_create_order(
            symbol=symbol,
            side=Client.SIDE_SELL,
            type=Client.FUTURE_ORDER_TYPE_TAKE_PROFIT,
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=quantity,
            price=take_profit_price,
            stopPrice=take_profit_price,
            reduceOnly = True
        )
        logging.info(f"Take Profit order placed: {json.dumps(tp_order, indent=2)}")

        # Calculate Stop Loss price
        stop_loss = float(last_price) * (1 - sl_percentage/100)
        stop_loss_price = round_step_size(stop_loss, 0.1)

        sl_order = client.futures_create_order(
            symbol=symbol,
            side=Client.SIDE_SELL,
            type=FUTURE_ORDER_TYPE_STOP_MARKET,  # Use STOP_MARKET or adjust depending on your strategy
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=quantity,
            stopPrice=stop_loss_price,
            reduceOnly = True
        )
        logging.info(f"Stop Loss order placed: {json.dumps(sl_order, indent=2)}")
    except Exception as e:
        logging.info(f"Error placing orders: {e}")

def sell_future_with_tpsl(symbol = "BTCUSDT", quantity = 0.005, tp_percentage = 5, sl_percentage = 2):
    try:
        details = client.futures_ticker(symbol=symbol)
        price =float(details["lastPrice"])

        last_price = round_step_size(price, 0.1)
        sell_order = client.futures_create_order(
            symbol=symbol,
            side=Client.SIDE_SELL,
            type=Client.FUTURE_ORDER_TYPE_LIMIT,  # Market order
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=quantity,
            price=last_price
        )
        logging.info(f"sell order placed: {json.dumps(sell_order, indent=2)}")

        # Calculate Take Profit price
        take_profit = float(last_price) * (1 - tp_percentage/100)
        take_profit_price = round_step_size(take_profit, 0.1)
        logging.info(take_profit_price)
        # time.sleep(5)

        tp_order = client.futures_create_order(
            symbol=symbol,
            side=Client.SIDE_BUY,
            type=Client.FUTURE_ORDER_TYPE_TAKE_PROFIT,
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=quantity,
            price=take_profit_price,
            stopPrice=take_profit_price,
            reduceOnly = True

        )
        logging.info(f"Take Profit order placed: {json.dumps(tp_order, indent=2)}")

        # Calculate Stop Loss price
        stop_loss = float(last_price) * (1 + sl_percentage/100)
        stop_loss_price = round_step_size(stop_loss, 0.1)
        logging.info(stop_loss_price)
        # time.sleep(5)

        sl_order = client.futures_create_order(
            symbol=symbol,
            side=Client.SIDE_BUY,
            type=FUTURE_ORDER_TYPE_STOP_MARKET,  # Use STOP_MARKET or adjust depending on your strategy
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=quantity,
            stopPrice=stop_loss_price,
            reduceOnly = True
        )
        
        logging.info(f"Stop Loss order placed: {json.dumps(sl_order, indent=2)}")
    except Exception as e:
        logging.info(f"Error placing orders: {e}")

def create_tp_order(order_info, quantity = 0.0):
    global currency_config
    try:
        symbol = order_info["order"]["symbol"]
        if float(quantity) >0:
            logging.info(f"partially filled order, quantity {quantity}")
        else:
            quantity = order_info["order"]["origQty"]
        last_price = float(order_info["order"]["price"])
        order_side = order_info["order"]["side"]
        tp_percentage = 0.75  # Adjust as needed for longs


        # Calculate Take Profit price
        if order_side == Client.SIDE_BUY:
            take_profit = last_price * (1 + tp_percentage/100)
            positionSide = "LONG"
        else:  # OrderSide.SELL
            take_profit = last_price * (1 - tp_percentage/100)
            positionSide = "SHORT"

        take_profit_price = round_step_size(take_profit, currency_config[symbol]["step_size"])

        tp_order = client.futures_create_order(
            symbol=symbol,
            side=Client.SIDE_SELL if order_side == Client.SIDE_BUY else Client.SIDE_BUY,
            type=Client.FUTURE_ORDER_TYPE_TAKE_PROFIT,
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=quantity,
            price=take_profit_price,
            stopPrice=last_price,
            # reduceOnly=True,
            positionSide = positionSide
        )
        logging.info(f"Take Profit order placed: {json.dumps(tp_order, indent=2)}")
        return tp_order 


    except ValueError as e:
        logging.info("caught value error in create_tp_order")
        return None
    
    except BinanceAPIException as e:
        logging.info(f"Caught BinanceAPIException in create_tp_order. status: {e.status_code}, error code: {e.code}, error message: {e.message}")
        if(e.code == -2021 and e.message =="Order would immediately trigger."):
            try:
                tp_order = client.futures_create_order(
                    symbol=symbol,
                    side=Client.SIDE_SELL if order_side == Client.SIDE_BUY else Client.SIDE_BUY,
                    type=Client.FUTURE_ORDER_TYPE_MARKET,
                    # timeInForce=TIME_IN_FORCE_GTC,
                    quantity=quantity,
                    # price=take_profit_price,
                    # stopPrice=last_price,
                    # reduceOnly=True,
                    positionSide = positionSide
                )

            except Exception as e:
                logging.info(f"Error placing immediate MARKET TP order: {e}")
                return None
            
            logging.info(f"Take profit MARKET done: {json.dumps(tp_order, indent=2)}")
            return 1
        else:
            return None

    

    except ClientError as e:
        logging.info(f"Caught ClientError in create_tp_order. status: {e.status_code}, error code: {e.error_code}, error message: {e.error_message}")            
        return None
    
    except Exception as e:
        logging.info(f"Error placing TP order: {e}")
        return None

def create_sl_order(order_info, quantity = 0.0):
    global currency_config
    try:
        symbol = order_info["order"]["symbol"]

        if float(quantity) >0:
            logging.info(f"partially filled order, quantity {quantity}")
        else:
            quantity = order_info["order"]["origQty"]
        last_price = float(order_info["order"]["price"])
        order_side = order_info["order"]["side"]
        sl_percentage = 0.3  # Adjust as needed for longs

        # Calculate Stop Loss price
        if order_side == Client.SIDE_BUY:
            stop_loss = last_price * (1 - sl_percentage/100)
            positionSide = "LONG"

        else:  # OrderSide.SELL
            stop_loss = last_price * (1 + sl_percentage/100)
            positionSide = "SHORT"


        stop_loss_price = round_step_size(stop_loss, currency_config[symbol]["step_size"])

        sl_order = client.futures_create_order(
            symbol=symbol,
            side=Client.SIDE_SELL if order_side == Client.SIDE_BUY else Client.SIDE_BUY,
            type=FUTURE_ORDER_TYPE_STOP_MARKET,  # Adjust if needed
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=quantity,
            stopPrice=stop_loss_price,
            # reduceOnly=True,
            positionSide = positionSide
        )
        logging.info(f"Stop Loss order placed: {json.dumps(sl_order, indent=2)}")
        return sl_order
    
    except ValueError as e:
        logging.info("caught value error in create_sl_order")
        return None

    except ClientError as e:
        logging.info(f"Caught ClientError in create_sl_order. status: {e.status_code}, error code: {e.error_code}, error message: {e.error_message}")            
        return None
    
        
    except BinanceAPIException as e:
        logging.info(f"Caught BinanceAPIException in create_sl_order. status: {e.status_code}, error code: {e.code}, error message: {e.message}")
        if(e.code == -2021 and e.message =="Order would immediately trigger."):
            try:
                sl_order = client.futures_create_order(
                symbol=symbol,
                side=Client.SIDE_SELL if order_side == Client.SIDE_BUY else Client.SIDE_BUY,
                type=FUTURE_ORDER_TYPE_MARKET,  # Adjust if needed
                # timeInForce=TIME_IN_FORCE_GTC,
                quantity=quantity,
                # stopPrice=stop_loss_price,
                # reduceOnly=True,
                positionSide = positionSide
                )

            except Exception as e:
                logging.info(f"Error placing immediate MARKET SL order: {e}")
                return None
            
            logging.info(f"Stop Loss Market done: {json.dumps(sl_order, indent=2)}")
            return 1
        else:
            return None
    
    
    except Exception as e:
        logging.info(f"Error placing SL order: {e}")
        return None

def cancel_order(order_data):
    try:
        order_id = order_data["orderId"]  # Assuming orderId is available
        result = client.futures_cancel_order(symbol=order_data["symbol"], orderId=order_id)
        logging.info(f"Order canceled: {json.dumps(result, indent=2)}")
        return result
    except Exception as e:
        logging.info(f"Error canceling order: {e}")
        return None
    
def get_order_status(orderId, symbol = "BTCUSDT"  ):
    try:
        order_status = client.futures_get_order(symbol=symbol, orderId=orderId)
        logging.debug(f"Order status: {json.dumps(order_status, indent=2)}")
        return order_status
    except Exception as e:
        logging.error(f"Error in fetching order status order: {e}, orderid:{orderId}")
        return None




    
# def amend_order(order,quantity = 0, **kwargs):
    #not working Function missing
# def amend_order(order,quantity):
#     try:
#         # Extract necessary order information
#         symbol = order["symbol"]
#         order_id = order["orderId"]

#         # Amend the order using the Binance API client
#         result = client.futures_amend_order(
#             symbol=symbol,
#             orderId=order_id,
#             quantity=quantity
#             # **kwargs  # Pass additional arguments for modification
#         )
#         logging.info(f"Order amended: {json.dumps(result, indent=2)}")
#         return result
#     except Exception as e:
#         logging.info(f"Error amending order: {e}")
#         return None