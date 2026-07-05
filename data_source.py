"""Simple data source fetching recent Argentina results from Wikipedia.

This is a lightweight scraper: it fetches the team page HTML and searches for
score patterns. It's best-effort and has a fallback to random modifiers if
fetching/parsing fails.
"""
import re
import random
from urllib.parse import quote

try:
    import requests
except Exception:
    requests = None


def _fetch_page(team_name):
    # map team to Wikipedia page slug
    slug = team_name.replace(' ', '_') + '_national_football_team'
    url = f'https://en.wikipedia.org/wiki/{quote(slug)}'
    if requests is None:
        raise RuntimeError('requests not available')
    r = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    return r.text


def parse_results_from_html(html, team_name, max_matches=5):
    # find match score patterns like 'Argentina 2–1 Brazil' or 'Brazil 1–2 Argentina'
    pattern = re.compile(r'([A-Za-z \-\.]+?)\s(\d+)\u2013(\d+)\s([A-Za-z \-\.]+)')
    matches = pattern.findall(html)
    results = []
    for a, sa, sb, b in matches:
        a = a.strip()
        b = b.strip()
        sa = int(sa)
        sb = int(sb)
        if team_name in (a, b):
            # normalize opponent and result from perspective of team_name
            if a == team_name:
                opp = b
                team_score = sa
                opp_score = sb
            else:
                opp = a
                team_score = sb
                opp_score = sa
            if team_score > opp_score:
                res = 'win'
            elif team_score < opp_score:
                res = 'loss'
            else:
                res = 'draw'
            results.append((opp, res))
        if len(results) >= max_matches:
            break
    return results


def get_recent_map(team_name='Argentina'):
    """Return a map of recent rating deltas for teams based on recent matches.

    Example return: {'Argentina': -20, 'Brazil': +20}
    Positive number increases team rating; negative decreases.
    """
    try:
        html = _fetch_page(team_name)
        parsed = parse_results_from_html(html, team_name, max_matches=6)
        if not parsed:
            raise RuntimeError('no parsed results')
        recent = {}
        for opp, res in parsed:
            opp_key = opp.split(',')[0]
            if res == 'win':
                recent[team_name] = recent.get(team_name, 0) + 80
                recent[opp_key] = recent.get(opp_key, 0) - 80
            elif res == 'loss':
                recent[team_name] = recent.get(team_name, 0) - 80
                recent[opp_key] = recent.get(opp_key, 0) + 80
            else:
                # draw moderate adjustments
                recent[team_name] = recent.get(team_name, 0) + 10
                recent[opp_key] = recent.get(opp_key, 0) - 10
        return recent
    except Exception:
        # fallback: small random recent deltas for 2026 World Cup teams
        teams = [
            'Argentina', 'Brazil', 'France', 'Spain', 'England', 'Portugal', 'Belgium', 'Germany',
            'Netherlands', 'Croatia', 'Switzerland', 'Morocco', 'United States', 'Senegal',
            'Japan', 'Australia', 'Uruguay', 'Colombia', 'Ecuador', 'Canada', 'Mexico',
            'South Korea', 'Iran', 'Saudi Arabia', 'Tunisia', 'Ghana', 'Egypt', 'Algeria',
            'Nigeria', 'South Africa', 'Ivory Coast', 'DR Congo', 'Cape Verde', 'New Zealand',
            'Qatar', 'Jordan', 'Iraq', 'Uzbekistan', 'Austria', 'Scotland', 'Norway',
            'Turkey', 'Czech Republic', 'Bosnia and Herzegovina', 'Curaçao', 'Haiti', 'Panama'
        ]
        recent = {t: random.uniform(-60, 60) for t in teams}
        recent[team_name] = -sum(recent.values()) / max(1, len(recent))
        return recent
