from contextlib import asynccontextmanager
import aiohttp
from api.token_manager import TokenManager
from api.models.player_model import PlayerModel
from api.models.team_model import TeamModel
from api.models.match_model import MatchModel
import settings

CLIENT_CREDENTIALS = {
    "username": settings.BOT_LOGIN,
    "password": settings.BOT_PASSWORD,
}

API_ENDPOINTS = {
    "players": settings.PLAYERS_API_URL,
    "teams": settings.TEAMS_API_URL,
    "matches": settings.MATCHES_API_URL,
}


class ApiClient:
    def __init__(self):

        self.token_manager = TokenManager(
            auth_endpoint=settings.AUTHENTICATION_API_URL,
            credentials=CLIENT_CREDENTIALS,
        )

    @asynccontextmanager
    async def _session_context(self):
        access_token = await self.token_manager.get_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            yield session

    async def get_all_players(self) -> list[PlayerModel]:

        async with self._session_context() as session:
            async with session.get(API_ENDPOINTS.get("players")) as response:
                if response.status != 200:
                    return []
                players_data = await response.json()
                return [PlayerModel(**player) for player in players_data]

    async def get_player_by_user(self, username: str) -> PlayerModel:
        player_detail_endpoint = f"{API_ENDPOINTS.get('players')}{username}"
        async with self._session_context() as session:
            async with session.get(player_detail_endpoint) as response:
                if response.status == 404:
                    return None
                data = await response.json()
                return PlayerModel(**data)

    async def get_player_by_uid(self, uid: int) -> PlayerModel:
        player_detail_endpoint = f"{API_ENDPOINTS.get('players')}by-uid/{uid}"
        async with self._session_context() as session:
            async with session.get(player_detail_endpoint) as response:
                if response.status == 404:
                    return None
                data = await response.json()
                return PlayerModel(**data)

    async def create_match(self):
        # acrescentar tratamento de erro
        async with self._session_context() as session:
            async with session.request(
                "POST", API_ENDPOINTS.get("matches")
            ) as response:
                match_data = await response.json()
                if response.status != 201:
                    return {"error": match_data}
                return MatchModel(**match_data)

    async def create_team(self, team: TeamModel) -> dict:

        if not isinstance(team, TeamModel):
            raise ValueError("team must be an instance of TeamModel")

        data = {
            "players_uuid": team.players_uuids,
            "match_uuid": team.match.uuid,
        }

        async with self._session_context() as session:
            async with session.post(API_ENDPOINTS.get("teams"), json=data) as response:
                team_data = await response.json()
                if response.status != 201:
                    return {"error": team_data}
                return team_data


api_client = ApiClient()
