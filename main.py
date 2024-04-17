from datetime import datetime, timedelta
import aiohttp
import asyncio
import sys
import json


async def ExchangeRatesAPI(date):
    
    url = "https://api.privatbank.ua/p24api/exchange_rates?json&date="
    url = url + date.strftime('%d.%m.%Y')

    async with aiohttp.ClientSession() as session:

        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                raise Exception(f"Error fetching data for {date}: {response.status}")

def process_data(data, currencies):
    
    result = {}
    for rate in data['exchangeRate']    :
        if rate['currency'] in currencies:
            result[rate['currency']] = {
                'sale': rate.get('saleRate', rate.get('saleRateNB')),
                'purchase': rate.get('purchaseRate', rate.get('purchaseRateNB'))
            }
    return result

async def main(count,currencies):
    
    tasks = []
    dates = [(datetime.now() - timedelta(days=i)).strftime('%d.%m.%Y') for i in range(count)]
    
    try:

        for date in dates:
            task = ExchangeRatesAPI(datetime.strptime(date, '%d.%m.%Y'))
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
        
        results = [{date: process_data(data,currencies)} for date, data in zip(dates, responses)]      
        return results
        
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or not sys.argv[1].isdigit():
        print("Usage: main.py <days>")
        sys.exit(1)
    days = int(sys.argv[1])
    if len(sys.argv) > 2:
        currencies = sys.argv[2].upper()
    else:
        currencies = ['EUR', 'USD']

    if days < 1 or days > 10:
        print("Error: Number of days should be between 1 and 10.")
        sys.exit(1)
    rate = asyncio.run(main(days,currencies))
    print(json.dumps(rate, indent=2))