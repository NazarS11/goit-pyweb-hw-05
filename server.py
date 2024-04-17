import asyncio
import aiofiles
from aiopath import AsyncPath
import logging
import websockets
import names
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
from datetime import datetime
from main import main as fetch_exchange_rates



logging.basicConfig(level=logging.INFO)


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            await asyncio.gather(*(client.send(message) for client in self.clients))

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distribute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    def format_exchange_data(self, data):
        formatted_text = "Exchange Rates:<br>"
        for entry in data:
            date = list(entry.keys())[0]
            rates = entry[date]
            formatted_text += f"Date: {date}<br>"
            for currency, details in rates.items():
                formatted_text += f"{currency} - Sale: {details['sale']}, Purchase: {details['purchase']}<br>"
            formatted_text += "<br>"
        return formatted_text
    
    async def log_command(self, message, date):
        log_path = AsyncPath("exchange_commands.log")
        async with aiofiles.open(log_path, mode='a') as log_file:
            await log_file.write(f"{date}: {message}\n")

    async def distribute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message.startswith("exchange"):
                if len(message.split()) == 1 and message.split()[0] == "exchange":
                    days = 1
                elif len(message.split()) == 2 and message.split()[1].isdigit():
                    days = int(message.split()[1])
                    if days < 1 or days > 10:
                        await ws.send("Error: Number of days should be between 1 and 10.")
                        continue
                else:
                    await ws.send("Invalid command format. Use 'exchange' or 'exchange &ltdays&gt'")
                    continue

                try:
                    command_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    await self.log_command(message, command_date)
                    results = await fetch_exchange_rates(days, ['USD', 'EUR'])
                    formatted_results = self.format_exchange_data(results)
                    await self.send_to_clients(formatted_results)
                except Exception as e:
                    await ws.send(f"An error occurred: {str(e)}")
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())
