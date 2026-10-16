import json

with open('scores_output.json') as f:
    d = json.load(f)

top31 = [s for s in d['all_scores'] if s['score'] >= 60]
ov = d['overview']

# Build top31 JS array with coordinates and component breakdowns
top31_js = ',\n    '.join([
    '{rank:%d,location_id:"%s",zone:"%s",road_condition:"%s",road_type:"%s",score:%.1f,tier:"%s",'
    'incident_count:%d,unresolved:%d,total_injuries:%d,complaint_count:%d,active_comp:%d,'
    'crit_inc:%d,high_inc:%d,near_school:%d,near_hospital:%d,pedestrian_activity:"%s",'
    'latitude:%.6f,longitude:%.6f,'
    'comp_inc:%.2f,comp_burden:%.2f,comp_unres:%.2f,comp_comp:%.2f,comp_active:%.2f,comp_road:%.2f,comp_exposure:%.2f}'
    % (
        s['rank'], s['location_id'], s['zone'], s['road_condition'], s['road_type'], s['score'], s['tier'],
        s['incident_count'], s['unresolved'], s['total_injuries'], s['complaint_count'], s['active_comp'],
        s['crit_inc'], s['high_inc'], s['near_school'], s['near_hospital'], s['pedestrian_activity'],
        s['latitude'], s['longitude'],
        s.get('comp_inc', 0), s.get('comp_burden', 0), s.get('comp_unres', 0), s.get('comp_comp', 0),
        s.get('comp_active', 0), s.get('comp_road', 0), s.get('comp_exposure', 0)
    )
    for s in top31
])

# Compact representation of all 1,000 locations for citywide map view
all_locs_js = json.dumps([
    [
        s['location_id'], round(s['latitude'], 5), round(s['longitude'], 5),
        s['score'], s['tier'], s['road_condition'], s['incident_count'],
        s['unresolved'], s['total_injuries'], s['active_comp'], s['zone'], s['rank']
    ]
    for s in d['all_scores']
])

month_inc_js = str(list(d['month_inc'].values()))
month_comp_js = str(list(d['month_comp'].values()))

html = r"""<!DOCTYPE html>
<html class="dark" lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>Metrix — Smart City Priority Operations</title>
<meta name="description" content="Metrix: Explainable Civic Infrastructure Prioritization & Geographic Problem Navigator"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
tailwind.config={darkMode:"class",theme:{extend:{colors:{"primary-container":"#b9f36a","on-primary-container":"#466f00","primary":"#fefff2","on-primary":"#203600","secondary":"#ffb3af","on-secondary":"#68000d","secondary-container":"#920418","secondary-fixed-dim":"#ffb3af","tertiary-fixed-dim":"#ffb955","surface":"#101419","surface-container-lowest":"#0a0f13","surface-container-low":"#181c21","surface-container":"#1c2025","surface-container-high":"#262a30","surface-container-highest":"#31353b","on-surface":"#e0e2ea","on-surface-variant":"#c3c9b3","primary-fixed":"#baf46b","outline":"#8d937f","background":"#101419","on-background":"#e0e2ea"},fontFamily:{"space-grotesk":["Space Grotesk"],"manrope":["Manrope"]},borderRadius:{"DEFAULT":"0.5rem","lg":"0.75rem","xl":"1rem","full":"9999px"}}}};
</script>
<style>
*{box-sizing:border-box;}
html,body{margin:0;padding:0;font-family:'Manrope',sans-serif;height:100%;overflow-x:hidden;}
body{background:#0a0f13;color:#e0e2ea;overscroll-behavior:none;}
::-webkit-scrollbar{width:4px;height:4px;}
::-webkit-scrollbar-track{background:#0a0f13;}
::-webkit-scrollbar-thumb{background:#31353b;border-radius:4px;}
.sg{font-family:'Space Grotesk',sans-serif;}
.tab-panel{display:none;}
.tab-panel.active{display:block;}

/* SIDEBAR & LAYOUT TRANSITIONS */
#sidebar{
  position:fixed;left:0;top:0;width:240px;height:100%;
  background:#101419;z-index:50;display:flex;flex-direction:column;
  justify-content:space-between;box-shadow:2px 0 12px rgba(0,0,0,.6);
  transition:width .25s cubic-bezier(0.4,0,0.2,1);
  border-right:1px solid #1c2025;
}
#main-content{
  margin-left:240px;min-height:100vh;display:flex;flex-direction:column;
  transition:margin-left .25s cubic-bezier(0.4,0,0.2,1);
}
body.sidebar-collapsed #sidebar{width:68px;}
body.sidebar-collapsed #main-content{margin-left:68px;}
body.sidebar-collapsed .sidebar-text,
body.sidebar-collapsed .sidebar-badge{display:none !important;}
body.sidebar-collapsed .nav-btn{justify-content:center;padding:10px 0;}
body.sidebar-collapsed .sidebar-brand-text{display:none !important;}
body.sidebar-collapsed .sidebar-footer-info{display:none !important;}

.nav-btn{
  display:flex;align-items:center;gap:12px;padding:9px 12px;border-radius:8px;
  transition:all .15s;text-align:left;width:100%;border:none;cursor:pointer;
  background:transparent;color:#c3c9b3;font-family:'Space Grotesk',sans-serif;
  font-size:.875rem;font-weight:600;letter-spacing:.02em;margin-bottom:4px;
}
.nav-btn.active{background:#262a30;color:#b9f36a;}
.nav-btn:hover:not(.active){background:#1c2025;color:#e0e2ea;}

.kpi-card{background:#181c21;border:1px solid #1c2025;border-radius:.75rem;padding:1rem;display:flex;align-items:center;justify-content:space-between;}
.chart-card{background:#181c21;border:1px solid #1c2025;border-radius:.75rem;padding:1rem;}
.table-card{background:#181c21;border:1px solid #1c2025;border-radius:.75rem;overflow:hidden;}
.metric-val{font-family:'Space Grotesk',sans-serif;font-size:1.75rem;font-weight:700;letter-spacing:-.02em;line-height:2rem;}
.label-sm{font-family:'Space Grotesk',sans-serif;font-size:.6875rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;}
.label-md{font-family:'Space Grotesk',sans-serif;font-size:.75rem;font-weight:600;letter-spacing:.04em;}
.label-lg{font-family:'Space Grotesk',sans-serif;font-size:.875rem;font-weight:600;letter-spacing:.02em;}

.badge{display:inline-block;padding:2px 7px;border-radius:4px;font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:700;border:1px solid;}
.badge-high{background:rgba(255,92,92,.12);border-color:#ff5c5c;color:#ff5c5c;}
.badge-mod{background:rgba(255,185,85,.12);border-color:#ffb955;color:#ffb955;}
.badge-lower{background:rgba(124,185,255,.12);border-color:#7cb9ff;color:#7cb9ff;}

.road-critical{background:rgba(255,92,92,.15);color:#ff5c5c;border:1px solid rgba(255,92,92,.35);}
.road-poor{background:rgba(255,185,85,.15);color:#ffb955;border:1px solid rgba(255,185,85,.35);}
.road-fair{background:rgba(124,185,255,.15);color:#7cb9ff;border:1px solid rgba(124,185,255,.35);}
.road-good{background:rgba(185,243,106,.15);color:#b9f36a;border:1px solid rgba(185,243,106,.35);}

.score-bar{height:3px;border-radius:2px;background:linear-gradient(90deg,#9fd752,#b9f36a);}
tr.data-row:hover{background:#1c2025;}
tr.data-row{border-bottom:1px solid #1c2025;cursor:pointer;}
td,th{padding:10px 12px;white-space:nowrap;}
th{font-family:'Space Grotesk',sans-serif;font-size:.6875rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#c3c9b3;border-bottom:1px solid #262a30;background:#1c2025;}

@keyframes pulse-dot{0%,100%{opacity:1;transform:scale(1);}50%{opacity:.6;transform:scale(1.2);}}
.pulse{animation:pulse-dot 2s ease-in-out infinite;}
.disclaimer-bar{background:#1c2025;border-bottom:1px solid #262a30;padding:6px 16px;display:flex;align-items:center;gap:8px;}
.section-title{font-family:'Space Grotesk',sans-serif;font-size:.875rem;font-weight:600;letter-spacing:.02em;text-transform:uppercase;color:#e0e2ea;}
.icon{font-family:'Material Symbols Outlined';font-variation-settings:'FILL' 0,'wght' 400;font-size:20px;display:inline-block;line-height:1;}
.icon-fill{font-variation-settings:'FILL' 1,'wght' 400;}

/* MAP STYLING */
#city-map{height:100%;width:100%;background:#0b0d10;}
.leaflet-popup-content-wrapper{
  background:#171c22 !important;color:#e0e2ea !important;
  border:1px solid #252c34 !important;border-radius:10px !important;
  box-shadow:0 12px 32px rgba(0,0,0,.75) !important;padding:0 !important;
}
.leaflet-popup-content{margin:12px 14px !important;font-family:'Manrope',sans-serif !important;}
.leaflet-popup-tip{background:#171c22 !important;}
.leaflet-container a.leaflet-popup-close-button{color:#c3c9b3 !important;top:8px !important;right:8px !important;}

/* Problem Navigator Card */
.prob-card{
  background:#181c21;border:1px solid #1c2025;border-radius:8px;
  padding:12px;margin-bottom:8px;cursor:pointer;transition:all .15s;
}
.prob-card:hover{background:#1c2025;border-color:#262a30;}
.prob-card.active{background:#262a30;border-color:#b9f36a;border-left:4px solid #b9f36a;}

/* Floating Controls */
.glass-panel{
  background:rgba(23,28,34,.88);backdrop-filter:blur(10px);
  border:1px solid #252c34;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.5);
}
</style>
</head>
<body>

<!-- SIDEBAR -->
<aside id="sidebar">
  <div>
    <!-- Brand -->
    <div style="height:56px;padding:0 16px;display:flex;align-items:center;justify-content:space-between;background:#181c21;border-bottom:1px solid #1c2025;">
      <div style="display:flex;align-items:center;gap:10px;overflow:hidden;">
        <div style="width:28px;height:28px;border-radius:8px;background:#b9f36a;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
          <span class="icon icon-fill" style="font-size:16px;color:#203600;">my_location</span>
        </div>
        <div class="sidebar-brand-text">
          <div class="sg" style="font-size:14px;font-weight:700;color:#b9f36a;letter-spacing:-.01em;line-height:1.2;">METRIX</div>
          <div class="label-sm" style="color:#8d937f;font-size:9px;letter-spacing:.1em;">CIVIC OPS</div>
        </div>
      </div>
      <!-- Close / Collapse Sidebar Button -->
      <button onclick="toggleSidebar()" title="Toggle Sidebar (Collapse/Expand)" style="background:transparent;border:none;cursor:pointer;color:#c3c9b3;padding:4px;border-radius:6px;display:flex;align-items:center;" onmouseover="this.style.color='#b9f36a'" onmouseout="this.style.color='#c3c9b3'">
        <span class="icon" id="sidebar-icon-inner" style="font-size:20px;">menu_open</span>
      </button>
    </div>

    <!-- Navigation List -->
    <nav style="padding:12px;">
      <button class="nav-btn active" data-tab="overview" id="nav-overview" onclick="switchTab('overview')">
        <span class="icon icon-fill" style="font-size:18px;">dashboard</span>
        <span class="sidebar-text">Overview</span>
      </button>

      <!-- DEDICATED MAP FEATURE TAB -->
      <button class="nav-btn" data-tab="map" id="nav-map" onclick="switchTab('map')">
        <span class="icon icon-fill" style="font-size:18px;color:#ff5c5c;">map</span>
        <span class="sidebar-text" style="color:#fefff2;">Priority Map</span>
        <span class="sidebar-badge" style="margin-left:auto;font-size:10px;padding:2px 6px;border-radius:99px;background:rgba(255,92,92,.2);border:1px solid #ff5c5c;color:#ff5c5c;font-weight:700;">31 HOT</span>
      </button>

      <button class="nav-btn" data-tab="worklist" id="nav-worklist" onclick="switchTab('worklist')">
        <span class="icon" style="font-size:18px;">format_list_numbered</span>
        <span class="sidebar-text">Priority Worklist</span>
        <span class="sidebar-badge" style="margin-left:auto;font-size:11px;padding:2px 7px;border-radius:99px;background:#1c2025;color:#c3c9b3;">31</span>
      </button>

      <button class="nav-btn" data-tab="zones" id="nav-zones" onclick="switchTab('zones')">
        <span class="icon" style="font-size:18px;">equalizer</span>
        <span class="sidebar-text">Zone Analysis</span>
      </button>
    </nav>
  </div>

  <!-- Sidebar Footer -->
  <div style="padding:12px;border-top:1px solid #1c2025;">
    <div style="display:flex;align-items:center;gap:8px;padding:8px;border-radius:8px;background:#1c2025;margin-bottom:8px;">
      <span class="pulse" style="width:8px;height:8px;border-radius:50%;background:#b9f36a;display:inline-block;flex-shrink:0;"></span>
      <span class="label-sm sidebar-text" style="color:#c3c9b3;font-size:.625rem;">Synthetic Data · 2025</span>
      <span class="sidebar-badge" style="margin-left:auto;font-size:9px;font-weight:700;color:#b9f36a;padding:1px 5px;border-radius:3px;background:#262a30;font-family:'Space Grotesk',sans-serif;">DEMO</span>
    </div>
    <div style="display:flex;align-items:center;gap:8px;padding:0 4px;">
      <div style="width:28px;height:28px;border-radius:50%;background:#262a30;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
        <span class="icon" style="font-size:14px;color:#c3c9b3;">person</span>
      </div>
      <div class="sidebar-footer-info">
        <div class="label-md" style="color:#e0e2ea;">Lead Analyst</div>
        <div class="label-sm" style="color:#8d937f;font-size:.6rem;letter-spacing:.04em;">civic-ops@demo.gov</div>
      </div>
    </div>
  </div>
</aside>

<!-- MAIN CONTENT WRAPPER -->
<div id="main-content">

  <!-- TOPBAR -->
  <header style="position:sticky;top:0;height:56px;background:rgba(16,20,25,.95);backdrop-filter:blur(8px);z-index:40;display:flex;align-items:center;justify-content:space-between;padding:0 16px;box-shadow:0 1px 6px rgba(0,0,0,.4);border-bottom:1px solid #1c2025;">
    <div style="display:flex;align-items:center;gap:10px;">
      <!-- Header sidebar collapse toggle button -->
      <button onclick="toggleSidebar()" title="Toggle Sidebar" style="background:#181c21;border:1px solid #262a30;color:#c3c9b3;cursor:pointer;padding:6px;border-radius:6px;display:flex;align-items:center;justify-content:center;" onmouseover="this.style.color='#b9f36a';this.style.borderColor='#b9f36a'" onmouseout="this.style.color='#c3c9b3';this.style.borderColor='#262a30'">
        <span class="icon" id="topbar-toggle-icon" style="font-size:18px;">menu</span>
      </button>

      <div style="position:relative;">
        <span class="icon" style="position:absolute;left:10px;top:50%;transform:translateY(-50%);font-size:16px;color:#c3c9b3;pointer-events:none;">search</span>
        <input id="search-input" type="text" placeholder="Search location (e.g. L0965)" style="background:#0a0f13;color:#e0e2ea;border:1px solid #1c2025;border-radius:8px;padding:6px 12px 6px 34px;font-family:'Manrope',sans-serif;font-size:.8125rem;outline:none;width:230px;" onfocus="this.style.borderColor='#b9f36a'" onblur="this.style.borderColor='#1c2025'"/>
      </div>

      <div style="display:flex;align-items:center;gap:6px;padding:5px 10px;border-radius:99px;background:#1c2025;font-size:.6875rem;font-weight:700;color:#c3c9b3;font-family:'Space Grotesk',sans-serif;letter-spacing:.04em;">
        <span class="icon" style="font-size:13px;color:#ffb3af;">info</span>
        Synthetic demo data · Simulated coordinates · Illustrative priorities only
      </div>
    </div>

    <div style="display:flex;align-items:center;gap:8px;">
      <button onclick="switchTab('map')" style="display:flex;align-items:center;gap:6px;padding:6px 12px;border-radius:8px;background:rgba(255,92,92,.12);border:1px solid rgba(255,92,92,.3);color:#ff5c5c;font-size:.75rem;font-weight:700;font-family:'Space Grotesk',sans-serif;cursor:pointer;" onmouseover="this.style.background='rgba(255,92,92,.2)'" onmouseout="this.style.background='rgba(255,92,92,.12)'">
        <span class="icon" style="font-size:15px;">explore</span>
        <span>Open Map View</span>
      </button>
      <div style="display:flex;align-items:center;gap:6px;padding:6px 10px;border-radius:8px;background:#1c2025;font-size:.75rem;font-weight:600;color:#e0e2ea;font-family:'Space Grotesk',sans-serif;">
        <span class="icon" style="font-size:15px;color:#c3c9b3;">speed</span>
        <span style="color:#b9f36a;font-weight:700;">Score v1.0</span>
      </div>
    </div>
  </header>

  <!-- MAIN PAGE CONTENT -->
  <main style="flex:1;position:relative;">

    <!-- ==================== TAB 1: OVERVIEW ==================== -->
    <div class="tab-panel active" id="tab-overview" style="padding:20px;">
      <!-- Page header -->
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;flex-wrap:wrap;">
        <span class="pulse" style="width:8px;height:8px;border-radius:50%;background:#b9f36a;box-shadow:0 0 8px #b9f36a;display:inline-block;flex-shrink:0;"></span>
        <span class="sg" style="font-size:1.1rem;font-weight:700;color:#fefff2;">Priority Operations Canvas</span>
        <span style="color:#c3c9b3;font-size:.8125rem;"> | Metrix City Intelligence</span>
        <span style="padding:2px 8px;border-radius:4px;background:#262a30;color:#b9f36a;font-family:'Space Grotesk',sans-serif;font-size:.6875rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;">Score v1.0</span>
        <span style="margin-left:auto;font-size:.6875rem;font-weight:700;color:#c3c9b3;font-family:'Space Grotesk',sans-serif;letter-spacing:.04em;">1,000 locations · 10,000 incidents · 8,000 complaints</span>
      </div>

      <!-- KPI Grid -->
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
        <div class="kpi-card">
          <div>
            <div class="label-sm" style="color:#c3c9b3;margin-bottom:4px;">Locations Loaded</div>
            <div class="metric-val" style="color:#e0e2ea;">1,000</div>
            <div class="label-sm" style="color:#8d937f;font-size:.625rem;margin-top:4px;">20 zones · 5 road types</div>
          </div>
          <div style="width:40px;height:40px;border-radius:10px;background:#262a30;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
            <span class="icon icon-fill" style="font-size:22px;color:#b9f36a;">pin_drop</span>
          </div>
        </div>
        <div class="kpi-card">
          <div>
            <div class="label-sm" style="color:#c3c9b3;margin-bottom:4px;">Total Incidents</div>
            <div class="metric-val" style="color:#e0e2ea;">10,000</div>
            <div class="label-sm" style="color:#ffb3af;font-size:.625rem;margin-top:4px;">2,874 unresolved (28.7%)</div>
          </div>
          <div style="width:40px;height:40px;border-radius:10px;background:#262a30;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
            <span class="icon" style="font-size:22px;color:#ffb3af;">emergency</span>
          </div>
        </div>
        <div class="kpi-card">
          <div>
            <div class="label-sm" style="color:#c3c9b3;margin-bottom:4px;">Public Complaints</div>
            <div class="metric-val" style="color:#e0e2ea;">8,000</div>
            <div class="label-sm" style="color:#ffb955;font-size:.625rem;margin-top:4px;">3,438 active (43.0%)</div>
          </div>
          <div style="width:40px;height:40px;border-radius:10px;background:#262a30;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
            <span class="icon" style="font-size:22px;color:#ffb955;">forum</span>
          </div>
        </div>
        <div class="kpi-card" style="border-color:rgba(255,92,92,.3);cursor:pointer;" onclick="switchTab('map')">
          <div>
            <div class="label-sm" style="color:#ffb3af;margin-bottom:4px;">High-Priority Hotspots</div>
            <div class="metric-val" style="color:#ff5c5c;">31</div>
            <div class="label-sm" style="color:#b9f36a;font-size:.625rem;margin-top:4px;">Click to view on Map →</div>
          </div>
          <div style="width:40px;height:40px;border-radius:10px;background:rgba(255,92,92,.15);display:flex;align-items:center;justify-content:center;flex-shrink:0;">
            <span class="icon icon-fill" style="font-size:22px;color:#ff5c5c;">map</span>
          </div>
        </div>
      </div>

      <!-- Charts Row -->
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:16px;">
        <div class="chart-card">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
            <span class="section-title">Incident Severity</span>
            <span class="label-sm" style="color:#8d937f;">10,000 total</span>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px;">
            <div style="display:flex;align-items:center;gap:8px;">
              <span class="label-sm" style="color:#c3c9b3;width:52px;text-align:right;flex-shrink:0;">CRITICAL</span>
              <div style="flex:1;height:20px;background:#1c2025;border-radius:4px;overflow:hidden;">
                <div style="width:4.7%;height:100%;background:#ff5c5c;border-radius:4px;"></div>
              </div>
              <span class="label-md" style="color:#e0e2ea;width:38px;text-align:right;flex-shrink:0;">470</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
              <span class="label-sm" style="color:#c3c9b3;width:52px;text-align:right;flex-shrink:0;">HIGH</span>
              <div style="flex:1;height:20px;background:#1c2025;border-radius:4px;overflow:hidden;">
                <div style="width:19.85%;height:100%;background:#ffb955;border-radius:4px;"></div>
              </div>
              <span class="label-md" style="color:#e0e2ea;width:38px;text-align:right;flex-shrink:0;">1,985</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
              <span class="label-sm" style="color:#c3c9b3;width:52px;text-align:right;flex-shrink:0;">MEDIUM</span>
              <div style="flex:1;height:20px;background:#1c2025;border-radius:4px;overflow:hidden;">
                <div style="width:37.26%;height:100%;background:#7cb9ff;border-radius:4px;"></div>
              </div>
              <span class="label-md" style="color:#e0e2ea;width:38px;text-align:right;flex-shrink:0;">3,726</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
              <span class="label-sm" style="color:#c3c9b3;width:52px;text-align:right;flex-shrink:0;">LOW</span>
              <div style="flex:1;height:20px;background:#1c2025;border-radius:4px;overflow:hidden;">
                <div style="width:38.19%;height:100%;background:#8d937f;border-radius:4px;"></div>
              </div>
              <span class="label-md" style="color:#e0e2ea;width:38px;text-align:right;flex-shrink:0;">3,819</span>
            </div>
          </div>
        </div>

        <div class="chart-card">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
            <span class="section-title">Road Conditions</span>
            <span class="label-sm" style="color:#8d937f;">1,000 roads</span>
          </div>
          <div style="height:150px;position:relative;">
            <canvas id="roadChart"></canvas>
          </div>
        </div>

        <div class="chart-card">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
            <span class="section-title">Monthly Trajectory</span>
            <span class="label-sm" style="color:#8d937f;">2025 Timeline</span>
          </div>
          <div style="height:150px;">
            <canvas id="trendChart"></canvas>
          </div>
        </div>
      </div>

      <!-- Top Priority Preview Table -->
      <div class="table-card">
        <div style="display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-bottom:1px solid #1c2025;">
          <span class="section-title">Top Priority Locations</span>
          <div style="display:flex;gap:12px;">
            <button onclick="switchTab('map')" style="background:none;border:none;cursor:pointer;color:#ff5c5c;font-family:'Space Grotesk',sans-serif;font-size:.75rem;font-weight:700;">View on Map →</button>
            <button onclick="switchTab('worklist')" style="background:none;border:none;cursor:pointer;color:#b9f36a;font-family:'Space Grotesk',sans-serif;font-size:.75rem;font-weight:600;">View All 31 →</button>
          </div>
        </div>
        <div style="overflow-x:auto;">
          <table style="width:100%;border-collapse:collapse;">
            <thead>
              <tr>
                <th>#</th><th>Location ID</th><th>Score</th><th>Road</th><th>Incidents (Unres)</th><th>Injuries</th><th>Key Evidence</th><th>Action</th>
              </tr>
            </thead>
            <tbody id="overview-rows"></tbody>
          </table>
        </div>
      </div>
    </div><!-- /tab-overview -->


    <!-- ==================== TAB 2: DEDICATED PRIORITY MAP ==================== -->
    <div class="tab-panel" id="tab-map" style="height:calc(100vh - 56px);position:relative;overflow:hidden;">
      <div style="display:flex;height:100%;width:100%;">

        <!-- Problem Navigator Sidebar (Left) -->
        <div id="problem-navigator" style="width:360px;flex-shrink:0;height:100%;background:#101419;border-right:1px solid #1c2025;display:flex;flex-direction:column;z-index:20;">
          
          <!-- Navigator Header -->
          <div style="padding:14px 16px;background:#181c21;border-bottom:1px solid #1c2025;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
              <div style="display:flex;align-items:center;gap:8px;">
                <span class="pulse" style="width:8px;height:8px;border-radius:50%;background:#ff5c5c;box-shadow:0 0 8px #ff5c5c;display:inline-block;"></span>
                <span class="sg" style="font-size:.9rem;font-weight:700;color:#fefff2;letter-spacing:.02em;">PROBLEM NAVIGATOR</span>
              </div>
              <span id="nav-counter" class="label-sm" style="color:#b9f36a;padding:2px 6px;border-radius:4px;background:#262a30;">31 Hotspots</span>
            </div>
            
            <!-- Quick Search Input -->
            <div style="position:relative;margin-bottom:8px;">
              <span class="icon" style="position:absolute;left:8px;top:50%;transform:translateY(-50%);font-size:16px;color:#8d937f;">search</span>
              <input id="nav-search-input" type="text" placeholder="Filter problems (e.g. L0965, Critical)" style="width:100%;background:#0a0f13;border:1px solid #262a30;border-radius:6px;padding:6px 10px 6px 30px;color:#e0e2ea;font-size:.8rem;outline:none;" oninput="filterProblemCards()"/>
            </div>

            <!-- Filter Chips -->
            <div style="display:flex;gap:6px;overflow-x:auto;padding-bottom:2px;">
              <button class="nav-filter-chip active" data-filter="all" onclick="setNavFilter('all', this)" style="padding:3px 8px;border-radius:4px;font-size:10px;font-weight:700;font-family:'Space Grotesk',sans-serif;background:#262a30;color:#b9f36a;border:1px solid #b9f36a;cursor:pointer;">All High (31)</button>
              <button class="nav-filter-chip" data-filter="critical_road" onclick="setNavFilter('critical_road', this)" style="padding:3px 8px;border-radius:4px;font-size:10px;font-weight:700;font-family:'Space Grotesk',sans-serif;background:#181c21;color:#c3c9b3;border:1px solid #262a30;cursor:pointer;">Crit Road</button>
              <button class="nav-filter-chip" data-filter="injuries" onclick="setNavFilter('injuries', this)" style="padding:3px 8px;border-radius:4px;font-size:10px;font-weight:700;font-family:'Space Grotesk',sans-serif;background:#181c21;color:#c3c9b3;border:1px solid #262a30;cursor:pointer;">Injuries &ge; 5</button>
              <button class="nav-filter-chip" data-filter="unresolved" onclick="setNavFilter('unresolved', this)" style="padding:3px 8px;border-radius:4px;font-size:10px;font-weight:700;font-family:'Space Grotesk',sans-serif;background:#181c21;color:#c3c9b3;border:1px solid #262a30;cursor:pointer;">Unres &ge; 5</button>
            </div>
          </div>

          <!-- Problem List Container -->
          <div id="prob-list" style="flex:1;overflow-y:auto;padding:12px;">
            <!-- Dynamically populated -->
          </div>

          <!-- Navigator Footer Info -->
          <div style="padding:10px 14px;background:#181c21;border-top:1px solid #1c2025;display:flex;align-items:center;justify-content:space-between;">
            <span class="label-sm" style="color:#8d937f;font-size:.65rem;">Click card to fly to map</span>
            <button onclick="resetMapView()" style="background:none;border:none;color:#b9f36a;font-size:11px;font-family:'Space Grotesk',sans-serif;cursor:pointer;font-weight:600;">Reset Extent ↺</button>
          </div>
        </div>

        <!-- Map Canvas (Right) -->
        <div id="map-viewport" style="flex:1;height:100%;position:relative;background:#0a0f13;">
          <div id="city-map"></div>

          <!-- Floating Map Mode Controls (Top Left) -->
          <div class="glass-panel" style="position:absolute;top:16px;left:16px;z-index:400;padding:8px 12px;display:flex;align-items:center;gap:8px;">
            <button id="btn-mode-hotspots" onclick="setMapDisplayMode('hotspots')" style="padding:4px 10px;border-radius:6px;background:#262a30;border:1px solid #ff5c5c;color:#ff5c5c;font-size:11px;font-weight:700;font-family:'Space Grotesk',sans-serif;cursor:pointer;">
              🔴 Hotspots (31)
            </button>
            <button id="btn-mode-city" onclick="setMapDisplayMode('city')" style="padding:4px 10px;border-radius:6px;background:transparent;border:1px solid #252c34;color:#c3c9b3;font-size:11px;font-weight:700;font-family:'Space Grotesk',sans-serif;cursor:pointer;">
              🌐 Citywide Grid (1,000)
            </button>
            <span style="width:1px;height:18px;background:#252c34;margin:0 4px;"></span>
            <span class="label-sm" style="color:#8d937f;font-size:.65rem;">Dark Matter Carto Tiles</span>
          </div>

          <!-- Floating Detail Inspector Card (Top Right) -->
          <div id="floating-inspector" class="glass-panel" style="position:absolute;top:16px;right:16px;width:340px;z-index:400;display:none;padding:16px;">
            <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:12px;">
              <div>
                <div style="display:flex;align-items:center;gap:6px;">
                  <span id="insp-id" class="sg" style="font-size:1.15rem;font-weight:700;color:#b9f36a;">L0965</span>
                  <span id="insp-zone" class="label-sm" style="color:#c3c9b3;">ZONE_20</span>
                </div>
                <div id="insp-coords" class="label-sm" style="color:#8d937f;font-size:.625rem;">16.45837° N, 80.40460° E</div>
              </div>
              <button onclick="closeInspector()" style="background:none;border:none;color:#8d937f;cursor:pointer;padding:2px;" onmouseover="this.style.color='#fefff2'" onmouseout="this.style.color='#8d937f'">
                <span class="icon" style="font-size:18px;">close</span>
              </button>
            </div>

            <!-- Score Pill -->
            <div style="display:flex;align-items:center;justify-content:space-between;padding:10px;background:#101419;border-radius:8px;border:1px solid #1c2025;margin-bottom:12px;">
              <div>
                <div class="label-sm" style="color:#8d937f;font-size:.6rem;">PRIORITY SCORE</div>
                <div style="display:flex;align-items:baseline;gap:6px;">
                  <span id="insp-score" class="metric-val" style="color:#ff5c5c;font-size:1.5rem;">78.7</span>
                  <span id="insp-tier" class="badge badge-high">HIGH</span>
                </div>
              </div>
              <div id="insp-road" class="badge road-critical" style="font-size:12px;">CRITICAL ROAD</div>
            </div>

            <!-- Component Scores Breakdown -->
            <div style="margin-bottom:12px;">
              <div class="label-sm" style="color:#8d937f;font-size:.625rem;margin-bottom:6px;">SCORE CONTRIBUTIONS (SUM=100)</div>
              <div style="display:flex;flex-direction:column;gap:5px;font-size:11px;">
                <div style="display:flex;justify-content:space-between;color:#c3c9b3;">
                  <span>Incident Recurrence (20%)</span><strong id="insp-c-inc" style="color:#e0e2ea;">20.0</strong>
                </div>
                <div style="display:flex;justify-content:space-between;color:#c3c9b3;">
                  <span>Safety Burden (25%)</span><strong id="insp-c-burden" style="color:#e0e2ea;">24.8</strong>
                </div>
                <div style="display:flex;justify-content:space-between;color:#c3c9b3;">
                  <span>Unresolved Incidents (15%)</span><strong id="insp-c-unres" style="color:#e0e2ea;">12.5</strong>
                </div>
                <div style="display:flex;justify-content:space-between;color:#c3c9b3;">
                  <span>Road Condition (10%)</span><strong id="insp-c-road" style="color:#e0e2ea;">10.0</strong>
                </div>
              </div>
            </div>

            <!-- Operational Metrics -->
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;">
              <div style="padding:8px;background:#101419;border-radius:6px;border:1px solid #1c2025;">
                <div class="label-sm" style="color:#8d937f;font-size:.6rem;">INCIDENTS</div>
                <div id="insp-inc" class="sg" style="font-size:1rem;font-weight:700;color:#e0e2ea;">19</div>
                <div id="insp-inj" class="label-sm" style="color:#ffb3af;font-size:.6rem;">12 injuries</div>
              </div>
              <div style="padding:8px;background:#101419;border-radius:6px;border:1px solid #1c2025;">
                <div class="label-sm" style="color:#8d937f;font-size:.6rem;">BACKLOG</div>
                <div id="insp-unres" class="sg" style="font-size:1rem;font-weight:700;color:#ffb3af;">2 unres</div>
                <div id="insp-active" class="label-sm" style="color:#ffb955;font-size:.6rem;">7 complaints</div>
              </div>
            </div>

            <!-- Recommended Next Step Intervention -->
            <div style="padding:10px;background:rgba(185,243,106,.08);border:1px solid rgba(185,243,106,.25);border-radius:8px;margin-bottom:12px;">
              <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
                <span class="icon" style="font-size:14px;color:#b9f36a;">build</span>
                <span class="label-sm" style="color:#b9f36a;">RECOMMENDED INTERVENTION</span>
              </div>
              <div id="insp-rec" style="font-size:.75rem;color:#e0e2ea;line-height:1.35;">
                Pavement milling & resurfacing; pedestrian traffic calming audit near school zone.
              </div>
            </div>

            <button onclick="switchTab('worklist')" style="width:100%;padding:8px;background:#262a30;border:1px solid #252c34;border-radius:6px;color:#fefff2;font-family:'Space Grotesk',sans-serif;font-size:.75rem;font-weight:700;cursor:pointer;" onmouseover="this.style.background='#31353b'" onmouseout="this.style.background='#262a30'">
              Inspect in Full Worklist Table →
            </button>
          </div>

          <!-- Floating Bottom Disclaimer & Legend -->
          <div class="glass-panel" style="position:absolute;bottom:16px;left:16px;z-index:400;padding:8px 14px;display:flex;align-items:center;gap:14px;">
            <div style="display:flex;align-items:center;gap:8px;">
              <span class="label-sm" style="color:#8d937f;font-size:.65rem;">PRIORITY TIERS:</span>
              <span style="display:flex;align-items:center;gap:4px;font-size:11px;color:#ff5c5c;font-weight:700;"><span style="width:8px;height:8px;border-radius:50%;background:#ff5c5c;"></span>High (&ge;60)</span>
              <span style="display:flex;align-items:center;gap:4px;font-size:11px;color:#ffb955;font-weight:700;"><span style="width:8px;height:8px;border-radius:50%;background:#ffb955;"></span>Mod (40–59)</span>
              <span style="display:flex;align-items:center;gap:4px;font-size:11px;color:#7cb9ff;font-weight:700;"><span style="width:8px;height:8px;border-radius:50%;background:#7cb9ff;"></span>Lower (&lt;40)</span>
            </div>
            <span style="width:1px;height:14px;background:#252c34;"></span>
            <div class="label-sm" style="color:#8d937f;font-size:.6rem;">
              ⚠️ SIMULATED GEODATA · DEMO PURPOSES ONLY
            </div>
          </div>
        </div>
      </div>
    </div><!-- /tab-map -->


    <!-- ==================== TAB 3: WORKLIST ==================== -->
    <div class="tab-panel" id="tab-worklist" style="padding:20px;">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:8px;">
        <div>
          <div class="sg" style="font-size:1.1rem;font-weight:700;color:#fefff2;">Priority Worklist</div>
          <div class="label-sm" style="color:#8d937f;font-size:.625rem;margin-top:4px;">High-tier locations · Score ≥ 60 · Sorted by priority score desc · Heuristic Score v1.0</div>
        </div>
        <div class="label-sm" style="color:#c3c9b3;padding:8px 12px;background:#1c2025;border-radius:8px;">
          Showing <span style="color:#b9f36a;font-weight:700;">31</span> locations · 428 Moderate · 541 Lower
        </div>
      </div>
      <div class="table-card">
        <div class="disclaimer-bar">
          <span class="icon" style="font-size:14px;color:#ffb3af;">info</span>
          <span class="label-sm" style="color:#c3c9b3;font-size:.625rem;"><strong style="color:#e0e2ea;">Synthetic demo data:</strong> Scores are illustrative and not for real-world public-safety decisions. Score = 7-component weighted percentile rank v1.0.</span>
        </div>
        <div style="overflow-x:auto;">
          <table style="width:100%;border-collapse:collapse;">
            <thead>
              <tr>
                <th>#</th><th>Location</th><th>Zone</th><th>Score</th><th>Road Cond.</th><th>Incidents</th><th>Unres.</th><th>Injuries</th><th>Active Comp.</th><th>Key Evidence</th><th>Action</th>
              </tr>
            </thead>
            <tbody id="worklist-rows"></tbody>
          </table>
        </div>
        <div style="padding:12px 16px;text-align:center;border-top:1px solid #1c2025;">
          <span class="label-sm" style="color:#8d937f;">Top 31 High-tier locations shown · Score range: 60.0 – 78.7 · All scores are illustrative</span>
        </div>
      </div>
    </div><!-- /tab-worklist -->


    <!-- ==================== TAB 4: ZONES ==================== -->
    <div class="tab-panel" id="tab-zones" style="padding:20px;">
      <div style="margin-bottom:16px;">
        <div class="sg" style="font-size:1.1rem;font-weight:700;color:#fefff2;">Zone Comparison</div>
        <div class="label-sm" style="color:#8d937f;font-size:.625rem;margin-top:4px;">Per-location averages · Zones have 43–65 locations (unequal sizes — raw totals not fair for comparison)</div>
      </div>
      <div class="chart-card" style="margin-bottom:16px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
          <span class="section-title">Avg Priority Score by Zone (Per-Location Average)</span>
          <span class="label-sm" style="color:#8d937f;">Synthetic data · Score v1.0</span>
        </div>
        <div style="height:220px;"><canvas id="zoneChart"></canvas></div>
      </div>
      <div class="table-card">
        <div class="disclaimer-bar">
          <span class="icon" style="font-size:14px;color:#ffb3af;">info</span>
          <span class="label-sm" style="color:#c3c9b3;font-size:.625rem;">Synthetic data · All values computed from CSV · Per-location averages shown · Zone size context included</span>
        </div>
        <div style="overflow-x:auto;">
          <table style="width:100%;border-collapse:collapse;">
            <thead>
              <tr>
                <th>Zone</th><th>Locations</th><th>Avg Score</th><th>Avg Inc/Loc</th><th>Avg Unres/Loc</th><th>Poor+Crit Road %</th>
              </tr>
            </thead>
            <tbody id="zone-rows"></tbody>
          </table>
        </div>
      </div>
    </div><!-- /tab-zones -->

  </main>
</div>

<script>
// ===== EMBEDDED REAL CSV DATA =====
const TOP31 = [
    """ + top31_js + """
];

const ALL_LOCS = """ + all_locs_js + """;

const ZONE_STATS = [
  {zone:"ZONE_01",locs:53,avg_score:46.4,avg_inc:10.0,avg_unres:2.9,pct_poor_crit:38},
  {zone:"ZONE_02",locs:48,avg_score:45.3,avg_inc:9.8,avg_unres:2.7,pct_poor_crit:38},
  {zone:"ZONE_03",locs:50,avg_score:47.3,avg_inc:10.2,avg_unres:3.0,pct_poor_crit:40},
  {zone:"ZONE_04",locs:51,avg_score:45.8,avg_inc:9.8,avg_unres:2.8,pct_poor_crit:39},
  {zone:"ZONE_05",locs:53,avg_score:46.4,avg_inc:10.3,avg_unres:2.9,pct_poor_crit:36},
  {zone:"ZONE_06",locs:50,avg_score:46.8,avg_inc:10.0,avg_unres:2.9,pct_poor_crit:36},
  {zone:"ZONE_07",locs:48,avg_score:46.2,avg_inc:10.3,avg_unres:2.9,pct_poor_crit:35},
  {zone:"ZONE_08",locs:49,avg_score:45.7,avg_inc:9.6,avg_unres:2.8,pct_poor_crit:39},
  {zone:"ZONE_09",locs:46,avg_score:47.3,avg_inc:10.4,avg_unres:3.0,pct_poor_crit:41},
  {zone:"ZONE_10",locs:50,avg_score:46.1,avg_inc:9.8,avg_unres:2.9,pct_poor_crit:38},
  {zone:"ZONE_11",locs:65,avg_score:46.3,avg_inc:9.9,avg_unres:2.8,pct_poor_crit:40},
  {zone:"ZONE_12",locs:54,avg_score:46.6,avg_inc:10.0,avg_unres:2.8,pct_poor_crit:42},
  {zone:"ZONE_13",locs:53,avg_score:45.7,avg_inc:9.7,avg_unres:2.7,pct_poor_crit:57},
  {zone:"ZONE_14",locs:49,avg_score:46.4,avg_inc:9.8,avg_unres:2.8,pct_poor_crit:44},
  {zone:"ZONE_15",locs:50,avg_score:47.2,avg_inc:10.4,avg_unres:2.9,pct_poor_crit:42},
  {zone:"ZONE_16",locs:48,avg_score:45.9,avg_inc:9.7,avg_unres:2.7,pct_poor_crit:43},
  {zone:"ZONE_17",locs:48,avg_score:46.0,avg_inc:9.9,avg_unres:2.8,pct_poor_crit:42},
  {zone:"ZONE_18",locs:46,avg_score:47.3,avg_inc:10.4,avg_unres:2.9,pct_poor_crit:41},
  {zone:"ZONE_19",locs:43,avg_score:46.2,avg_inc:10.0,avg_unres:2.8,pct_poor_crit:41},
  {zone:"ZONE_20",locs:62,avg_score:46.7,avg_inc:9.9,avg_unres:2.8,pct_poor_crit:40}
];

const MONTH_INC = """ + month_inc_js + """;
const MONTH_COMP = """ + month_comp_js + """;

// ===== SIDEBAR CLOSE / COLLAPSE FEATURE =====
function toggleSidebar() {
  document.body.classList.toggle('sidebar-collapsed');
  const isCollapsed = document.body.classList.contains('sidebar-collapsed');
  localStorage.setItem('metrix_sidebar_collapsed', isCollapsed ? '1' : '0');
  
  const innerIcon = document.getElementById('sidebar-icon-inner');
  if (innerIcon) innerIcon.textContent = isCollapsed ? 'chevron_right' : 'menu_open';
  
  const topbarIcon = document.getElementById('topbar-toggle-icon');
  if (topbarIcon) topbarIcon.textContent = isCollapsed ? 'menu_open' : 'menu';

  // Resize map tiles smoothly
  if (window.map) {
    setTimeout(() => { window.map.invalidateSize(); }, 280);
  }
}

// Restore saved sidebar preference
if (localStorage.getItem('metrix_sidebar_collapsed') === '1') {
  document.body.classList.add('sidebar-collapsed');
  const innerIcon = document.getElementById('sidebar-icon-inner');
  if (innerIcon) innerIcon.textContent = 'chevron_right';
  const topbarIcon = document.getElementById('topbar-toggle-icon');
  if (topbarIcon) topbarIcon.textContent = 'menu_open';
}

// ===== HELPERS =====
function roadBadge(c){
  const m={Critical:'road-critical',Poor:'road-poor',Fair:'road-fair',Good:'road-good'};
  return `<span class="badge ${m[c]||''}">${c.toUpperCase()}</span>`;
}
function tierBadge(s){
  if(s>=60) return '<span class="badge badge-high">HIGH</span>';
  if(s>=40) return '<span class="badge badge-mod">MOD</span>';
  return '<span class="badge badge-lower">LOWER</span>';
}
function driver(loc){
  if(loc.road_condition==='Critical') return '🛣️ Critical road surface';
  if(loc.total_injuries>=7) return '🚑 High injury count (' + loc.total_injuries + ')';
  if(loc.crit_inc>=2) return '⚠️ Multiple critical incidents';
  if(loc.unresolved>=6) return '📋 High unresolved backlog';
  if(loc.high_inc>=6) return '⚡ Many High-severity incidents';
  if(loc.active_comp>=7) return '💬 High active complaints backlog';
  if(loc.near_school===1&&loc.pedestrian_activity==='High') return '🏫 School zone + High foot traffic';
  return '📊 Compounding risk factors';
}
function recommendIntervention(loc){
  if(loc.road_condition==='Critical' && loc.total_injuries>=6) {
    return 'Urgent pavement resurfacing, geometric re-alignment & traffic-calming safety barriers.';
  }
  if(loc.road_condition==='Critical') {
    return 'High-priority full road surface rehabilitation and structural base repair.';
  }
  if(loc.unresolved>=5) {
    return 'Dispatch dedicated municipal remediation team to eliminate persistent backlog.';
  }
  if(loc.total_injuries>=6) {
    return 'Deploy automated speed enforcement & enhance intersection lighting and signage.';
  }
  if(loc.active_comp>=6) {
    return 'Civil engineering field audit to investigate recurrent citizen drainage & pothole complaints.';
  }
  return 'Routine preventive maintenance & scheduled quarterly infrastructure review.';
}

// ===== RENDER OVERVIEW ROWS =====
function renderOverviewRows(){
  const t=document.getElementById('overview-rows');
  t.innerHTML=TOP31.slice(0,8).map(loc=>`
    <tr class="data-row" onclick="viewLocationOnMap('${loc.location_id}')">
      <td class="label-md" style="color:#8d937f;">${loc.rank}</td>
      <td><div class="label-lg" style="color:#b9f36a;">${loc.location_id}</div><div class="label-sm" style="color:#8d937f;font-size:.6rem;">${loc.zone} · ${loc.road_type}</div></td>
      <td><div style="display:flex;align-items:center;gap:6px;"><span class="sg" style="font-size:1rem;font-weight:700;color:#e0e2ea;">${loc.score}</span>${tierBadge(loc.score)}</div><div class="score-bar" style="width:${loc.score}%;margin-top:3px;"></div></td>
      <td>${roadBadge(loc.road_condition)}</td>
      <td class="label-md" style="color:#e0e2ea;">${loc.incident_count} <span style="color:#8d937f;">(${loc.unresolved} unres)</span></td>
      <td class="label-md" style="color:${loc.total_injuries>=5?'#ffb3af':'#e0e2ea'};">${loc.total_injuries}</td>
      <td class="label-sm" style="color:#c3c9b3;max-width:200px;white-space:normal;">${driver(loc)}</td>
      <td><button onclick="event.stopPropagation();viewLocationOnMap('${loc.location_id}')" style="background:#262a30;border:1px solid #1c2025;color:#b9f36a;font-size:11px;padding:3px 8px;border-radius:4px;cursor:pointer;font-family:'Space Grotesk',sans-serif;font-weight:700;">MAP ↗</button></td>
    </tr>
  `).join('');
}

// ===== RENDER WORKLIST =====
function renderWorklist(){
  const t=document.getElementById('worklist-rows');
  t.innerHTML=TOP31.map(loc=>`
    <tr class="data-row" onclick="viewLocationOnMap('${loc.location_id}')">
      <td class="label-md" style="color:#8d937f;">${loc.rank}</td>
      <td><div class="label-lg" style="color:#b9f36a;">${loc.location_id}</div><div class="label-sm" style="color:#8d937f;font-size:.6rem;">${loc.road_type}</div></td>
      <td class="label-md" style="color:#e0e2ea;">${loc.zone}</td>
      <td><div style="display:flex;align-items:center;gap:6px;"><span class="sg" style="font-size:1rem;font-weight:700;color:#e0e2ea;">${loc.score}</span>${tierBadge(loc.score)}</div></td>
      <td>${roadBadge(loc.road_condition)}</td>
      <td class="label-md" style="color:#e0e2ea;">${loc.incident_count}</td>
      <td class="label-md" style="color:${loc.unresolved>=5?'#ffb3af':'#e0e2ea'};">${loc.unresolved}</td>
      <td class="label-md" style="color:${loc.total_injuries>=5?'#ffb3af':'#e0e2ea'};">${loc.total_injuries}</td>
      <td class="label-md" style="color:#e0e2ea;">${loc.active_comp}</td>
      <td class="label-sm" style="color:#c3c9b3;max-width:180px;white-space:normal;">${driver(loc)}</td>
      <td><button onclick="event.stopPropagation();viewLocationOnMap('${loc.location_id}')" style="background:#262a30;border:1px solid #1c2025;color:#ff5c5c;font-size:11px;padding:3px 8px;border-radius:4px;cursor:pointer;font-family:'Space Grotesk',sans-serif;font-weight:700;">LOCATE ↗</button></td>
    </tr>
  `).join('');
}

// ===== RENDER ZONES =====
function renderZones(){
  const sorted=[...ZONE_STATS].sort((a,b)=>b.avg_score-a.avg_score);
  const t=document.getElementById('zone-rows');
  t.innerHTML=sorted.map(z=>`
    <tr class="data-row">
      <td class="label-lg" style="color:#b9f36a;">${z.zone}</td>
      <td class="label-md" style="color:#8d937f;">${z.locs}</td>
      <td>
        <div style="display:flex;align-items:center;gap:8px;">
          <span class="sg" style="font-size:.95rem;font-weight:700;color:#e0e2ea;">${z.avg_score.toFixed(1)}</span>
          <div style="width:80px;height:5px;background:#1c2025;border-radius:99px;overflow:hidden;"><div style="width:${z.avg_score}%;height:100%;background:#b9f36a;border-radius:99px;"></div></div>
        </div>
      </td>
      <td class="label-md" style="color:#e0e2ea;">${z.avg_inc.toFixed(1)}</td>
      <td class="label-md" style="color:#e0e2ea;">${z.avg_unres.toFixed(1)}</td>
      <td><span class="badge ${z.pct_poor_crit>=50?'road-critical':z.pct_poor_crit>=45?'road-poor':'road-fair'}">${z.pct_poor_crit}%</span></td>
    </tr>
  `).join('');
}

// ===== DEDICATED MAP & PROBLEM NAVIGATOR FEATURE =====
let map = null;
let markersLayer = null;
let currentFilter = 'all';
let currentDisplayMode = 'hotspots'; // 'hotspots' or 'city'
let selectedLocationId = null;
const locMarkerMap = {};

function initMapIfNeeded() {
  if (map) {
    map.invalidateSize();
    return;
  }
  
  // Center on simulation coordinates: approx 16.45 N, 80.53 E
  map = L.map('city-map', {
    zoomControl: false,
    attributionControl: false
  }).setView([16.45, 80.53], 11);

  L.control.zoom({ position: 'bottomright' }).addTo(map);

  // CartoDB Dark Matter tile layer
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(map);

  markersLayer = L.layerGroup().addTo(map);

  renderProblemCards();
  plotMarkers();
}

function plotMarkers() {
  if (!markersLayer) return;
  markersLayer.clearLayers();

  if (currentDisplayMode === 'hotspots') {
    // Plot top 31 hotspots
    TOP31.forEach(loc => {
      const isSelected = loc.location_id === selectedLocationId;
      const marker = L.circleMarker([loc.latitude, loc.longitude], {
        radius: isSelected ? 12 : 9,
        color: '#ff5c5c',
        weight: isSelected ? 3 : 2,
        fillColor: '#ff5c5c',
        fillOpacity: 0.85
      });

      marker.bindPopup(`
        <div style="min-width:180px;">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
            <strong style="color:#b9f36a;font-family:'Space Grotesk',sans-serif;font-size:14px;">${loc.location_id}</strong>
            <span class="badge badge-high">${loc.score}</span>
          </div>
          <div style="color:#c3c9b3;font-size:11px;margin-bottom:4px;">${loc.zone} · ${loc.road_condition} Road</div>
          <div style="font-size:11px;color:#e0e2ea;margin-bottom:8px;">${driver(loc)}</div>
          <button onclick="selectProblemCard('${loc.location_id}')" style="width:100%;background:#b9f36a;color:#101419;border:none;padding:4px 8px;border-radius:4px;font-weight:700;font-size:11px;cursor:pointer;font-family:'Space Grotesk',sans-serif;">INSPECT DETAILS</button>
        </div>
      `);

      marker.on('click', () => {
        selectProblemCard(loc.location_id, false);
      });

      locMarkerMap[loc.location_id] = marker;
      markersLayer.addLayer(marker);
    });
  } else {
    // Plot citywide points
    ALL_LOCS.forEach(pt => {
      const [id, lat, lon, sc, tier, road, inc, unres, inj, act, z, rank] = pt;
      const col = sc >= 60 ? '#ff5c5c' : sc >= 40 ? '#ffb955' : '#7cb9ff';
      const rad = sc >= 60 ? 7 : 4;
      const marker = L.circleMarker([lat, lon], {
        radius: rad,
        color: col,
        weight: 1,
        fillColor: col,
        fillOpacity: sc >= 60 ? 0.9 : 0.6
      });

      marker.bindPopup(`
        <div style="min-width:160px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
            <strong style="color:#b9f36a;">${id}</strong>
            <span style="font-weight:700;color:${col};">${sc} (${tier})</span>
          </div>
          <div style="font-size:11px;color:#c3c9b3;">${z} · ${road}</div>
          <div style="font-size:11px;color:#e0e2ea;">${inc} incidents · ${inj} injuries</div>
        </div>
      `);
      markersLayer.addLayer(marker);
    });
  }
}

function renderProblemCards() {
  const container = document.getElementById('prob-list');
  const q = (document.getElementById('nav-search-input')?.value || '').trim().toUpperCase();

  let list = TOP31.filter(loc => {
    if (q && !loc.location_id.toUpperCase().includes(q) && !loc.zone.toUpperCase().includes(q)) return false;
    if (currentFilter === 'critical_road' && loc.road_condition !== 'Critical') return false;
    if (currentFilter === 'injuries' && loc.total_injuries < 5) return false;
    if (currentFilter === 'unresolved' && loc.unresolved < 5) return false;
    return true;
  });

  const countEl = document.getElementById('nav-counter');
  if (countEl) countEl.textContent = `${list.length} Problems`;

  if (list.length === 0) {
    container.innerHTML = `<div style="padding:20px;text-align:center;color:#8d937f;font-size:.8rem;">No problems matching active filter</div>`;
    return;
  }

  container.innerHTML = list.map(loc => `
    <div class="prob-card ${loc.location_id === selectedLocationId ? 'active' : ''}" id="card-${loc.location_id}" onclick="selectProblemCard('${loc.location_id}', true)">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;">
        <div style="display:flex;align-items:center;gap:6px;">
          <span class="label-md" style="color:#8d937f;">#${loc.rank}</span>
          <span class="sg" style="font-size:.95rem;font-weight:700;color:#fefff2;">${loc.location_id}</span>
          <span class="label-sm" style="color:#8d937f;font-size:.65rem;">${loc.zone}</span>
        </div>
        <div style="display:flex;align-items:center;gap:4px;">
          <span class="sg" style="font-size:.9rem;font-weight:700;color:#ff5c5c;">${loc.score}</span>
          ${tierBadge(loc.score)}
        </div>
      </div>

      <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;flex-wrap:wrap;">
        ${roadBadge(loc.road_condition)}
        <span class="badge" style="background:#1c2025;color:#e0e2ea;border-color:#262a30;">${loc.incident_count} Incidents</span>
        <span class="badge" style="background:#1c2025;color:${loc.unresolved >= 5 ? '#ffb3af' : '#c3c9b3'};border-color:#262a30;">${loc.unresolved} Unres</span>
        <span class="badge" style="background:#1c2025;color:${loc.total_injuries >= 5 ? '#ffb3af' : '#c3c9b3'};border-color:#262a30;">${loc.total_injuries} Inj</span>
      </div>

      <div style="font-size:11px;color:#c3c9b3;line-height:1.3;">
        ${driver(loc)}
      </div>
    </div>
  `).join('');
}

function setNavFilter(filterName, btn) {
  currentFilter = filterName;
  document.querySelectorAll('.nav-filter-chip').forEach(b => {
    b.style.background = '#181c21';
    b.style.color = '#c3c9b3';
    b.style.borderColor = '#262a30';
  });
  btn.style.background = '#262a30';
  btn.style.color = '#b9f36a';
  btn.style.borderColor = '#b9f36a';
  renderProblemCards();
}

function filterProblemCards() {
  renderProblemCards();
}

function selectProblemCard(locId, flyTo = true) {
  selectedLocationId = locId;
  const loc = TOP31.find(l => l.location_id === locId);
  if (!loc) return;

  // Highlight card
  document.querySelectorAll('.prob-card').forEach(c => c.classList.remove('active'));
  const card = document.getElementById(`card-${locId}`);
  if (card) {
    card.classList.add('active');
    card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // Open inspector
  const insp = document.getElementById('floating-inspector');
  if (insp) {
    insp.style.display = 'block';
    document.getElementById('insp-id').textContent = loc.location_id;
    document.getElementById('insp-zone').textContent = `${loc.zone} · ${loc.road_type}`;
    document.getElementById('insp-coords').textContent = `${loc.latitude.toFixed(5)}° N, ${loc.longitude.toFixed(5)}° E`;
    document.getElementById('insp-score').textContent = loc.score;
    document.getElementById('insp-road').textContent = `${loc.road_condition.toUpperCase()} ROAD`;
    document.getElementById('insp-road').className = `badge ${loc.road_condition === 'Critical' ? 'road-critical' : 'road-poor'}`;
    
    document.getElementById('insp-c-inc').textContent = `${loc.comp_inc.toFixed(1)} / 20`;
    document.getElementById('insp-c-burden').textContent = `${loc.comp_burden.toFixed(1)} / 25`;
    document.getElementById('insp-c-unres').textContent = `${loc.comp_unres.toFixed(1)} / 15`;
    document.getElementById('insp-c-road').textContent = `${loc.comp_road.toFixed(1)} / 10`;

    document.getElementById('insp-inc').textContent = `${loc.incident_count} (${loc.crit_inc} Critical)`;
    document.getElementById('insp-inj').textContent = `${loc.total_injuries} injuries reported`;
    document.getElementById('insp-unres').textContent = `${loc.unresolved} unresolved`;
    document.getElementById('insp-active').textContent = `${loc.active_comp} active complaints`;

    document.getElementById('insp-rec').textContent = recommendIntervention(loc);
  }

  // Fly on map
  if (flyTo && map) {
    map.flyTo([loc.latitude, loc.longitude], 14, { duration: 0.8 });
    const marker = locMarkerMap[locId];
    if (marker) {
      setTimeout(() => marker.openPopup(), 850);
    }
  }
}

function closeInspector() {
  const insp = document.getElementById('floating-inspector');
  if (insp) insp.style.display = 'none';
  selectedLocationId = null;
  document.querySelectorAll('.prob-card').forEach(c => c.classList.remove('active'));
}

function setMapDisplayMode(mode) {
  currentDisplayMode = mode;
  const btnHot = document.getElementById('btn-mode-hotspots');
  const btnCity = document.getElementById('btn-mode-city');
  if (mode === 'hotspots') {
    btnHot.style.background = '#262a30';
    btnHot.style.borderColor = '#ff5c5c';
    btnHot.style.color = '#ff5c5c';
    btnCity.style.background = 'transparent';
    btnCity.style.borderColor = '#252c34';
    btnCity.style.color = '#c3c9b3';
  } else {
    btnCity.style.background = '#262a30';
    btnCity.style.borderColor = '#b9f36a';
    btnCity.style.color = '#b9f36a';
    btnHot.style.background = 'transparent';
    btnHot.style.borderColor = '#252c34';
    btnHot.style.color = '#c3c9b3';
  }
  plotMarkers();
}

function resetMapView() {
  if (!map) return;
  map.flyTo([16.45, 80.53], 11, { duration: 0.8 });
  closeInspector();
}

function viewLocationOnMap(locId) {
  switchTab('map');
  setTimeout(() => {
    selectProblemCard(locId, true);
  }, 200);
}

// ===== CHARTS =====
Chart.defaults.color='#c3c9b3';
Chart.defaults.font.family="'Space Grotesk', sans-serif";
Chart.defaults.font.size=11;

function initRoadChart(){
  new Chart(document.getElementById('roadChart'),{
    type:'doughnut',
    data:{labels:['Critical','Poor','Fair','Good'],datasets:[{data:[78,309,383,230],backgroundColor:['#ff5c5c','#ffb955','#7cb9ff','#b9f36a'],borderColor:'#0a0f13',borderWidth:2,hoverOffset:4}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'68%',plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` ${c.label}: ${c.raw} (${((c.raw/1000)*100).toFixed(1)}%)`}}}}
  });
}

function initTrendChart(){
  const months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  new Chart(document.getElementById('trendChart'),{
    type:'bar',
    data:{labels:months,datasets:[
      {label:'Incidents',data:MONTH_INC,backgroundColor:'rgba(185,243,106,.2)',borderColor:'#b9f36a',borderWidth:1.5,borderRadius:3,order:2},
      {label:'Complaints',data:MONTH_COMP,type:'line',borderColor:'#ffb955',backgroundColor:'rgba(255,185,85,.08)',borderWidth:2,pointRadius:3,pointBackgroundColor:'#ffb955',tension:.3,fill:true,order:1}
    ]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{mode:'index',intersect:false}},scales:{x:{grid:{color:'rgba(67,73,56,.4)'},ticks:{color:'#c3c9b3'}},y:{grid:{color:'rgba(67,73,56,.4)'},ticks:{color:'#c3c9b3'},min:500}}}
  });
}

let zoneChartInit=false;
function initZoneChart(){
  if(zoneChartInit)return; zoneChartInit=true;
  const sorted=[...ZONE_STATS].sort((a,b)=>b.avg_score-a.avg_score);
  new Chart(document.getElementById('zoneChart'),{
    type:'bar',
    data:{labels:sorted.map(z=>z.zone.replace('ZONE_','Z')),datasets:[{label:'Avg Score',data:sorted.map(z=>z.avg_score),backgroundColor:sorted.map(z=>z.avg_score>=47?'rgba(185,243,106,.5)':'rgba(185,243,106,.2)'),borderColor:'#b9f36a',borderWidth:1,borderRadius:3}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>` Avg Score: ${c.raw.toFixed(1)} — ${sorted[c.dataIndex].locs} locations`}}},scales:{x:{grid:{display:false},ticks:{color:'#c3c9b3',font:{size:10}}},y:{grid:{color:'rgba(67,73,56,.4)'},ticks:{color:'#c3c9b3'},min:44,max:49}}}
  });
}

// ===== TAB NAVIGATION =====
function switchTab(tabId){
  document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b=>b.classList.remove('active'));
  
  const targetPanel = document.getElementById('tab-'+tabId);
  if (targetPanel) {
    targetPanel.classList.add('active');
    if (tabId === 'map') {
      targetPanel.style.display = 'block';
    } else {
      targetPanel.style.display = 'block';
    }
  }

  const nb=document.getElementById('nav-'+tabId);
  if(nb) nb.classList.add('active');
  
  if(tabId==='zones') setTimeout(initZoneChart, 50);
  if(tabId==='map') {
    setTimeout(initMapIfNeeded, 100);
  }
}

// ===== SEARCH BAR =====
document.getElementById('search-input').addEventListener('input',function(){
  const q=this.value.trim().toUpperCase();
  if(!q) return;
  const match = TOP31.find(l=>l.location_id.toUpperCase().includes(q));
  if(match) {
    viewLocationOnMap(match.location_id);
  }
});

// ===== INITIALIZE =====
renderOverviewRows();
renderWorklist();
renderZones();
initRoadChart();
initTrendChart();
</script>
</body>
</html>
"""

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Dashboard updated with Map feature and Closeable Sidebar, size:", len(html), "bytes")
