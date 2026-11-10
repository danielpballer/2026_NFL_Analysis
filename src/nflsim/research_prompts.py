"""Write the weekly research prompts (four team groups plus weather) for the web-search agents.

    PYTHONPATH=src NFLSIM_WEEK=10 python -m nflsim.research_prompts /path/to/outdir 2026-11-10

Each prompt tells an agent which teams to cover, the schedule, the projected quarterbacks from the
schedule file, last week's carried absences, the JSON schema to write and the search budget.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from . import config as C

TEAM_PROMPT = """You are researching NFL injury and roster news for the {season} season, Week {week} (games {first_day} to {last_day}). Today is {today}. Week {prev} games were played in the seven days before today.

TOOLS: Only WebSearch works. WebFetch and direct HTTP to sports sites are blocked by the proxy, so rely on search-result snippets. Use WebSearch mode "extended" with specific opponent/date terms (e.g. "<team> <opponent> injury report {month_year}"); generic "week {week} injury report" queries in standard mode return prior seasons. You have a HARD BUDGET of {budget} WebSearch calls. Plan them: roughly 4-5 per team. Stop at {budget} even if gaps remain and say what is unverified.

DATE DISCIPLINE: Only use information dated {cutoff} or later for status. Articles from earlier seasons appear in results constantly; DISCARD them. If a snippet has no date and references a game or opponent that does not match the {season} schedule below, discard it. Say "unverified" rather than guessing.

Your teams (and their Week {week} opponents):
{teams}

Week {week} schedule (away at home): {schedule}. Byes: {byes}.

The schedule file lists these projected starting QBs; VERIFY each for your teams and explain any that look odd (the file has been wrong before): {qbs}.

Players we carried as absent LAST week (Week {prev}) for your teams are listed below. For each, say whether they are still out, activated/returned, or unknown:
{absences}

For EACH of your teams collect:
1. week{prev}_result: score and opponent, plus one line on anything notable (blowout, injuries in-game, QB benching).
2. qb: starter expected for Week {week}, backup, changed_from_week{prev} (true/false), notes (injury, benching, rookie debut, practice status).
3. injuries: every player with a Week {week} status concern, new IR/PUP/suspension placements since {cutoff}, and players activated from IR. Fields: player (full name as on the NFL roster, no nicknames, no semicolons), position, status (one of: Out, IR, PUP, NFI, Suspended, Doubtful, Questionable, Probable), injury (short description with the date/source context), starter (true/false: is this player a regular starter?), source (URL).
4. context_notes: 2-5 bullets of anything else relevant to the game: coaching changes, key player trades, travel, motivation, kicker issues, offensive line reshuffles.
5. sources: list of URLs used.

OUTPUT: Write valid JSON to the file {outfile} with the exact structure:
{{"collected_on": "{today_iso}", "search_calls_used": <int>, "unverified": ["..."], "teams": {{"TEAM": {{"week{prev}_result": "...", "qb": {{"starter": "...", "backup": "...", "changed_from_week{prev}": false, "notes": "..."}}, "injuries": [ {{...}} ], "context_notes": ["..."], "sources": ["..."]}}}}}}
Use the team abbreviations exactly as given (e.g. LA for the Rams, LV, JAX, NO). Validate the JSON by loading it with python before finishing. Your final reply should be a short summary (which teams had QB changes, the biggest injury news, what is unverified).
"""

WEATHER_PROMPT = """You are collecting weather forecasts for the {season} NFL Week {week} games ({first_day} to {last_day}). Today is {today}.

TOOLS: Only WebSearch works (WebFetch and direct HTTP to weather or sports sites are blocked). HARD BUDGET: 20 WebSearch calls. Use mode "extended" with the city, "forecast" and the date; local TV station and NWS pages work best. One search per outdoor game, 1-2 for the tropical outlook, and skip games in fixed domes. If no forecast dated {cutoff} or later exists, say "climatology" and give typical values rather than numbers from older articles. Stop at 20.

Games (game_id, day, kickoff ET, venue, roof per schedule file, location flag):
{games}

For each game report: venue, roof (outdoors/dome/closed/open), forecast_available (bool), temp_f (at kickoff), wind_mph (sustained; note gusts in notes), precip_chance_pct, conditions (one line), roof_closed_expected (bool, for retractables), source_type ("forecast" or "climatology"), confidence (low/medium/high), notes, source (URL). For a neutral or international venue, say whether it is open-air.
Also report a "tropical_outlook" string (NHC outlook for any system that could affect a venue this weekend).

OUTPUT: Write valid JSON to {outfile} with structure {{"collected_on": "{today_iso}", "search_calls_used": <int>, "tropical_outlook": "...", "games": {{"<game_id>": {{...}}, ...}}}}. Validate with python json.load before finishing. Final reply: 5-line summary of any game where wind >= 15 mph, rain >= 50%, cold, or an international venue.
"""


def build(outdir: Path, today_iso: str, season: int = C.SEASON, week: int = C.WEEK, budget: int = 40) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    g = pd.read_csv(C.RAW / "games.csv", low_memory=False)
    w = g[(g.season == season) & (g.week == week)].copy()
    today = pd.Timestamp(today_iso)
    all_teams = sorted(set(g[(g.season == season)].home_team))
    playing = list(w.away_team) + list(w.home_team)
    byes = sorted(set(all_teams) - set(playing))
    sched = "; ".join(f"{r.away_team} at {r.home_team}" + (f" ({r.stadium}, neutral site)" if str(r.location).lower() == "neutral" else "")
                      + (f" ({r.weekday[:3]})" if r.weekday != "Sunday" else "") for _, r in w.iterrows())
    qbs = ", ".join([f"{r.away_team} {r.away_qb_name}" for _, r in w.iterrows()] + [f"{r.home_team} {r.home_qb_name}" for _, r in w.iterrows()])
    opp = {}
    for _, r in w.iterrows():
        tag = " (neutral site)" if str(r.location).lower() == "neutral" else ""
        opp[r.away_team] = f"at {r.home_team}{tag}, {r.weekday}" + (f", {int(r.away_rest)} days rest" if r.away_rest != 7 else "")
        opp[r.home_team] = f"vs {r.away_team}{tag}, {r.weekday}" + (f", {int(r.home_rest)} days rest" if r.home_rest != 7 else "")
    prev_inj = json.loads((C.MANUAL / f"injuries_{season}_wk{week - 1}.json").read_text())["teams"]
    absent = {t: "; ".join(f"{p['player']} ({p['position']}, {p['status']})" for p in v["players"] if p["status"] in ("IR", "PUP", "NFI", "Suspended", "Out"))
              for t, v in prev_inj.items()}
    # four groups in schedule order so both teams of a game share an agent
    order = [t for _, r in w.iterrows() for t in (r.away_team, r.home_team)]
    size = -(-len(order) // 4)
    size += size % 2
    groups = [order[i:i + size] for i in range(0, len(order), size)]
    common = dict(season=season, week=week, prev=week - 1, today=today.strftime("%a %b %-d, %Y"), today_iso=today_iso,
                  first_day=pd.Timestamp(w.gameday.min()).strftime("%a %b %-d"), last_day=pd.Timestamp(w.gameday.max()).strftime("%a %b %-d, %Y"),
                  month_year=today.strftime("%B %Y"), cutoff=(today - pd.Timedelta(days=7)).strftime("%b %-d, %Y"),
                  schedule=sched, byes=", ".join(byes), qbs=qbs, budget=budget)
    paths = []
    for name, teams in zip("ABCD", groups):
        p = outdir / f"prompt_{name}.md"
        p.write_text(TEAM_PROMPT.format(teams="\n".join(f"- {t}: {opp[t]}" for t in teams),
                                        absences="\n".join(f"{t} {absent.get(t) or '(none)'}" for t in teams),
                                        outfile=outdir / f"group_{name}.json", **common))
        paths.append(p)
    games = "\n".join(f"- {r.game_id} {r.weekday} {r.gameday} {r.gametime} ET, {r.stadium}, roof={r.roof}, location={r.location}" for _, r in w.iterrows())
    p = outdir / "prompt_weather.md"
    p.write_text(WEATHER_PROMPT.format(games=games, outfile=outdir / "weather.json",
                                       **{k: common[k] for k in ("season", "week", "today", "today_iso", "first_day", "last_day")},
                                       cutoff=(today - pd.Timedelta(days=2)).strftime("%b %-d, %Y")))
    paths.append(p)
    return paths


if __name__ == "__main__":
    out = Path(sys.argv[1])
    day = sys.argv[2]
    for p in build(out, day):
        print("wrote", p)
