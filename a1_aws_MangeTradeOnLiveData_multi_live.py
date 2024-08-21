import json
from binanceApiEndpoints import *
import logging
from binance.lib.utils import config_logging
from binance.um_futures import UMFutures
from binance.websocket.um_futures.websocket_client import UMFuturesWebsocketClient
from config import *
from collections import defaultdict

log_file_path = "LiveManger.log"
config_logging(logging, logging.INFO, log_file_path)

AlreadyShort_Dictionary = {
    "btcusdt": 0,
    "ethusdt":0,
    "dogeusdt":0,
    "bnbusdt":0,
    "fetusdt":0,
    "rndrusdt":0,
    "agixusdt":0,
    "dydxusdt":0,
    "1000shibusdt":0,
    "galausdt":0,
    "xrpusdt":0,
    "qtumusdt":0,
    "maskusdt":0,
    "kasusdt":0,
    "bntusdt":0,
    "bondusdt":0,
    "darusdt":0,
    "linkusdt":0,
    "wldusdt":0,
    "etcusdt":0,
    "ordiusdt":0,
    "opusdt":0
}
ordersShort = defaultdict(dict)  # Dictionary to track orders and TP/SL orders

def on_error1(ws, error):
    print("on_error1")
    print(f"WebSocket error: {error}")
    print(f"Error type: {type(error)}")
    print(f"Error message: {error.args}")

def amend_order(order,quantity):
    global currency_config
    try:
        # Extract necessary order information
        symbol = order["symbol"]
        order_id = order["orderId"]
        side = order["side"]
        price = float(order["price"])
        if(price == 0.0):
            price = float(order["stopPrice"])

        round_price = round_step_size(price, currency_config[symbol]["step_size"])
        # round_qty = round_step_size(quantity, currency_config[symbol]["quantity_step_size"])

        # Amend the order using the Binance API client
        response = Umclient.modify_order(
            symbol=symbol,
            orderId=order_id,
            quantity=quantity,
            side=side,
            price=round_price
            
            )
        
        # print(f"Order amended: {json.dumps(response, indent=2)}")
        logging.info(f"Order amended: {json.dumps(response)}")

        return response
    except ClientError as e:
        logging.error(f"Error amending order: {e}")
        return None
    
def message_handler(_, message):
    global AlreadyShort_Dictionary

    data = json.loads(message)
    logging.info(f"message: {json.dumps(data, indent=2)}")

    if "id" in data:
        return

    if data["e"] == "listenKeyExpired":
        response = Umclient.new_listen_key()
        logging.info("Listen key : {}".format(response["listenKey"]))
        ws_client.user_data(
        listen_key=response["listenKey"],
        id=1,
         )

    if data["e"] == "ORDER_TRADE_UPDATE":
            
            clientOrderId = data["o"]["c"]
            currency = data["o"]["s"] 
            currency = str(currency).lower()
            order_info = None

            if data["o"]["X"] == "NEW" and data["o"]["ot"] == "LIMIT" and data["o"]["ps"] == "SHORT" and data["o"]["S"] == "SELL":
                logging.info(f'data["o"]["X"] == "NEW" and data["o"]["ot"] == "LIMIT" and data["o"]["ps"] == "SHORT" and data["o"]["S"] == "SELL"')
                order_info ={
                            "orderId": data["o"]["i"],
                            "symbol": data["o"]["s"],
                            "status": data["o"]["X"],
                            "clientOrderId": data["o"]["c"],
                            "price": data["o"]["p"],
                            "avgPrice": data["o"]["ap"],
                            "origQty": data["o"]["q"],
                            "executedQty": data["o"]["l"],
                            "cumQty": data["o"]["z"],
                            "cumQuote": "0.00000",
                            "timeInForce": data["o"]["f"],
                            "type": data["o"]["o"],
                            "reduceOnly": data["o"]["R"],
                            "closePosition": data["o"]["cp"],
                            "side": data["o"]["S"],
                            "positionSide": data["o"]["ps"],
                            "stopPrice": data["o"]["sp"],
                            "workingType": data["o"]["wt"],
                            "priceProtect": data["o"]["pP"],
                            "origType": data["o"]["ot"],
                            "priceMatch": data["o"]["pm"],
                            "selfTradePreventionMode": data["o"]["V"],
                            "goodTillDate": data["o"]["gtd"],
                            "updateTime": data["o"]["T"]
                            }

                ordersShort[currency][clientOrderId] = {
                    "order": order_info,  
                    "tp": None,
                    "sl": None,
                    "partial_closed" : None,
                    "partial" : None
                }
                logging.info(f"order stored:{ ordersShort[currency][clientOrderId]} for currency:{currency}, clientorderid:{clientOrderId}")

            if data["o"]["X"] == "FILLED" and data["o"]["ot"] == "LIMIT":
                logging.info(f"Inside data['o']['X'] == 'FILLED' and data['o']['ot'] == 'LIMIT'")
                if data["o"]["ps"] == "SHORT" and data["o"]["S"] == "BUY":
                    logging.info(f"Inside data['o']['ps'] == 'SHORT' and data['o']['S'] == 'BUY'")
                    logging.info(f"If non partial TAKE_PROFIT, need to Cancel the SL, and RESET/clear the respective DS.")
                    logging.info(f"If partial TAKE_PROFIT, need to Cancel the SL. RESET/clear of the respective DS NOT REQUIRED.")

                    logging.info(f"fetching  the first entry of Short DS.")
                    order_info = list(ordersShort[currency].values())[0]

                    if order_info:
                        logging.info(f"fetched the first entry of Short DS. Entry FOUND :{order_info}")
                        other_order = order_info["sl"] 
                        if(other_order):
                            logging.info(f"Entry has SL. Cancelling it.")
                            canceled_order = cancel_order(other_order)
                            logging.info(f"SL Cancelled. Details:{canceled_order}")
                        if(order_info["partial"] == 1):
                            logging.info(f"inside order_info['partial'] == 1, After SL cancellation,SHORT,FILLED&TAKE_PROFIT ")
                            logging.info(f"updating partial_closed for the filled quantity, Deleteing TP/SL from the short DS. Letting the remaining limit to still run.")                            
                            order_info["sl"] = None
                            order_info["tp"] = None
                            if(order_info["partial_closed"]):
                                logging.info(f"adding {data['o']['z']} to partial_closed:{order_info['partial_closed']}")
                                order_info["partial_closed"] = float(order_info["partial_closed"]) +  float(data["o"]["z"])
                                logging.info(f"partial_closed:{order_info['partial_closed']}")
                            else:
                                order_info["partial_closed"] =  float(data["o"]["z"]) 
                                logging.info(f"partial_closed:{order_info['partial_closed']}")
                        else:
                            logging.info(f"non partial TAKE_PROFIT, AlreadyShort = 0 and RESET/clear the Short DS Done.")
                            del ordersShort[currency]
                            AlreadyShort_Dictionary[currency] = 0

                elif data["o"]["ps"] == "SHORT" and data["o"]["S"] == "SELL":
                    order_info = ordersShort[currency][clientOrderId]

                    if order_info is None:
                        logging.error(f"order details not found in the short DS, storing into ds")
                        
                        order_info ={
                            "orderId": data["o"]["i"],
                            "symbol": data["o"]["s"],
                            "status": data["o"]["X"],
                            "clientOrderId": data["o"]["c"],
                            "price": data["o"]["p"],
                            "avgPrice": data["o"]["ap"],
                            "origQty": data["o"]["q"],
                            "executedQty": data["o"]["l"],
                            "cumQty": data["o"]["z"],
                            "cumQuote": "0.00000",
                            "timeInForce": data["o"]["f"],
                            "type": data["o"]["o"],
                            "reduceOnly": data["o"]["R"],
                            "closePosition": data["o"]["cp"],
                            "side": data["o"]["S"],
                            "positionSide": data["o"]["ps"],
                            "stopPrice": data["o"]["sp"],
                            "workingType": data["o"]["wt"],
                            "priceProtect": data["o"]["pP"],
                            "origType": data["o"]["ot"],
                            "priceMatch": data["o"]["pm"],
                            "selfTradePreventionMode": data["o"]["V"],
                            "goodTillDate": data["o"]["gtd"],
                            "updateTime": data["o"]["T"]
                            }
                        ordersShort[currency][clientOrderId] = {
                            "order": order_info, 
                            "tp": None,
                            "sl": None,                        
                            "partial_closed" : None,
                            "partial" : None
                        }
                        logging.error(f"stored:{order_info} for {clientOrderId} and currency {currency}")

                    if order_info and order_info["tp"] is None and order_info["sl"] is None:
                        logging.info(f"order details found {order_info} for id {clientOrderId}in the short DS, TP & SL are None. creating tp")
                        if( order_info["partial_closed"]):
                            logging.info(f"Found 'partial_closed' filled. Creating TP/SL only for the quantity from 'l'")
                            tp_order = buy_future_as_TP(order_info, data["o"]["l"])
                            if(tp_order ==  1):
                                logging.info(f"TP got MARKET, As this is 'Limit' 'Filled' with TP hit, clearing short DS, marking AlreadyShort = 0")
                                del ordersShort[currency]
                                AlreadyShort_Dictionary[currency] = 0
                            else:
                                logging.info(f"TP placed succefully. Details:{tp_order}")
                                sl_order = create_sl_order(order_info, data["o"]["l"])
                                if(sl_order == 1 ):
                                    logging.info(f"SL got MARKET, As this is 'Limit' 'Filled' with SL hit, going to cancel the TP clearing short DS, marking AlreadyShort = 0")
                                    canceled = cancel_order(tp_order)
                                    logging.info(f"TP cancelled. Details:{canceled}")
                                    del ordersShort[currency]
                                    AlreadyShort_Dictionary[currency] = 0
                                else:
                                    logging.info(f"SL placed succefully. Details:{sl_order}. Updating DS with SL and TP details('partial_closed' is true)")
                                    ordersShort[currency][clientOrderId]["tp"] = tp_order
                                    ordersShort[currency][clientOrderId]["sl"] = sl_order 

                        else:
                            tp_order = buy_future_as_TP(order_info)                             
                            if(tp_order == 1):
                                logging.info(f"TP got MARKET, As this is 'Limit' 'Filled' with TP hit, clearing DS, marking AlreadyShort = 0")
                                del ordersShort[currency]
                                AlreadyShort_Dictionary[currency] = 0
                            else:
                                logging.info(f"TP placed succefully. Details:{tp_order}")
                                sl_order = create_sl_order(order_info) 
                                if(sl_order == 1):
                                    logging.info(f"SL got MARKET, As this is 'Limit' 'Filled' with SL hit, going to cancel the TP clearing DS, marking AlreadyShort = 0")
                                    canceled = cancel_order(tp_order)
                                    logging.info(f"TP cancelled. Details:{canceled}")
                                    del ordersShort[currency]
                                    AlreadyShort_Dictionary[currency] = 0
                                else:
                                    logging.info(f"SL placed succefully. Details:{sl_order}. Updating DS with SL and TP details")
                                    ordersShort[currency][clientOrderId]["tp"] = tp_order
                                    ordersShort[currency][clientOrderId]["sl"] = sl_order

                    elif order_info["tp"] and order_info["sl"]:
                        logging.info(f"order details found {order_info} for id {clientOrderId}in the short DS, TP & SL are also filled.")
                        if(order_info["partial_closed"]):
                            logging.info(f"partial_closed is filled, subtracting partial_closed: {order_info['partial_closed']} from z: {data['o']['z']}")
                            qty = float(data["o"]["z"]) - float(order_info["partial_closed"])
                        else:
                            logging.info(f"partial_closed is not filled, ammending tp for qty= z: {data['o']['z']}")
                            qty = float(data["o"]["z"]) 

                        tp_old_order = order_info["tp"] 
                        ameneded_order = amend_order(tp_old_order ,qty )
                        logging.info(f"TP ameneded. Details:{ameneded_order}")
                        sl_old_order = order_info["sl"] 
                        if sl_old_order:
                            logging.info(f"Cancelling sl, for placing with new qty")
                            canceled_order = cancel_order(sl_old_order)
                            logging.info(f"canceled_order sl:{canceled_order}")
                        new_sl_order = create_sl_order(order_info=order_info, quantity=qty)
                        if(new_sl_order == 1):
                            logging.info(f"SL got market, as this is 'FILLED', cancel tp just placed, update  clearing DS:{ordersShort},  marking AlreadyShort = 0:{AlreadyShort_Dictionary}")
                            canceled = cancel_order(tp_order)  
                            logging.info(f"TP cancelled. Details:{canceled}")
                            del ordersShort[currency]
                            AlreadyShort_Dictionary[currency] = 0
                            logging.info(f"updated DS:{ordersShort},  marked AlreadyShort = 0:{AlreadyShort_Dictionary}")

                        else:
                            order_info["sl"] = new_sl_order
                            order_info["tp"] = ameneded_order
                            order_info["partial"] = None
                            logging.info(f"SL placed succefully. Details:{new_sl_order}. Updating DS with new tp/SL details: {ordersShort}, marked partial to None")

                        # ameneded_order = amend_order(sl_old_order, qty )
                        # logging.info(f"sl ameneded. Details:{ameneded_order}")

            elif data["o"]["X"] == "FILLED" and data["o"]["ot"] == "STOP_MARKET":
                logging.info(f"Inside data['o']['X'] == 'FILLED' and data['o']['ot'] == 'STOP_MARKET'")
                logging.info(f"If non partial STOP_MARKET, need to Cancel the TP, and RESET/clear the respective DS.")
                logging.info(f"If partial STOP_MARKET, need to Cancel the TP. RESET/clear of the respective DS NOT REQUIRED.")

                if data["o"]["ps"] == "SHORT":
                    logging.info(f"Inside data['o']['ps'] == 'SHORT'")
                    logging.info(f"fetching  the first entry of Short DS.")
                    order_info = list(ordersShort[currency].values())[0]

                    if order_info:
                        logging.info(f"fetched the first entry of Short DS. Entry FOUND")
                        other_order = order_info["tp"] 
                        if(other_order):
                            logging.info(f"Entry has TP. Cancelling it.")
                            canceled_order = cancel_order(other_order)
                            logging.info(f"TP Cancelled. Details:{canceled_order}")
                        if(order_info["partial"] == 1):
                            logging.info(f"inside order_info['partial'] == 1, After TP cancellation,SHORT,FILLED&STOP_MARKET ")
                            logging.info(f"updating partial_closed for the filled quantity, Deleteing TP/SL from the short DS. Letting the remaining limit to still run.")
                            order_info["sl"] = None
                            order_info["tp"] = None
                            if(order_info["partial_closed"]):
                                logging.info(f"adding {data['o']['z']} to partial_closed:{order_info['partial_closed']}")
                                order_info["partial_closed"] = float(order_info["partial_closed"]) +  float(data["o"]["z"])
                                logging.info(f"partial_closed:{order_info['partial_closed']}")
                            else:
                                order_info["partial_closed"] =  float(data["o"]["z"]) 
                                logging.info(f"partial_closed:{order_info['partial_closed']}")
                        else:
                            logging.info(f"non partial STOP_MARKET, AlreadyShort = 0 and RESET/clear the Short DS Done.")
                            del ordersShort[currency]
                            AlreadyShort_Dictionary[currency] = 0
                
                if order_info is None:
                    logging.error(f"Main order not found for filled SL ordersShort DS:{ordersShort}.")
        
            elif data["o"]["X"] == "CANCELED" and data["o"]["ot"] == "LIMIT":
                logging.info(f"Inside data['o']['X'] == 'CANCELED' and data['o']['ot'] == 'LIMIT'")

                if data["o"]["ps"] == "SHORT" and data["o"]["S"] == "SELL" :
                    logging.info(f"Inside data['o']['ps'] == 'SHORT' and data['o']['S'] == 'SELL'")
                    logging.info(f"Have to cancel TP/sl if placed for the limit orders and reset the DS and the Variables.")
                    logging.info(f"Cancelling orders short.")
                    order_info = list(ordersShort[currency].values())[0]
                    if order_info:
                        logging.info(f"found order_info for currency: {currency}.")
                        other_order = order_info["tp"] 
                        if other_order:
                            logging.info(f"Cancelling tp.")
                            canceled_order = cancel_order(other_order)
                            logging.info(f"canceled_order tp:{canceled_order}")
                        other_order = order_info["sl"] 
                        if other_order:
                            logging.info(f"Cancelling sl.")
                            canceled_order = cancel_order(other_order)
                            logging.info(f"canceled_order sl:{canceled_order}")
                        logging.info(f"AlreadyShort = 0, Short DS cleared/RESET.")
                        del ordersShort[currency]
                        AlreadyShort_Dictionary[currency] = 0

                if order_info is None:
                    logging.error(f"No orders found from the bot DS. ordersShort DS:{ordersShort}")
                   
            elif data["o"]["X"] == "PARTIALLY_FILLED" and data["o"]["ot"] == "LIMIT":
                logging.info(f"going for patiral tp/sl placement")
                # Need 1: Place TP/SL orders
                if data["o"]["ps"] == "SHORT" and data["o"]["S"] == "SELL":
                    order_info = ordersShort[currency][clientOrderId]
                    if order_info is None:
                        logging.error(f"order details not found in the short DS, storing into ds")
                        
                        order_info ={
                            "orderId": data["o"]["i"],
                            "symbol": data["o"]["s"],
                            "status": data["o"]["X"],
                            "clientOrderId": data["o"]["c"],
                            "price": data["o"]["p"],
                            "avgPrice": data["o"]["ap"],
                            "origQty": data["o"]["q"],
                            "executedQty": data["o"]["l"],
                            "cumQty": data["o"]["z"],
                            "cumQuote": "0.00000",
                            "timeInForce": data["o"]["f"],
                            "type": data["o"]["o"],
                            "reduceOnly": data["o"]["R"],
                            "closePosition": data["o"]["cp"],
                            "side": data["o"]["S"],
                            "positionSide": data["o"]["ps"],
                            "stopPrice": data["o"]["sp"],
                            "workingType": data["o"]["wt"],
                            "priceProtect": data["o"]["pP"],
                            "origType": data["o"]["ot"],
                            "priceMatch": data["o"]["pm"],
                            "selfTradePreventionMode": data["o"]["V"],
                            "goodTillDate": data["o"]["gtd"],
                            "updateTime": data["o"]["T"]
                            }
                        ordersShort[currency][clientOrderId] = {
                            "order": order_info,  
                            "tp": None,
                            "sl": None,                        
                            "partial_closed" : None,
                            "partial" : None
                        }
                        logging.error(f"stored:{order_info} for {clientOrderId} and currency {currency}")

                    if order_info and order_info["tp"] is None and order_info["sl"] is None:
                        if( order_info["partial_closed"]):
                            logging.info(f"order details found {order_info} for id {clientOrderId}in the short DS, TP & SL are None.")
                            logging.info(f"Found 'partial_closed' filled. Creating TP/SL only for the quantity from 'l' qty:{data['o']['l']}")
                            tp_order = buy_future_as_TP(order_info, data["o"]["l"])
                            if(tp_order ==  1):
                                logging.info(f"TP got MARKET, As this is 'PARTIALLY_FILLED', adding this quantity to partial_closed")
                                order_info["partial_closed"] =  float(order_info["partial_closed"]) + float(data["o"]["l"])
                            else:
                                logging.info(f"TP placed succefully. Details:{tp_order}")
                                sl_order = create_sl_order(order_info, data["o"]["l"])
                                if(sl_order == 1 ):
                                    logging.info(f"SL got MARKET, As this is 'PARTIALLY_FILLED' , adding this quantity to partial_closed, Also canceling respective tp ")
                                    canceled = cancel_order(tp_order)
                                    logging.info(f"TP cancelled. Details:{canceled}")
                                    order_info["partial_closed"] =  float(order_info["partial_closed"] )+ float(data["o"]["l"])
                                else:
                                    logging.info(f"SL placed succefully. Details:{sl_order}. Updating DS with SL and TP details('partial_closed' is true & partial = 1 )")
                                    order_info["tp"] = tp_order
                                    order_info["sl"] = sl_order 
                                    order_info["partial"] = 1
                        else:
                            logging.info(f"This is the first time this order is geting filled as, neither we have tp/sl for it, nor we have PARTIALLY_FILLED qty")
                            tp_order = buy_future_as_TP(order_info, data["o"]["z"]) 
                            if(tp_order == 1):
                                logging.info(f"TP got MARKET, As this is 'PARTIALLY_FILLED', updating partial_closed with this qty:{data['o']['z']}")                                                                   
                                order_info["partial_closed"] = float(data["o"]["z"])
                            else:
                                logging.info(f"TP placed succefully. Details:{tp_order}")
                                sl_order = create_sl_order(order_info, data["o"]["z"]) 
                                if(sl_order == 1):
                                    logging.info(f"SL got MARKET, As this is 'PARTIALLY_FILLED', updating partial_closed with this qty:{data['o']['z']}Also cancelling just placed TP ")
                                    canceled = cancel_order(tp_order)  
                                    logging.info(f"TP cancelled. Details:{canceled}")
                                    order_info["partial_closed"] = float(data["o"]["z"])
                                else:
                                    logging.info(f"SL placed succefully. Details:{sl_order}. Updating DS with SL and TP details, Also marking 'partial'= 1")
                                    order_info["tp"] = tp_order
                                    order_info["sl"] = sl_order
                                    order_info["partial"] = 1
                    elif order_info["tp"] and order_info["sl"]:
                        logging.info(f"This is the consequitive time this order is geting filled as, we ALREADY have tp/sl for it, we need to check if we have")
                        logging.info(f"partial_closed and it has to be subtracted from 'z'/ or we could add 'l' to the existing tp quantity . Opted addidtion for faster computation")
                        logging.info(f"if not partial_closed, modify orders for  qty'z'")
                        if(order_info["partial_closed"]):
                            qty = float(order_info["tp"]["origQty"]) + float(data["o"]["l"])
                            logging.info(f"partial_closed is filled, add TP/sl origQty: {order_info['tp']['origQty']} to  l: {data['o']['l']}")
                        else:
                            qty = float(data["o"]["z"]) 
                            logging.info(f"partial_closed is not filled, ammending tp for qty= z: {data['o']['z']}")                        
                        tp_old_order = order_info["tp"]                         
                        ameneded_order = amend_order(tp_old_order, qty )
                        logging.info(f"TP ameneded. Details:{ameneded_order}")
                        sl_old_order = order_info["sl"] 
                        if sl_old_order:
                            logging.info(f"Cancelling sl, for placing with new qty sl")
                            canceled_order = cancel_order(sl_old_order)
                            logging.info(f"canceled_order sl:{canceled_order}")
                        new_sl_order = create_sl_order(order_info=order_info, quantity=qty)
                        if(new_sl_order == 1):
                            logging.info(f"SL got market, as this is 'PARTIALLY_FILLED', cancel tp just placed, update order_info tp/sl partial_closed with this qty:{qty}")
                            canceled = cancel_order(tp_order)  
                            logging.info(f"TP cancelled. Details:{canceled}")
                            order_info["partial_closed"] = float(data["o"]["z"])
                            order_info["sl"] = None
                            order_info["tp"] = None
                        else:
                            logging.info(f"SL placed succefully. Details:{new_sl_order}. Updating DS with new TP/SL details")
                            order_info["sl"] = new_sl_order
                            order_info["tp"] = ameneded_order

                        # ameneded_order = amend_order(sl_old_order, qty )
                        # logging.info(f"new sl placed. Details:{ameneded_order}")

def on_close(ws, error):
    print("on_close")
    logging.info("on_close")
    print(f"WebSocket error: {error}")
    print(f"Error type: {type(error)}")
    print(f"Error message: {error.args}")

Umclient = UMFutures(api_key_futures_real, api_secret_futures_real)
response = Umclient.new_listen_key()
logging.info("Listen key : {}".format(response["listenKey"]))

ws_client = UMFuturesWebsocketClient(stream_url = "wss://fstream.binance.com", on_message=message_handler, on_error=on_error1, on_close=on_close)
ws_client.user_data(
    listen_key=response["listenKey"],
    id=1,
)#subscribing to user data stream

i = 1
while(1):
    if(i == 1):
        print("working")
        i = i +1


logging.info(f"closing socket")

ws_client.stop()
logging.info(f"stopping manager")

exit(0)




