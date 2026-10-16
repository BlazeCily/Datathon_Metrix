import csv, collections, json, statistics

def load(path):
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

locs = load('locations.csv')
incidents = load('incidents.csv')
complaints = load('public_complaints.csv')

inc_by_loc = collections.defaultdict(list)
for i in incidents:
    inc_by_loc[i['location_id']].append(i)

comp_by_loc = collections.defaultdict(list)
for c in complaints:
    comp_by_loc[c['location_id']].append(c)

sev_w = {'Low':1,'Medium':2,'High':4,'Critical':7}
road_w = {'Good':0.10,'Fair':0.35,'Poor':0.70,'Critical':1.00}
ped_w = {'Low':0.25,'Medium':0.60,'High':1.00}
INJURY_MULT = 2

loc_scores = []
for loc in locs:
    lid = loc['location_id']
    inc_list = inc_by_loc[lid]
    comp_list = comp_by_loc[lid]

    inc_count = len(inc_list)
    sev_burden = sum(sev_w.get(i['severity'],0) for i in inc_list)
    total_injuries = sum(int(i['injuries']) for i in inc_list)
    unresolved = sum(1 for i in inc_list if i['resolved']=='0')
    crit_inc = sum(1 for i in inc_list if i['severity']=='Critical')
    high_inc = sum(1 for i in inc_list if i['severity']=='High')
    raw_burden = sev_burden + INJURY_MULT * total_injuries

    comp_count = len(comp_list)
    active_comp = sum(1 for c in comp_list if c['status'] in ('Open','Assigned','In progress'))
    high_priority = sum(1 for c in comp_list if c['priority_reported']=='High')

    loc_scores.append({
        'location_id': lid,
        'zone': loc['zone'],
        'road_condition': loc['road_condition'],
        'road_type': loc['road_type'],
        'population_density': int(loc['population_density_per_km2']),
        'near_school': int(loc['near_school']),
        'near_hospital': int(loc['near_hospital']),
        'pedestrian_activity': loc['pedestrian_activity'],
        'latitude': float(loc['latitude']),
        'longitude': float(loc['longitude']),
        'incident_count': inc_count,
        'sev_burden': sev_burden,
        'total_injuries': total_injuries,
        'raw_burden': raw_burden,
        'unresolved': unresolved,
        'crit_inc': crit_inc,
        'high_inc': high_inc,
        'complaint_count': comp_count,
        'active_comp': active_comp,
        'high_priority_comp': high_priority,
    })

def pct_rank(vals):
    sorted_unique = sorted(set(vals))
    n = len(sorted_unique)
    rank_map = {v: i/(n-1) if n>1 else 0.5 for i,v in enumerate(sorted_unique)}
    return [rank_map[v] for v in vals]

pr_inc = pct_rank([s['incident_count'] for s in loc_scores])
pr_burden = pct_rank([s['raw_burden'] for s in loc_scores])
pr_unres = pct_rank([s['unresolved'] for s in loc_scores])
pr_comp = pct_rank([s['complaint_count'] for s in loc_scores])
pr_active = pct_rank([s['active_comp'] for s in loc_scores])
pr_pop = pct_rank([s['population_density'] for s in loc_scores])

for i, s in enumerate(loc_scores):
    exposure = (pr_pop[i] + ped_w[s['pedestrian_activity']] + s['near_school'] + s['near_hospital']) / 4
    road_factor = road_w[s['road_condition']]
    c_inc = pr_inc[i] * 20
    c_burden = pr_burden[i] * 25
    c_unres = pr_unres[i] * 15
    c_comp = pr_comp[i] * 15
    c_active = pr_active[i] * 10
    c_road = road_factor * 10
    c_exposure = exposure * 5
    score = c_inc + c_burden + c_unres + c_comp + c_active + c_road + c_exposure
    s['score'] = round(score, 1)
    s['comp_inc'] = round(c_inc, 2)
    s['comp_burden'] = round(c_burden, 2)
    s['comp_unres'] = round(c_unres, 2)
    s['comp_comp'] = round(c_comp, 2)
    s['comp_active'] = round(c_active, 2)
    s['comp_road'] = round(c_road, 2)
    s['comp_exposure'] = round(c_exposure, 2)
    sc = s['score']
    if sc >= 80:
        s['tier'] = 'Very High'
    elif sc >= 60:
        s['tier'] = 'High'
    elif sc >= 40:
        s['tier'] = 'Moderate'
    else:
        s['tier'] = 'Lower'

loc_scores.sort(key=lambda x: (-x['score'], x['location_id']))
for rank, s in enumerate(loc_scores, 1):
    s['rank'] = rank

# Overview stats
total_locs = len(locs)
total_inc = len(incidents)
total_comp = len(complaints)
unres_total = sum(1 for i in incidents if i['resolved']=='0')
res_total = total_inc - unres_total
critical_inc = sum(1 for i in incidents if i['severity']=='Critical')
high_inc_total = sum(1 for i in incidents if i['severity']=='High')
medium_inc = sum(1 for i in incidents if i['severity']=='Medium')
low_inc = sum(1 for i in incidents if i['severity']=='Low')
active_total_comp = sum(1 for c in complaints if c['status'] in ('Open','Assigned','In progress'))
very_high = sum(1 for s in loc_scores if s['score']>=80)
high_tier = sum(1 for s in loc_scores if 60<=s['score']<80)
moderate_tier = sum(1 for s in loc_scores if 40<=s['score']<60)
lower_tier = sum(1 for s in loc_scores if s['score']<40)

road_counts = dict(collections.Counter(loc['road_condition'] for loc in locs))
type_counts = dict(collections.Counter(i['incident_type'] for i in incidents))
cat_counts = dict(collections.Counter(c['category'] for c in complaints))

month_inc = collections.defaultdict(int)
month_comp = collections.defaultdict(int)
for i in incidents:
    m = i['timestamp'][:7]
    month_inc[m] += 1
for c in complaints:
    m = c['created_at'][:7]
    month_comp[m] += 1

result = {
    'overview': {
        'total_locs': total_locs,
        'total_inc': total_inc,
        'total_comp': total_comp,
        'unres_total': unres_total,
        'res_total': res_total,
        'critical_inc': critical_inc,
        'high_inc': high_inc_total,
        'medium_inc': medium_inc,
        'low_inc': low_inc,
        'active_comp': active_total_comp,
        'very_high': very_high,
        'high_tier': high_tier,
        'moderate': moderate_tier,
        'lower': lower_tier,
    },
    'road_counts': road_counts,
    'type_counts': type_counts,
    'cat_counts': cat_counts,
    'month_inc': dict(sorted(month_inc.items())),
    'month_comp': dict(sorted(month_comp.items())),
    'top20': loc_scores[:20],
    'all_scores': loc_scores,
}

with open('scores_output.json', 'w') as f:
    json.dump(result, f, indent=2)

print('Done. Overview:', result['overview'])
print('Top 5:')
for s in loc_scores[:5]:
    print(f"  {s['rank']}. {s['location_id']} {s['zone']} score={s['score']} tier={s['tier']} road={s['road_condition']} inc={s['incident_count']} unres={s['unresolved']} inj={s['total_injuries']}")
