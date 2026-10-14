import re
import requests
import json

class LiveGameParser:
    ESPORTS_API = "https://esports-api.lolesports.com/persisted/gw"
    LIVE_STATS_API = "https://feed.lolesports.com/livestats/v1"

    DDRAGON_VERSIONS = (
        "https://ddragon.leagueoflegends.com/api/versions.json"
    )

    ROLE_ORDER = [
        "TOP",
        "JUNGLE",
        "MID",
        "BOTTOM",
        "SUPPORT",
    ]

    ROLE_MAPPING = {
        "TOP": "TOP",

        "JUNGLE": "JUNGLE",
        "JNG": "JUNGLE",

        "MID": "MID",
        "MIDDLE": "MID",

        "BOTTOM": "BOTTOM",
        "BOT": "BOTTOM",
        "ADC": "BOTTOM",

        "SUPPORT": "SUPPORT",
        "SUP": "SUPPORT",
    }

    def __init__(self, api_key, locale="en-US"):
        self.api_key = api_key
        self.locale = locale

        self.session = requests.Session()

        self.session.headers.update({
            "x-api-key": self.api_key
        })

        # Load Riot champion ID -> display name mapping once.
        self.champion_names = self._load_champion_names()

    # ============================================================
    # DATA DRAGON
    # ============================================================

    def _load_champion_names(self):
        """
        Build:

        {
            "LeeSin": "Lee Sin",
            "TwistedFate": "Twisted Fate",
            "MonkeyKing": "Wukong",
            ...
        }

        Also maps numeric champion keys where possible.
        """

        try:
            response = requests.get(
                self.DDRAGON_VERSIONS,
                timeout=10,
            )
            response.raise_for_status()

            versions = response.json()

            if not versions:
                return {}

            version = versions[0]

            url = (
                "https://ddragon.leagueoflegends.com/"
                f"cdn/{version}/data/en_US/champion.json"
            )

            response = requests.get(
                url,
                timeout=10,
            )
            response.raise_for_status()

            champions = (
                response
                .json()
                .get("data", {})
            )

            mapping = {}

            for champion in champions.values():

                riot_id = champion.get("id")
                numeric_key = champion.get("key")
                display_name = champion.get("name")

                if riot_id and display_name:
                    mapping[str(riot_id)] = display_name

                if numeric_key and display_name:
                    mapping[str(numeric_key)] = display_name

            # Riot historically uses MonkeyKing internally.
            mapping["MonkeyKing"] = "Wukong"

            return mapping

        except requests.RequestException as exc:

            print(
                "Warning: failed to load Data Dragon "
                f"champion names: {exc}"
            )

            return {}

    def _champion_name(self, champion_id):
        """
        Convert a Riot champion identifier into its display name.

        LeeSin     -> Lee Sin
        MonkeyKing -> Wukong

        If no mapping exists, return the original value.
        """

        if champion_id is None:
            return None

        champion_id = str(champion_id)

        return self.champion_names.get(
            champion_id,
            champion_id,
        )

    # ============================================================
    # API REQUESTS
    # ============================================================

    def get_live_events(self):

        response = self.session.get(
            f"{self.ESPORTS_API}/getLive",
            params={
                "hl": self.locale,
            },
            timeout=10,
        )

        response.raise_for_status()

        return (
            response
            .json()
            .get("data", {})
            .get("schedule", {})
            .get("events")
        ) or []

    def get_event_details(self, event_id):

        response = self.session.get(
            f"{self.ESPORTS_API}/getEventDetails",
            params={
                "hl": self.locale,
                "id": event_id,
            },
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    def get_live_stats(self, game_id):

        response = self.session.get(
            f"{self.LIVE_STATS_API}/window/{game_id}",
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    # ============================================================
    # EVENT PARSING
    # ============================================================

    @staticmethod
    def _get_event(event_details):

        return (
            event_details
            .get("data", {})
            .get("event", {})
        )

    def _get_event_games(self, event_details):

        event = self._get_event(event_details)

        return (
            event
            .get("match", {})
            .get("games")
        ) or []

    def get_game_ids(self, event_details):

        games = self._get_event_games(
            event_details
        )

        return [
            str(game["id"])
            for game in games
            if game.get("id") is not None
        ]

    # ============================================================
    # SERIES
    # ============================================================

    def _get_game_number(
        self,
        event_details,
        game_id,
    ):

        games = self._get_event_games(
            event_details
        )

        game_id = str(game_id)

        for index, game in enumerate(
            games,
            start=1,
        ):

            if str(game.get("id")) == game_id:
                return str(index)

        return "0"

    def _get_series_score_before_game(
        self,
        event_details,
        game_id,
        blue_team_id=None,
    ):
        """
        Series score differential from the current
        game's blue-team perspective.

        Blue leading 2-1 -> "1"
        Red leading 2-0  -> "-2"
        Tied             -> "0"
        """

        games = self._get_event_games(
            event_details
        )

        blue_wins = 0
        red_wins = 0

        game_id = str(game_id)

        for game in games:

            if str(game.get("id")) == game_id:
                break

            if (
                str(game.get("state", "")).lower()
                != "completed"
            ):
                continue

            winner = game.get("winner")

            if winner is None:
                continue

            if isinstance(winner, int):

                if winner == 1:
                    blue_wins += 1

                elif winner == 2:
                    red_wins += 1

                continue

            winner_string = str(winner)
            winner_lower = winner_string.lower()

            if winner_lower in ("blue", "1"):

                blue_wins += 1

            elif winner_lower in ("red", "2"):

                red_wins += 1

            elif (
                blue_team_id
                and winner_string == str(blue_team_id)
            ):

                blue_wins += 1

            else:

                red_wins += 1

        return str(
            blue_wins - red_wins
        )

    # ============================================================
    # SPLIT / PLAYOFFS
    # ============================================================

    def _get_split(self, event_details):

        event = self._get_event(
            event_details
        )

        tournament = (
            event.get("tournament")
            or {}
        )

        candidates = [
            tournament.get("split"),
            event.get("split"),
            tournament.get("name"),
            event.get("blockName"),
        ]

        for value in candidates:

            if not value:
                continue

            lower = str(value).lower()

            if "spring" in lower:
                return "Spring"

            if "summer" in lower:
                return "Summer"

            if "winter" in lower:
                return "Winter"

        return "Summer"

    def _is_playoffs(self, event_details):

        event = self._get_event(
            event_details
        )

        tournament = (
            event.get("tournament")
            or {}
        )

        text = " ".join([
            str(event.get("blockName", "")),
            str(tournament.get("name", "")),
            str(event.get("type", "")),
        ]).lower()

        playoff_terms = (
            "playoff",
            "knockout",
            "quarterfinal",
            "quarter-final",
            "semifinal",
            "semi-final",
            "grand final",
            "final",
        )

        return (
            "1"
            if any(
                term in text
                for term in playoff_terms
            )
            else "0"
        )

    # ============================================================
    # ROLES
    # ============================================================

    @classmethod
    def _normalize_role(cls, role):

        role = str(
            role or ""
        ).strip().upper()

        return cls.ROLE_MAPPING.get(
            role,
            role,
        )

    @classmethod
    def _participants_by_role(
        cls,
        participants,
    ):

        result = {}

        for participant in participants or []:

            role = cls._normalize_role(
                participant.get("role")
            )

            if not role:
                continue

            result[role] = {
                "name": participant.get(
                    "summonerName"
                ),
                "champion": participant.get(
                    "championId"
                ),
            }

        return result

    # ============================================================
    # PLAYER NAME CLEANING
    # ============================================================

    @staticmethod
    def _clean_player_name(
        player_name,
        team_name=None,
        team_code=None,
    ):
        """
        Remove team prefixes from player names.

        Examples:

            "GEN Chovy"       -> "Chovy"
            "GEN.Chovy"       -> "Chovy"
            "GEN_Chovy"       -> "Chovy"
            "Gen.G Chovy"     -> "Chovy"

            "T1 Faker"        -> "Faker"
            "T1.Faker"        -> "Faker"

        If the name is already just "Chovy", it is unchanged.
        """

        if player_name is None:
            return None

        name = str(player_name).strip()

        prefixes = []

        if team_code:
            prefixes.append(
                str(team_code).strip()
            )

        if team_name:
            prefixes.append(
                str(team_name).strip()
            )

        # Longest first so "Gen.G" gets tested
        # before a shorter overlapping prefix.
        prefixes.sort(
            key=len,
            reverse=True,
        )

        for prefix in prefixes:

            if not prefix:
                continue

            # Match:
            #
            # GEN Chovy
            # GEN.Chovy
            # GEN_Chovy
            # GEN-Chovy
            # Gen.G Chovy

            pattern = (
                r"^"
                + re.escape(prefix)
                + r"[\s._\-|:]+"
            )

            cleaned = re.sub(
                pattern,
                "",
                name,
                count=1,
                flags=re.IGNORECASE,
            )

            if cleaned != name:
                return cleaned.strip()

        return name

    # ============================================================
    # PATCH
    # ============================================================

    @staticmethod
    def _format_patch(patch):

        if not patch:
            return "0"

        patch = str(patch)

        parts = patch.split(".")

        if len(parts) >= 2:
            return (
                f"{parts[0]}"
                f"{parts[1]}"
            )

        return patch.replace(
            ".",
            "",
        )

    # ============================================================
    # TEAM INFORMATION
    # ============================================================

    @staticmethod
    def _extract_event_teams(event):

        teams = (
            event
            .get("match", {})
            .get("teams")
        ) or []

        result = []

        for team in teams:

            result.append({
                "id": str(
                    team.get("id", "")
                ),
                "name": team.get(
                    "name",
                    "Unknown",
                ),
                "code": team.get("code"),
            })

        return result

    @staticmethod
    def _resolve_blue_red_teams(
        event_teams,
        metadata,
    ):

        blue_metadata = (
            metadata.get(
                "blueTeamMetadata"
            )
            or {}
        )

        red_metadata = (
            metadata.get(
                "redTeamMetadata"
            )
            or {}
        )

        blue_id = str(
            blue_metadata.get(
                "esportsTeamId",
                "",
            )
        )

        red_id = str(
            red_metadata.get(
                "esportsTeamId",
                "",
            )
        )

        team_lookup = {
            str(team["id"]): team
            for team in event_teams
        }

        blue_event_team = (
            team_lookup.get(blue_id)
            or {}
        )

        red_event_team = (
            team_lookup.get(red_id)
            or {}
        )

        blue_name = blue_event_team.get(
            "name",
            blue_metadata.get(
                "teamName",
                "Unknown",
            ),
        )

        red_name = red_event_team.get(
            "name",
            red_metadata.get(
                "teamName",
                "Unknown",
            ),
        )

        return {
            "blue_id": blue_id,
            "red_id": red_id,

            "blue_name": blue_name,
            "red_name": red_name,

            "blue_code": blue_event_team.get(
                "code"
            ),

            "red_code": red_event_team.get(
                "code"
            ),
        }

    # ============================================================
    # LIVE GAME DISCOVERY
    # ============================================================

    def get_live_games(self):

        live_games = []

        events = self.get_live_events()

        for event in events:

            event_id = event.get("id")

            if not event_id:
                continue

            league = (
                event
                .get("league", {})
                .get("name", "0")
            )

            event_teams = (
                self._extract_event_teams(
                    event
                )
            )

            try:

                details = (
                    self.get_event_details(
                        event_id
                    )
                )

            except requests.RequestException as exc:

                print(
                    f"Failed to get event "
                    f"{event_id}: {exc}"
                )

                continue

            game_ids = self.get_game_ids(
                details
            )

            for game_id in game_ids:

                try:

                    stats = self.get_live_stats(
                        game_id
                    )

                except requests.HTTPError as exc:

                    if (
                        exc.response is not None
                        and
                        exc.response.status_code
                        in (400, 404)
                    ):
                        continue

                    print(
                        f"Failed to get game "
                        f"{game_id}: {exc}"
                    )

                    continue

                except requests.RequestException as exc:

                    print(
                        f"Failed to get game "
                        f"{game_id}: {exc}"
                    )

                    continue

                frames = (
                    stats.get("frames")
                    or []
                )

                if not frames:
                    continue

                live_games.append({
                    "event_id": str(
                        event_id
                    ),

                    "game_id": str(
                        game_id
                    ),

                    "league": league,

                    "event": event,

                    "event_details": details,

                    "event_teams": event_teams,

                    "stats": stats,
                })

        return live_games

    # ============================================================
    # MODEL JSON
    # ============================================================

    def game_to_json(self, game):

        stats = game["stats"]

        metadata = (
            stats.get("gameMetadata")
            or {}
        )

        blue_metadata = (
            metadata.get(
                "blueTeamMetadata"
            )
            or {}
        )

        red_metadata = (
            metadata.get(
                "redTeamMetadata"
            )
            or {}
        )

        # --------------------------------------------------------
        # Participants
        # --------------------------------------------------------

        blue = self._participants_by_role(
            blue_metadata.get(
                "participantMetadata"
            )
        )

        red = self._participants_by_role(
            red_metadata.get(
                "participantMetadata"
            )
        )

        # --------------------------------------------------------
        # Teams
        # --------------------------------------------------------

        teams = self._resolve_blue_red_teams(
            game["event_teams"],
            metadata,
        )

        # --------------------------------------------------------
        # Player names
        # --------------------------------------------------------

        player_names = []

        # Blue players first.
        for role in self.ROLE_ORDER:

            raw_name = (
                blue
                .get(role, {})
                .get("name")
            )

            clean_name = self._clean_player_name(
                raw_name,
                team_name=teams["blue_name"],
                team_code=teams["blue_code"],
            )

            player_names.append(
                clean_name
            )

        # Red players second.
        for role in self.ROLE_ORDER:

            raw_name = (
                red
                .get(role, {})
                .get("name")
            )

            clean_name = self._clean_player_name(
                raw_name,
                team_name=teams["red_name"],
                team_code=teams["red_code"],
            )

            player_names.append(
                clean_name
            )

        # --------------------------------------------------------
        # Champion picks
        # --------------------------------------------------------

        def blue_champion(role):

            champion = (
                blue
                .get(role, {})
                .get("champion")
            )

            return self._champion_name(
                champion
            )

        def red_champion(role):

            champion = (
                red
                .get(role, {})
                .get("champion")
            )

            return self._champion_name(
                champion
            )

        # --------------------------------------------------------
        # Patch
        # --------------------------------------------------------

        patch = (
            metadata.get("patchVersion")
            or metadata.get("patch")
        )

        patch = self._format_patch(
            patch
        )

        # --------------------------------------------------------
        # Series
        # --------------------------------------------------------

        game_number = (
            self._get_game_number(
                game["event_details"],
                game["game_id"],
            )
        )

        series_score = (
            self._get_series_score_before_game(
                game["event_details"],
                game["game_id"],
                teams["blue_id"],
            )
        )

        # --------------------------------------------------------
        # Final dictionary
        # --------------------------------------------------------

        return {
            "league": game.get(
                "league",
                "0",
            ),

            "split": self._get_split(
                game["event_details"]
            ),

            "playoffs": self._is_playoffs(
                game["event_details"]
            ),

            "game_in_series": game_number,

            "series_score_before_game": (
                series_score
            ),

            "patch": patch,

            "team1_blue": teams[
                "blue_name"
            ],

            "team2_red": teams[
                "red_name"
            ],

            # Historical features
            "head_to_head": "0",

            "team1_last5": "0",

            "team2_last5": "0",

            # Blue picks
            "blue_top_pick": (
                blue_champion("TOP")
            ),

            "blue_jng_pick": (
                blue_champion("JUNGLE")
            ),

            "blue_mid_pick": (
                blue_champion("MID")
            ),

            "blue_bot_pick": (
                blue_champion("BOTTOM")
            ),

            "blue_sup_pick": (
                blue_champion("SUPPORT")
            ),

            # Red picks
            "red_top_pick": (
                red_champion("TOP")
            ),

            "red_jng_pick": (
                red_champion("JUNGLE")
            ),

            "red_mid_pick": (
                red_champion("MID")
            ),

            "red_bot_pick": (
                red_champion("BOTTOM")
            ),

            "red_sup_pick": (
                red_champion("SUPPORT")
            ),

            # Players
            "playername": player_names,

            # Blue players = 1
            # Red players = 0
            "firstpick": [
                1, 1, 1, 1, 1,
                0, 0, 0, 0, 0,
            ],

            # Historical feature
            "champion_patch_winrate": [
                0.5, 0.5, 0.5, 0.5, 0.5,
                0.5, 0.5, 0.5, 0.5, 0.5,
            ],

            # Unknown while live
            "winner": "0",
        }

    # ============================================================
    # MAIN PUBLIC METHOD
    # ============================================================

    def get_live_game_jsons(self):
        """
        Return one model-input dictionary per live game.
        """

        games = self.get_live_games()

        return [
            self.game_to_json(game)
            for game in games
        ]


if __name__ == "__main__":
    bob = LiveGameParser(api_key="0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z") # I AM AWARE THAT THIS IS LEAKED INTO THE REPO. This is a publically available api key.

    for (count, game) in enumerate(bob.get_live_game_jsons()):
        print(f"{count}: {game['team1_blue']} vs {game['team2_red']}")
        with open("/Users/gig/Documents/Code/LOL_AI/user_input/" + str(count) + ".json", "w") as f:
            json.dump(game, f, indent=4)