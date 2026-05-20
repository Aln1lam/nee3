import sqlite3
from pprint import pprint

conn = sqlite3.connect('e:/neepu/dev.db')
cur = conn.cursor()
cur.execute("select name from sqlite_master where type='table'")
print('tables:')
pprint([r[0] for r in cur.fetchall()])

# try common table names
for table in ['ctf_challenge', 'game_challenge', 'challenge', 'ctf_game_challenge']:
    try:
        cur.execute(f"select id,title,docker_image,docker_port,challenge_type from {table} order by id desc limit 20")
        rows = cur.fetchall()
        print('\n', table)
        pprint(rows)
    except Exception as exc:
        print('\n', table, '->', exc)

conn.close()
