import os
import pymysql
from urllib.parse import urlparse
from pprint import pprint

url = os.environ.get('NEPU_DATABASE_URL', 'mysql+pymysql://neepu_user:123456@localhost:3306/neepu')
if url.startswith('mysql+pymysql://'):
    url = url.replace('mysql+pymysql://', 'mysql://', 1)

parsed = urlparse(url)
conn = pymysql.connect(
    host=parsed.hostname or 'localhost',
    port=parsed.port or 3306,
    user=parsed.username or 'root',
    password=parsed.password or '',
    database=(parsed.path or '/neepu').lstrip('/'),
    charset='utf8mb4',
)

with conn.cursor() as cur:
    cur.execute('SHOW TABLES')
    tables = [r[0] for r in cur.fetchall()]
    print('tables:')
    pprint(tables)

    for table in ['ctf_challenge', 'game_challenge']:
        if table in tables:
            cur.execute(f"select id,title,docker_image,docker_port,challenge_type from {table} order by id desc limit 20")
            print(f"\n{table} recent:")
            pprint(cur.fetchall())

conn.close()
