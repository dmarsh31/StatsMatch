"""Placeholder pages for player comparisons and similarity exploration."""
from flask import Blueprint, current_app, render_template, request
from ..services.players import load_players
from ..services.api_football import PlayerAPIError
from ..services.player_stats import (
    DEFAULT_SEASON, METRICS, get_cached_statistics, combine_player_statistics, per_90,
)
from ..services.similarity import build_similarity_map

explore_pages = Blueprint('explore', __name__)


@explore_pages.get('/compare')
def compare():
    players = sorted(load_players(), key=lambda player: player['name'].casefold())
    by_id = {player['id']: player for player in players}
    selected = [request.args.get('player1', ''), request.args.get('player2', '')]
    columns = []
    error = None
    status = 200
    if any(selected):
        if not all(player_id in by_id for player_id in selected):
            error, status = 'Select two saved players to compare.', 400
        elif selected[0] == selected[1]:
            error, status = 'Select two different players.', 400
        else:
            for player_id in selected:
                column = {'player': by_id[player_id], 'stat': None, 'error': None}
                try:
                    statistics = get_cached_statistics(
                        player_id, current_app.config.get('API_FOOTBALL_KEY'), DEFAULT_SEASON)
                    column['stat'] = combine_player_statistics(statistics)
                except PlayerAPIError as exception:
                    column['error'] = str(exception)
                    status = 502 if current_app.config.get('API_FOOTBALL_KEY') else 503
                except (OSError, ValueError):
                    current_app.logger.exception('Unable to load comparison statistics')
                    column['error'] = 'Unable to read or save statistics. Please try again.'
                    status = 500
                columns.append(column)
    return render_template('compare.html', title='Compare', players=players,
                           selected=selected, columns=columns, error=error,
                           season=DEFAULT_SEASON, metrics=METRICS, per_90=per_90), status


@explore_pages.get('/similarity-map')
def similarity_map():
    clusters = max(2, min(8, request.args.get('clusters', 2, type=int)))
    minimum_minutes = max(1, min(10000, request.args.get('minutes', 90, type=int)))
    try:
        model = build_similarity_map(clusters, minimum_minutes)
    except (OSError, ValueError, KeyError, TypeError):
        current_app.logger.exception('Unable to build similarity map')
        return render_template('similarity_map.html', title='Similarity map',
                               model={'points': [], 'message': 'Unable to read saved statistics. Please check the CSV data.', 'season': DEFAULT_SEASON, 'cached': 0, 'eligible': 0},
                               clusters=clusters, minimum_minutes=minimum_minutes), 500
    return render_template('similarity_map.html', title='Similarity map', model=model,
                           clusters=clusters, minimum_minutes=minimum_minutes)
