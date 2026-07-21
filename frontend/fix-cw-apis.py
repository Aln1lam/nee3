# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(r'E:\neepu\frontend\src\components\ChallengeWorkspace.vue')
text = p.read_text(encoding='utf-8')

replacements = [
    ('const res = await axios.get(/api/challenges/games//challenges)',
     'const res = await axios.get(`/api/challenges/games/${props.gameId}/challenges`)'),
    ('const res = await axios.get(/api/challenges//stats, bgConfig(signal))',
     'const res = await axios.get(`/api/challenges/${ch.id}/stats`, bgConfig(signal))'),
    ('const detail = await axios.get(/api/challenges/, bgConfig(signal))',
     'const detail = await axios.get(`/api/challenges/${ch.id}`, bgConfig(signal))'),
    ('/api/challenges/games//first-solves,',
     '`/api/challenges/games/${props.gameId}/first-solves`,'),
    ('const detailPromise = axios.get(/api/challenges/)',
     'const detailPromise = axios.get(`/api/challenges/${ch.id}`)'),
    ('? axios.get(/api/challenges//stats).catch(() => null)',
     '? axios.get(`/api/challenges/${ch.id}/stats`).catch(() => null)'),
    ('const res = await axios.get(/api/challenges//hints)',
     'const res = await axios.get(`/api/challenges/${selectedChallenge.value.id}/hints`)'),
    ('const res = await axios.post(/api/challenges//access-hint)',
     'const res = await axios.post(`/api/challenges/${h.id}/access-hint`)'),
    ('const res = await axios.get(/api/challenges//container-status)',
     'const res = await axios.get(`/api/challenges/${selectedChallenge.value.id}/container-status`)'),
    ('res = await axios.post(/api/challenges//start-container)',
     'res = await axios.post(`/api/challenges/${selectedChallenge.value.id}/start-container`)'),
    ('res = await axios.post(/api/container/start/)',
     'res = await axios.post(`/api/container/start/${selectedChallenge.value.id}`)'),
    ('/api/challenges//submit,',
     '`/api/challenges/${selectedChallenge.value.id}/submit`,'),
    ('?  获得！',
     '? `${bloodNames[bloodLevel]} 获得！`'),
    ('message.warning(已扣除  分)',
     'message.warning(`已扣除 ${res.data?.data?.penalty} 分`)'),
]

for old, new in replacements:
    if old not in text:
        print('MISSING:', old[:60])
    text = text.replace(old, new)

p.write_text(text, encoding='utf-8', newline='\n')
print('ChallengeWorkspace API URLs fixed')
