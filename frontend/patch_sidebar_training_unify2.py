# -*- coding: utf-8 -*-
"""GamesHub / Bulletin / AdminPanel sidebar group-label + GamesHub footer."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'src' / 'components'


def patch_games_hub():
    p = ROOT / 'GamesHub.vue'
    text = p.read_text(encoding='utf-8')

    old = '''        <div v-if="isAdmin" class="sidebar-actions">
          <UiButton size="small" variant="primary" @click="openCreate">创建赛事</UiButton>
        </div>

        <n-spin :show="loading" class="sidebar-spin">
          <div class="game-list">
            <button
              v-for="g in featuredGames"
              :key="g.id"
              type="button"
              class="sidebar-item game-list-item"
              :class="{ active: selected?.id === g.id }"
              @click="selectGame(g)"
            >
              <span class="item-code">{{ getGameSidebarCode(g) }}</span>
              <span class="item-title">{{ g.title }}</span>
              <span class="item-count status-dot" :class="getGameStatusDotClass(g)" aria-hidden="true" />
            </button>
          </div>

          <div v-if="!featuredGames.length && !loading" class="empty-side">
            <p>暂无赛事</p>
            <p class="empty-hint">
              管理员可创建赛事，或先前往
              <router-link to="/training">训练场</router-link>
            </p>
          </div>
        </n-spin>

        <n-pagination
          v-if="totalPages > 1"
          v-model:page="keyPage"
          :page-count="totalPages"
          size="small"
          class="side-pagination"
        />

        <button
          v-if="otherGamesAll.length"
          class="other-toggle sidebar-rail-footer"
          type="button"
          @click="scrollToOthers"
        >
          <span>其他赛事</span>
          <span class="other-chevron">↓</span>
        </button>
      </aside>'''

    new = '''        <div v-if="isAdmin" class="sidebar-actions">
          <UiButton size="small" variant="primary" @click="openCreate">创建赛事</UiButton>
        </div>

        <div class="sidebar-rail-nav">
          <div class="sidebar-group">
            <div class="group-label">赛事</div>
            <n-spin :show="loading" class="sidebar-spin">
              <div class="game-list">
                <button
                  v-for="g in featuredGames"
                  :key="g.id"
                  type="button"
                  class="sidebar-item game-list-item"
                  :class="{ active: selected?.id === g.id }"
                  @click="selectGame(g)"
                >
                  <span class="item-code">{{ getGameSidebarCode(g) }}</span>
                  <span class="item-title">{{ g.title }}</span>
                  <span class="item-count status-dot" :class="getGameStatusDotClass(g)" aria-hidden="true" />
                </button>
              </div>

              <div v-if="!featuredGames.length && !loading" class="empty-side">
                <p>暂无赛事</p>
                <p class="empty-hint">
                  管理员可创建赛事，或先前往
                  <router-link to="/training">训练场</router-link>
                </p>
              </div>
            </n-spin>
          </div>
        </div>

        <n-pagination
          v-if="totalPages > 1"
          v-model:page="keyPage"
          :page-count="totalPages"
          size="small"
          class="side-pagination"
        />

        <div class="sidebar-links sidebar-rail-footer">
          <button
            v-if="otherGamesAll.length"
            type="button"
            class="sidebar-link"
            @click="scrollToOthers"
          >
            <span class="link-code">OTH</span>
            <span>其他赛事</span>
          </button>
          <router-link to="/training" class="sidebar-link">
            <span class="link-code">TRN</span>
            <span>训练靶场</span>
          </router-link>
          <router-link to="/home" class="sidebar-link">
            <span class="link-code">HOM</span>
            <span>返回首页</span>
          </router-link>
        </div>
      </aside>'''

    if old not in text:
        raise SystemExit('GamesHub block not found')
    p.write_text(text.replace(old, new, 1), encoding='utf-8', newline='\n')
    print('ok GamesHub.vue')


def patch_bulletin():
    p = ROOT / 'Bulletin.vue'
    text = p.read_text(encoding='utf-8')

    old = '''      <nav class="sidebar-nav sidebar-rail-nav">
        <div class="sidebar-item">
          <span class="item-code">ALL</span>
          <span class="item-title">全部公告</span>
          <span class="item-count">{{ bulletins.length }}</span>
        </div>
        <div class="sidebar-item">
          <span class="item-code">PG</span>
          <span class="item-title">当前页</span>
          <span class="item-count">{{ pagedBulletins.length }}</span>
        </div>
        <router-link
          v-if="isAdmin"
          to="/bulletin/create"
          class="sidebar-item"
        >
          <span class="item-code">NEW</span>
          <span class="item-title">发布公告</span>
          <span class="item-count">→</span>
        </router-link>
      </nav>'''

    new = '''      <nav class="sidebar-rail-nav">
        <div class="sidebar-group">
          <div class="group-label">概览</div>
          <div class="sidebar-item">
            <span class="item-code">ALL</span>
            <span class="item-title">全部公告</span>
            <span class="item-count">{{ bulletins.length }}</span>
          </div>
          <div class="sidebar-item">
            <span class="item-code">PG</span>
            <span class="item-title">当前页</span>
            <span class="item-count">{{ pagedBulletins.length }}</span>
          </div>
          <router-link
            v-if="isAdmin"
            to="/bulletin/create"
            class="sidebar-item"
          >
            <span class="item-code">NEW</span>
            <span class="item-title">发布公告</span>
            <span class="item-count">→</span>
          </router-link>
        </div>
      </nav>'''

    if old not in text:
        raise SystemExit('Bulletin block not found')
    p.write_text(text.replace(old, new, 1), encoding='utf-8', newline='\n')
    print('ok Bulletin.vue')


def patch_admin():
    p = ROOT / 'AdminPanel.vue'
    text = p.read_text(encoding='utf-8')

    old = '''      <nav class="sidebar-rail-nav admin-nav">
        <router-link
          v-for="item in menuItems"
          :key="item.key"
          :to="`/admin/${item.key}`"
          class="sidebar-item"
          :class="{ active: activeKey === item.key }"
        >
          <span class="item-code">{{ item.code }}</span>
          <span class="item-title">{{ item.label }}</span>
        </router-link>
      </nav>'''

    new = '''      <nav class="sidebar-rail-nav admin-nav">
        <div class="sidebar-group">
          <div class="group-label">模块</div>
          <router-link
            v-for="item in menuItems"
            :key="item.key"
            :to="`/admin/${item.key}`"
            class="sidebar-item"
            :class="{ active: activeKey === item.key }"
          >
            <span class="item-code">{{ item.code }}</span>
            <span class="item-title">{{ item.label }}</span>
          </router-link>
        </div>
      </nav>'''

    if old not in text:
        raise SystemExit('AdminPanel block not found')
    p.write_text(text.replace(old, new, 1), encoding='utf-8', newline='\n')
    print('ok AdminPanel.vue')


def patch_wiki_tagcode():
    p = ROOT / 'KnowledgeList.vue'
    text = p.read_text(encoding='utf-8')

    old = """      if (t.includes('awd')) return 'AWD'
      if (t.includes('ai') || t.includes('人工智能')) return 'AI'
      if (t.includes('blockchain') || t.includes('区块链')) return 'BC'"""

    new = """      if (t.includes('awd')) return 'AWD'
      if (t.includes('blockchain') || t.includes('区块链')) return 'BC'
      if (t.includes('ai') || t.includes('人工智能')) return 'AI'"""

    if old not in text:
        raise SystemExit('KnowledgeList tagCode block not found')
    p.write_text(text.replace(old, new, 1), encoding='utf-8', newline='\n')
    print('ok KnowledgeList tagCode')


if __name__ == '__main__':
    patch_games_hub()
    patch_bulletin()
    patch_admin()
    patch_wiki_tagcode()
