# -*- coding: utf-8 -*-
"""Strip scoped layout rules — golden-ratio.css owns spacing/grid globally."""
from pathlib import Path

root = Path(__file__).resolve().parent / 'src' / 'components'

patches = [
    (
        root / 'Home.vue',
        '.home-wrap { display:flex; gap:24px; padding:20px; align-items:flex-start }\n.home-sidebar { width:320px; display:flex; flex-direction:column; gap:16px }\n',
        '',
    ),
    (
        root / 'Home.vue',
        '.home-main { flex:1; display:flex; flex-direction:column; gap:18px }\n',
        '',
    ),
    (
        root / 'Home.vue',
        '.large-hero .carousel { height:360px; border-radius:12px; overflow:hidden; position:relative }\n.large-hero .slide img { width:100%; height:360px; object-fit:cover; display:block; filter:brightness(.95) }\n',
        '.large-hero .slide img { width:100%; object-fit:cover; display:block; filter:brightness(.95) }\n',
    ),
    (
        root / 'Home.vue',
        '.home-bottom-grid { display:grid; grid-template-columns: 1fr 360px; gap:18px }\n',
        '',
    ),
    (
        root / 'Home.vue',
        '.calendar-card, .announce-card { border-radius:10px }\n',
        '',
    ),
    (
        root / 'Home.vue',
        '.mini-calendar { padding:12px }\n',
        '',
    ),
    (
        root / 'Home.vue',
        '.days-grid { display:grid; grid-template-columns: repeat(7,1fr); gap:6px }\n.day { min-height:56px; border-radius:8px; background:var(--card-bg); display:flex; align-items:flex-start; justify-content:flex-end; padding:8px; border:1px solid rgba(0,0,0,0.03) }\n',
        '.days-grid { display:grid; grid-template-columns: repeat(7,1fr); }\n.day { background:var(--card-bg); display:flex; align-items:flex-start; justify-content:flex-end; border:1px solid rgba(0,0,0,0.03) }\n',
    ),
    (
        root / 'Home.vue',
        '.announcement-item { padding: 12px; border-bottom: 1px solid rgba(0,0,0,0.05); }\n',
        '.announcement-item { border-bottom: 1px solid rgba(0,0,0,0.05); }\n',
    ),
    (
        root / 'Home.vue',
        '@media (max-width: 900px) {\n  .home-wrap { flex-direction:column }\n  .home-sidebar { width:100%; flex-direction:row; overflow:auto }\n  .home-bottom-grid { grid-template-columns: 1fr }\n}\n',
        '',
    ),
    (
        root / 'UserList.vue',
        """.search-bar {
  max-width: 420px;
  margin-bottom: 16px;
}

.user-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 10px;
}

""",
        """.search-bar {
  max-width: 420px;
}

""",
    ),
    (
        root / 'GameAdmin.vue',
        '.stat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; margin-bottom: 24px; }\n.stat-card {\n  padding: 16px;\n  border: 1px solid var(--border);\n  border-radius: var(--card-radius);\n  background: var(--card-bg);\n  display: flex;\n  flex-direction: column;\n  gap: 4px;\n}\n',
        '.stat-card {\n  border: 1px solid var(--border);\n  border-radius: var(--card-radius);\n  background: var(--card-bg);\n  display: flex;\n  flex-direction: column;\n  gap: 4px;\n}\n',
    ),
    (
        root / 'admin' / 'PlatformDashboard.vue',
        """.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
}

/* 图表区 */
.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.chart-container {
  background: white;
  padding: 20px;
  border-radius: 10px;
""",
        """.chart-container {
  background: white;
  border-radius: 10px;
""",
    ),
    (
        root / 'admin' / 'PlatformDashboard.vue',
        """.todo-stats {
  background: white;
  padding: 20px;
  border-radius: 10px;
""",
        """.todo-stats {
  background: white;
  border-radius: 10px;
""",
    ),
    (
        root / 'admin' / 'PlatformDashboard.vue',
        """.active-users {
  background: white;
  padding: 20px;
  border-radius: 10px;
""",
        """.active-users {
  background: white;
  border-radius: 10px;
""",
    ),
    (
        root / 'admin' / 'MetricCard.vue',
        """.metric-card {
  background: white;
  padding: 20px;
  border-radius: 10px;
""",
        """.metric-card {
  background: white;
  border-radius: 10px;
""",
    ),
    (
        root / 'MyProfile.vue',
        """.myprofile-wrap {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

""",
        '',
    ),
    (
        root / 'MyProfile.vue',
        """.profile-header {
  display: flex;
  gap: 32px;
  align-items: flex-start;
  padding: 24px 0;
}

""",
        """.profile-header {
  display: flex;
  align-items: flex-start;
  padding: var(--fib-34) 0;
}

""",
    ),
    (
        root / 'MyProfile.vue',
        """.profile-stats {
  display: flex;
  gap: 32px;
  margin-bottom: 16px;
}

""",
        """.profile-stats {
  display: flex;
  margin-bottom: var(--fib-21);
}

""",
    ),
    (
        root / 'MyProfile.vue',
        """.profile-content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

""",
        '',
    ),
    (
        root / 'MyProfile.vue',
        """@media (max-width: 768px) {
  .myprofile-wrap {
    padding: 12px;
  }

  .profile-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 20px;
  }

""",
        """@media (max-width: 768px) {
  .profile-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: var(--fib-21);
  }

""",
    ),
    (
        root / 'MyProfile.vue',
        """  .profile-content-grid {
    grid-template-columns: 1fr;
  }
""",
        '',
    ),
    (
        root / 'UserPublicProfile.vue',
        '.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }\n.stat-box { text-align: center; padding: 16px; background: var(--hover); border-radius: var(--card-radius); }\n',
        '.stat-box { text-align: center; background: var(--hover); border-radius: var(--card-radius); }\n',
    ),
    (
        root / 'UserPublicProfile.vue',
        '.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }\n',
        '',
    ),
    (
        root / 'UserPublicProfile.vue',
        '@media (max-width: 900px) {\n  .charts-row { grid-template-columns: 1fr; }\n}\n',
        '',
    ),
    (
        root / 'GameDetail.vue',
        """.game-detail-page {
  width: 100%;
  margin: 0;
  min-height: calc(100vh - var(--nav-height, 56px) - 52px);
  padding: 24px 28px 48px;
  box-sizing: border-box;
}

""",
        """.game-detail-page {
  width: 100%;
  margin: 0;
  min-height: calc(100vh - var(--nav-height, 56px) - 52px);
  box-sizing: border-box;
}

""",
    ),
    (
        root / 'GameDetail.vue',
        """.detail-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 32px;
  max-width: none;
  width: 100%;
  margin: 0;
  align-items: start;
}

""",
        '',
    ),
]

for path, old, new in patches:
    text = path.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'mismatch in {path.name}: missing block')
    path.write_text(text.replace(old, new, 1), encoding='utf-8', newline='\n')
    print(f'patched {path.name}')

print('all golden global patches applied')
