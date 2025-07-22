import httpx
from config import GRAPH_API_ENDPOINT

async def create_event(access_token: str, event_data: dict):
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GRAPH_API_ENDPOINT}/me/events",
            json=event_data,
            headers=headers
        )
        return response.json()

async def update_event(access_token: str, event_id: str, event_data: dict):
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{GRAPH_API_ENDPOINT}/me/events/{event_id}",
            json=event_data,
            headers=headers
        )
        return response.json()

async def delete_event(access_token: str, event_id: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{GRAPH_API_ENDPOINT}/me/events/{event_id}",
            headers=headers
        )
        return response.status_code == 204
