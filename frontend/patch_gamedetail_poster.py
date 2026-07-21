# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(__file__).resolve().parent / 'src' / 'components' / 'GameDetail.vue'
text = p.read_text(encoding='utf-8')

old_img = '''              <img v-if="posterUrl" :src="posterUrl" :alt="game.title" class="action-poster-img" />'''
new_img = '''              <img v-if="posterUrl && !posterBroken" :src="posterUrl" :alt="game.title" class="action-poster-img" @error="posterBroken = true" />'''
if old_img not in text:
    raise SystemExit('img not found')
text = text.replace(old_img, new_img, 1)

old_poster = '''    const posterUrl = computed(() => {
      const path = getGamePosterPath(game.value)
      return path ? resolveUploadUrl(path) : ''
    })'''
# find actual block
import re
m = re.search(r"const posterUrl = computed\(\(\) => \{[^}]+\}\)", text)
if not m:
    # multiline
    m = re.search(r"const posterUrl = computed\(\(\) => \{\n(?:.*\n){1,4}\s*\}\)", text)
if not m:
    raise SystemExit('posterUrl not found')
print('found posterUrl at', m.start())

# More reliable: read around line from grep earlier
old = '''    const posterUrl = computed(() => {
      const path = getGamePosterPath(game.value)
      return path ? resolveUploadUrl(path) : ''
    })'''
if old not in text:
    # try without exact spaces
    raise SystemExit('exact posterUrl block missing:\n' + text[text.find('posterUrl'):text.find('posterUrl')+200])
text = text.replace(old, '''    const posterBroken = ref(false)
    const posterUrl = computed(() => {
      const path = getGamePosterPath(game.value)
      return path ? resolveUploadUrl(path, game.value?.id) : ''
    })
    watch(() => game.value?.id, () => { posterBroken.value = false })''', 1)

# ensure watch imported
if 'watch' not in text.split('from \'vue\'')[0][-80:]:
    text = text.replace(
        "import { ref, computed, inject, onMounted, onUnmounted, watch } from 'vue'",
        "import { ref, computed, inject, onMounted, onUnmounted, watch } from 'vue'",
        1,
    )

# return posterBroken
if 'posterBroken,' not in text:
    text = text.replace('posterUrl,', 'posterUrl, posterBroken,', 1)

p.write_text(text, encoding='utf-8', newline='\n')
print('GameDetail poster ok')
