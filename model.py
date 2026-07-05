"""Simple Elo-based probability model for match/tournament chances.

Provides functions to compute probability of `team` beating a random opponent
from a list, and a lightweight tournament simulation proxy for the 2026 World Cup.
"""
import math
import random

# Basic ratings for demonstration. Values approximate FIFA/ELO-style ratings
# for the 48 teams expected at the 2026 World Cup.
DEFAULT_RATINGS = {
    "Argentina": 2140,
    "Brazil": 2100,
    "France": 2095,
    "Spain": 2085,
    "England": 2075,
    "Portugal": 2065,
    "Belgium": 2055,
    "Germany": 2050,
    "Netherlands": 2045,
    "Croatia": 2025,
    "Switzerland": 1995,
    "Morocco": 1990,
    "Senegal": 1985,
    "United States": 1980,
    "Japan": 1975,
    "Australia": 1965,
    "Uruguay": 1955,
    "Colombia": 1945,
    "Ecuador": 1935,
    "Mexico": 1925,
    "Canada": 1915,
    "South Korea": 1900,
    "Iran": 1885,
    "Saudi Arabia": 1875,
    "Tunisia": 1865,
    "Ghana": 1855,
    "Egypt": 1850,
    "Algeria": 1845,
    "Nigeria": 1840,
    "South Africa": 1835,
    "Ivory Coast": 1830,
    "DR Congo": 1825,
    "Cape Verde": 1815,
    "New Zealand": 1810,
    "Qatar": 1805,
    "Jordan": 1800,
    "Iraq": 1795,
    "Uzbekistan": 1790,
    "Austria": 1785,
    "Scotland": 1780,
    "Norway": 1775,
    "Turkey": 1770,
    "Czech Republic": 1765,
    "Bosnia and Herzegovina": 1760,
    "Curaçao": 1755,
    "Haiti": 1750,
    "Panama": 1745,
}

DEFAULT_TEAMS = list(DEFAULT_RATINGS.keys())


def win_prob(r_a, r_b, k=200.0):
    """Probability A beats B given Elo-style ratings."""
    return 1.0 / (1.0 + 10 ** ((r_b - r_a) / k))


def probability_vs_field(team, others, ratings=None):
    """Return average win probability of `team` vs each team in `others`."""
    if ratings is None:
        ratings = DEFAULT_RATINGS
    r_a = ratings.get(team, 1500)
    probs = []
    for opponent in others:
        if opponent == team:
            continue
        r_b = ratings.get(opponent, 1500)
        probs.append(win_prob(r_a, r_b))
    return sum(probs) / len(probs) if probs else 0.0


def tournament_proxy(team, field, ratings=None):
    """Proxy probability of winning a tournament based on pairwise strengths."""
    return probability_vs_field(team, field, ratings)


def simulate_knockout(team, field, ratings=None, iterations=450):
    """Simulate a simple knockout tournament for a field of teams."""
    if ratings is None:
        ratings = DEFAULT_RATINGS
    if team not in field:
        return 0.0
    pool = list(field)
    if len(pool) == 0:
        return 0.0

    wins = 0
    if len(pool) & (len(pool) - 1) != 0:
        while len(pool) & (len(pool) - 1) != 0:
            pool.append('Bye')

    for _ in range(iterations):
        bracket = pool[:]
        random.shuffle(bracket)
        while len(bracket) > 1:
            next_round = []
            for i in range(0, len(bracket), 2):
                home = bracket[i]
                away = bracket[i + 1]
                if home == 'Bye':
                    winner = away
                elif away == 'Bye':
                    winner = home
                else:
                    ra = ratings.get(home, 1500)
                    rb = ratings.get(away, 1500)
                    p_home = win_prob(ra, rb)
                    winner = home if random.random() < p_home else away
                next_round.append(winner)
            bracket = next_round
        if bracket and bracket[0] == team:
            wins += 1
    return wins / iterations


def world_cup_win_probability(team, field=None, ratings=None, recent_map=None, injuries_map=None, form_map=None):
    """Estimate win probability for a team in a 2026-style tournament."""
    if field is None:
        field = DEFAULT_TEAMS
    if ratings is None:
        ratings = DEFAULT_RATINGS
    if recent_map or injuries_map or form_map:
        ratings = adjusted_ratings_map(ratings, injuries_map, form_map, recent_map)

    if len(field) < 8:
        return tournament_proxy(team, field, ratings)
    return simulate_knockout(team, field, ratings, iterations=450)


def top_teams(field=None, ratings=None, recent_map=None, injuries_map=None, form_map=None, count=8):
    """Return the top teams sorted by estimated tournament win probability."""
    if field is None:
        field = DEFAULT_TEAMS
    if ratings is None:
        ratings = DEFAULT_RATINGS
    if recent_map or injuries_map or form_map:
        ratings = adjusted_ratings_map(ratings, injuries_map, form_map, recent_map)
    entries = []
    for team in field:
        entries.append({
            'team': team,
            'rating': ratings.get(team, 1500),
            'prob': world_cup_win_probability(team, field, ratings),
        })
    entries.sort(key=lambda item: item['prob'], reverse=True)
    return entries[:count]


def adjusted_rating(base_rating, injuries=0, form=0, recent_delta=0):
    """Apply simple adjustments to a base rating."""
    r = base_rating
    r -= 100 * int(injuries)
    r += 45 * int(form)
    r += float(recent_delta)
    return r


def adjusted_ratings_map(base_ratings, injuries_map=None, form_map=None, recent_map=None):
    """Return a new ratings dict with per-team adjustments applied."""
    injuries_map = injuries_map or {}
    form_map = form_map or {}
    recent_map = recent_map or {}
    out = {}
    for team, rating in base_ratings.items():
        inj = injuries_map.get(team, 0)
        form = form_map.get(team, 0)
        recent = recent_map.get(team, 0)
        out[team] = adjusted_rating(rating, injuries=inj, form=form, recent_delta=recent)
    return out


if __name__ == '__main__':
    field = list(DEFAULT_RATINGS.keys())
    print('Argentina win probability:', world_cup_win_probability('Argentina', field))
    print('Top teams:', [row['team'] for row in top_teams(field)])
