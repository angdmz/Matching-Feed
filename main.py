import asyncio
import websockets
import cbpro
import time
from decimal import Decimal

WEBSOCKET_ENDPOINT = "wss://ws-feed-public.sandbox.pro.coinbase.com"
WEBSOCKET_PROD_ENDPOINT = "wss://ws-feed.pro.coinbase.com"
TRADING_PAIRS = ["BTC-USD", "ETH-USD", "ETH-BTC"]
DATA_POINTS_COUNT = 200
MATCH_CHANNEL = "matches"


class CountingWebsocketClient(cbpro.WebsocketClient):
    def on_open(self):
        print("Let's get this started!")
    def on_message(self, message):
      if 'price' in message and 'type' in message:
        self.data_points[message['product_id']].append(message)
        if len(self.data_points[message['product_id']]) > self.message_cap:
          del self.data_points[message['product_id']][0]

    def on_close(self):
        print("-- Goodbye! --")

    def calculate_vwap(self, product, stream_out):
      numerator = 0
      denominator = 0
      for point in self.data_points[product]:
        numerator += Decimal(point["price"]) * Decimal(point["size"])
        denominator += Decimal(point["size"])
      vwap = numerator/denominator if denominator > 0 else 0
      stream_out(vwap)
      return vwap

    @staticmethod
    def create_websocket_client(endpoint, products, channels, message_cap):
      client = CountingWebsocketClient()
      client.channels = channels
      client.url = endpoint
      client.products = products
      client.message_cap = message_cap
      client.data_points = {product_id: [] for product_id in products}
      return client

ws_client = CountingWebsocketClient.create_websocket_client(WEBSOCKET_ENDPOINT, TRADING_PAIRS, [MATCH_CHANNEL], DATA_POINTS_COUNT)
ws_client.start()
print(ws_client.url, ws_client.products)
while True:
    for product in TRADING_PAIRS:
      vwap = ws_client.calculate_vwap(product, print)
    print("sleeping")
    time.sleep(1)

ws_client.close()
