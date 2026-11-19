"""Detail screen: load one player and calculate per-90 statistics."""
from flask import Blueprint, current_app, render_template, request
from ..services.players import load_players
from ..services.api_football import PlayerAPIError
from ..services.player_stats import (
    METRICS, DEFAULT_SEASON, get_cached_statistics, combine_player_statistics, per_90,
)

detail_page = Blueprint('detail', __name__)


@detail_page.get('/players/<player_id>')
def show(player_id):
    player = next((p for p in load_players() if p['id'] == player_id), None)
    if player is None:
        return render_template('not_found.html', title='Player not found'), 404
    season = DEFAULT_SEASON
    error = None
    status = 200
    statistics = []
    try:
        statistics = get_cached_statistics(player_id, current_app.config.get('API_FOOTBALL_KEY'), season)
    except PlayerAPIError as exception:
        error = str(exception)
        status = 502 if current_app.config.get('API_FOOTBALL_KEY') else 503
    except (OSError, ValueError):
        current_app.logger.exception('Unable to read or save season statistics')
        error, status = 'Unable to read or save season statistics. Please try again.', 500
    return render_template(
        'detail.html', title=player['name'], player=player,
        query=request.args.get('q', ''),
        stat=combine_player_statistics(statistics or []), metrics=METRICS, season=season, error=error,
        per_90=per_90,
    ), status
