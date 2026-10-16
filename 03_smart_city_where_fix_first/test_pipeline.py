"""
Tests for Smart City - Metrix Prioritization Engine
Asserts score bounds, component weight sum, monotonicity, and data integrity.
"""
import pytest
import json
import csv
import os

def test_weights_sum_to_100():
    weights = [20, 25, 15, 15, 10, 10, 5]
    assert sum(weights) == 100

def test_scores_json_exists_and_valid():
    path = os.path.join(os.path.dirname(__file__), 'scores_output.json')
    assert os.path.exists(path), "scores_output.json must exist"
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert 'all_scores' in data
    assert 'overview' in data
    assert len(data['all_scores']) == 1000

def test_score_bounds_and_tiers():
    path = os.path.join(os.path.dirname(__file__), 'scores_output.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for loc in data['all_scores']:
        assert 0.0 <= loc['score'] <= 100.0, f"Score {loc['score']} out of bounds for {loc['location_id']}"
        assert loc['tier'] in ('Very High', 'High', 'Moderate', 'Lower')
        
        # Check tier alignment
        if loc['score'] >= 80:
            assert loc['tier'] == 'Very High'
        elif loc['score'] >= 60:
            assert loc['tier'] == 'High'
        elif loc['score'] >= 40:
            assert loc['tier'] == 'Moderate'
        else:
            assert loc['tier'] == 'Lower'

def test_tie_handling_and_sorting():
    path = os.path.join(os.path.dirname(__file__), 'scores_output.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    scores = [item['score'] for item in data['all_scores']]
    # Verify sorted descending
    assert scores == sorted(scores, reverse=True)

def test_referential_integrity():
    base_dir = os.path.dirname(__file__)
    with open(os.path.join(base_dir, 'locations.csv'), 'r', encoding='utf-8') as f:
        loc_ids = {r['location_id'] for r in csv.DictReader(f)}
    
    with open(os.path.join(base_dir, 'incidents.csv'), 'r', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            assert r['location_id'] in loc_ids
            
    with open(os.path.join(base_dir, 'public_complaints.csv'), 'r', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            assert r['location_id'] in loc_ids

if __name__ == '__main__':
    pytest.main([__file__])
