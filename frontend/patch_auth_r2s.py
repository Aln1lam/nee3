# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(__file__).resolve().parent / 'src' / 'components' / 'Auth.vue'
text = p.read_text(encoding='utf-8')

# Ensure login inputs use input-md height via class if possible
if 'auth-r2s' not in text:
    text = text.replace('<div class="auth-page', '<div class="auth-page auth-r2s', 1)
    if '<div class="auth-page auth-r2s' not in text:
        # try other root
        text = text.replace('class="auth-wrap"', 'class="auth-wrap auth-r2s"', 1)

# append style block addition before last </style> or end
extra = '''
<style>
.auth-r2s .n-input {
  --n-height: 48px !important;
  --n-border-radius: 8px !important;
  font-family: 'Reverier Mono', Menlo, monospace !important;
}
.auth-r2s .n-button {
  --n-height: 48px !important;
  --n-border-radius: 8px !important;
  font-weight: 700 !important;
}
.auth-r2s .n-form-item-label {
  font-family: 'Reverier Mono', Menlo, monospace !important;
}
.auth-icon-slot {
  width: 48px;
  height: 48px;
}
</style>
'''
if 'auth-r2s .n-input' not in text:
    text = text.rstrip() + '\n' + extra

p.write_text(text, encoding='utf-8', newline='\n')
print('Auth r2s ok')
