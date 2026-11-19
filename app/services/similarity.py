"""K-means on saved, combined outfield-player performance; no API calls."""
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from .players import load_players
from .player_stats import DEFAULT_SEASON, combine_player_statistics, load_saved_statistics

FEATURES = (
    ('Goals', 'goals', 'total'), ('Assists', 'goals', 'assists'),
    ('Shots', 'shots', 'total'), ('Key passes', 'passes', 'key'),
    ('Passes', 'passes', 'total'), ('Tackles', 'tackles', 'total'),
    ('Interceptions', 'tackles', 'interceptions'), ('Duels won', 'duels', 'won'),
    ('Successful dribbles', 'dribbles', 'success'),
)


def build_similarity_map(clusters=2, minimum_minutes=90):
    saved = load_saved_statistics()
    candidates, vectors = [], []
    for player in sorted(load_players(), key=lambda item: int(item['id'])):
        blocks = saved.get(player['id'], [])
        combined = combine_player_statistics(blocks)
        if not combined or player.get('position', '').casefold() == 'goalkeeper':
            continue
        minutes = combined['games']['minutes']
        if minutes is None or minutes < max(1, minimum_minutes):
            continue
        # Match each numerator to minutes from the same competition blocks.
        # Missing competition data must not dilute rates by adding extra minutes.
        vector = []
        for _, group, field in FEATURES:
            covered = [block for block in blocks
                       if (block.get(group) or {}).get(field) is not None
                       and (block.get('games') or {}).get('minutes') is not None
                       and float(block['games']['minutes']) > 0]
            if covered:
                covered_stats = combine_player_statistics(covered)
                vector.append(float(covered_stats[group][field]) * 90
                              / float(covered_stats['games']['minutes']))
            else:
                vector.append(np.nan)
        if np.isfinite(vector).sum() < 3:
            continue
        candidates.append(dict(player, minutes=minutes))
        vectors.append(vector)

    result = {'points': [], 'message': None, 'season': DEFAULT_SEASON,
              'clusters': 0, 'features': [], 'eligible': len(candidates),
              'cached': len(saved), 'variance': 0}
    if len(candidates) < 2:
        result['message'] = 'At least two saved outfield players need enough minutes and three available stats. Open more player profiles to save their season stats, or lower the minutes filter.'
        return result
    matrix = np.asarray(vectors, dtype=float)
    # Drop unavailable or non-varying features; do not interpret missing stats as zero.
    columns = [index for index in range(len(FEATURES))
               if np.isfinite(matrix[:, index]).sum() >= 2
               and np.nanstd(matrix[:, index]) > 0]
    if not columns:
        result['message'] = 'Saved players do not yet have enough differing stats to form clusters.'
        return result
    matrix = matrix[:, columns]
    missing = np.isnan(matrix)
    medians = np.nanmedian(matrix, axis=0)
    matrix = np.where(missing, medians, matrix)
    scaled = StandardScaler().fit_transform(matrix)
    count = min(clusters, len(np.unique(scaled, axis=0)), len(candidates))
    if count < 2:
        result['message'] = 'Saved players have identical usable stats. Save more players to form clusters.'
        return result
    with threadpool_limits(limits=1):
        labels = KMeans(n_clusters=count, random_state=42, n_init=10).fit_predict(scaled)
        pca = PCA(n_components=min(2, len(columns)), svd_solver='full')
        coordinates = pca.fit_transform(scaled)
    if coordinates.shape[1] == 1:
        coordinates = np.column_stack((coordinates[:, 0], np.zeros(len(candidates))))
    distances = np.linalg.norm(scaled[:, None, :] - scaled[None, :, :], axis=2)
    for index, player in enumerate(candidates):
        nearest = [int(other) for other in np.argsort(distances[index]) if other != index][:3]
        result['points'].append({
            'id': player['id'], 'name': player['name'], 'position': player.get('position', ''),
            'photo': player.get('photo', ''), 'minutes': player['minutes'],
            'cluster': int(labels[index]) + 1, 'x': float(coordinates[index, 0]),
            'y': float(coordinates[index, 1]), 'imputed': int(missing[index].sum()),
            'nearest': [candidates[other]['id'] for other in nearest],
        })
    result.update(clusters=count, features=[FEATURES[index][0] for index in columns],
                  variance=round(float(pca.explained_variance_ratio_.sum()) * 100))
    return result
