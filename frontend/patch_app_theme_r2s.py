# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(__file__).resolve().parent / 'src' / 'App.vue'
text = p.read_text(encoding='utf-8')

old = """    const themeOverrides = computed(() => ({
      common: isDark.value ? {
        primaryColor: '#5ED9A8',
        primaryColorHover: '#7EE8C0',
        bodyColor: 'transparent',
        textColor1: '#E2E8F0',
        textColor2: '#7A8494',
        textColor3: '#7A8494',
        cardColor: '#12141D',
        borderColor: 'rgba(45, 181, 138, 0.18)',
        borderRadius: '10px',
        fontSize: '16px',
        fontSizeMini: '12px',
        fontSizeTiny: '12px',
        fontSizeSmall: '14px',
        fontSizeMedium: '16px',
        fontSizeLarge: '18px',
        fontSizeHuge: '20px',
        fontFamily: "'M PLUS Rounded 1c', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei UI', sans-serif",
        fontFamilyMono: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
      } : {
        primaryColor: '#1A9B6E',
        primaryColorHover: '#15803D',
        bodyColor: 'transparent',
        textColor1: '#0F172A',
        textColor2: '#64748B',
        textColor3: '#64748B',
        cardColor: '#FFFFFF',
        borderColor: 'rgba(26, 155, 110, 0.16)',
        borderRadius: '10px',
        fontSize: '16px',
        fontSizeMini: '12px',
        fontSizeTiny: '12px',
        fontSizeSmall: '14px',
        fontSizeMedium: '16px',
        fontSizeLarge: '18px',
        fontSizeHuge: '20px',
        fontFamily: "'M PLUS Rounded 1c', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei UI', sans-serif",
        fontFamilyMono: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
      },
    }))"""

font = "'Reverier Mono', Menlo, 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', Consolas, monospace"

new = f"""    const themeOverrides = computed(() => ({{
      common: isDark.value ? {{
        primaryColor: '#3aa6f0',
        primaryColorHover: '#0891ed',
        bodyColor: 'transparent',
        textColor1: '#e8ecf2',
        textColor2: 'rgba(232, 236, 242, 0.6)',
        textColor3: 'rgba(232, 236, 242, 0.6)',
        cardColor: 'rgba(30, 34, 44, 0.72)',
        borderColor: 'rgba(255, 255, 255, 0.08)',
        borderRadius: '12px',
        fontSize: '16px',
        fontSizeMini: '12px',
        fontSizeTiny: '12px',
        fontSizeSmall: '14px',
        fontSizeMedium: '16px',
        fontSizeLarge: '18px',
        fontSizeHuge: '20px',
        fontFamily: "{font}",
        fontFamilyMono: "{font}",
      }} : {{
        primaryColor: '#0891ed',
        primaryColorHover: '#0678c7',
        bodyColor: 'transparent',
        textColor1: '#000000',
        textColor2: 'rgba(0, 0, 0, 0.6)',
        textColor3: 'rgba(0, 0, 0, 0.6)',
        cardColor: 'rgba(255, 255, 255, 0.6)',
        borderColor: 'rgba(0, 0, 0, 0.08)',
        borderRadius: '12px',
        fontSize: '16px',
        fontSizeMini: '12px',
        fontSizeTiny: '12px',
        fontSizeSmall: '14px',
        fontSizeMedium: '16px',
        fontSizeLarge: '18px',
        fontSizeHuge: '20px',
        fontFamily: "{font}",
        fontFamilyMono: "{font}",
      }},
    }}))"""

if old not in text:
    raise SystemExit('themeOverrides block not found')
p.write_text(text.replace(old, new, 1), encoding='utf-8', newline='\n')
print('App themeOverrides ok')
