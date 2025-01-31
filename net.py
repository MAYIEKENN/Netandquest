from fastapi import FastAPI
import aiohttp
import asyncio

app = FastAPI()

# URLs
API_URL = "https://xalyon.x10.mx/data.json"
CLAIM_URL = "https://apis.mytel.com.mm/daily-quest-v3/api/v3/daily-quest/daily-claim"
TEST_URL = "https://apis.mytel.com.mm/network-test/v3/submit"

# Operators List
OPERATORS = ["MYTEL", "MPT", "OOREDOO", "ATOM"]

async def fetch_json_data(session):
    """Fetch JSON data from the API."""
    async with session.get(API_URL) as response:
        if response.status == 200:
            return await response.json()
        return None

async def send_claim_request(session, access_token, msisdn):
    """Send a request to claim daily rewards."""
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    payload = {"msisdn": msisdn}

    async with session.post(CLAIM_URL, json=payload, headers=headers) as response:
        return response.status == 200

async def send_network_test_request(session, number, api_key, operator):
    """Send a network test request for each operator."""
    payload = {
        "cellId": "51273751",
        "deviceModel": "Redmi Note 8 Pro",
        "downloadSpeed": 0.8,
        "enb": "200288",
        "latency": 734.875,
        "latitude": "21.4631248",
        "location": "Mandalay Region, Myanmar (Burma)",
        "longitude": "95.3621706",
        "msisdn": number.replace("%2B959", "+959"),
        "networkType": "_4G",
        "operator": operator,
        "requestId": number,
        "rsrp": "-98",
        "township": "Mandalay Region",
        "uploadSpeed": 10.0
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    async with session.post(TEST_URL, json=payload, headers=headers) as response:
        return response.status == 200

@app.get("/start")
async def start_processing():
    """API endpoint to start processing claims and network tests."""
    async with aiohttp.ClientSession() as session:
        data = await fetch_json_data(session)
        if not data:
            return {"status": "error", "message": "Failed to fetch JSON data."}

        # Create tasks for both claims and network tests
        claim_tasks = [send_claim_request(session, item["api"], item["number"]) for item in data]
        network_tasks = [
            send_network_test_request(session, item["number"], item["api"], operator)
            for item in data for operator in OPERATORS
        ]

        results = await asyncio.gather(*claim_tasks, *network_tasks)

        # Count success and failure
        success_count = sum(results)
        fail_count = len(results) - success_count

        return {"status": "success", "success": success_count, "fail": fail_count}
