<template>
  <div class="competitions-container page-wrap competition-page">
    <!-- 竞赛列表 -->
    <div v-if="!selectedGame" class="competitions-list">
      <n-card>
        <template #header>
          <div class="header-title">
            <span>CTF 竞赛</span>
            <n-button 
              v-if="isAdmin" 
              type="primary" 
              @click="showCreateDialog = true"
              size="small"
            >
              创建竞赛
            </n-button>
          </div>
        </template>

        <n-spin :show="loading">
          <div class="games-grid">
            <n-card
              v-for="game in games"
              :key="game.id"
              class="game-card"
              :bordered="false"
            >
              <template #header>
                <div class="game-header">
                  <h3 class="clickable-title" @click.stop="openCompetition(game)">{{ game.title }}</h3>
                  <n-tag 
                    :type="isGameActive(game) ? 'success' : 'default'"
                    round
                  >
                    {{ isGameActive(game) ? '进行中' : '未开始' }}
                  </n-tag>
                </div>
              </template>

              <div class="game-info">
                <p><strong>开始时间：</strong> {{ formatTime(game.start_time) }}</p>
                <p><strong>结束时间：</strong> {{ formatTime(game.end_time) }}</p>
                <p><strong>题目数：</strong> {{ game.challenge_count }}</p>
                <p><strong>参赛队伍：</strong> {{ game.participation_count }}</p>
              </div>

              <template #footer>
                <div class="game-actions">
                  <n-button 
                    v-if="!isUserJoined(game.id)"
                    type="primary"
                    @click.stop="joinGame(game.id)"
                    :loading="joiningGame === game.id"
                  >
                    加入竞赛
                  </n-button>
                  <n-button 
                    v-else
                    type="info"
                    @click.stop="openCompetition(game)"
                    :disabled="!isGameActive(game)"
                  >
                    {{ isGameActive(game) ? '进入竞赛' : '未开始' }}
                  </n-button>
                </div>
              </template>
            </n-card>
          </div>

          <n-empty 
            v-if="games.length === 0"
            description="暂无竞赛"
            style="margin-top: 20px"
          />
        </n-spin>
      </n-card>
    </div>

    <!-- 竞赛详情 -->
    <div v-else class="game-detail">
      <n-card>
        <template #header>
            <div class="detail-header">
            <n-button text @click="backToList">
              <template #icon>
                <n-icon><arrow-left /></n-icon>
              </template>
              返回
            </n-button>
            <h3 class="detail-title">{{ selectedGame.title }}</h3>
          </div>
        </template>

        <n-tabs type="line" animated>
          <!-- 题目 Tab -->
          <n-tab-pane name="challenges" tab="题目">
            <div class="challenges-section">
              <div class="challenges-grid">
                <div
                  v-for="challenge in challenges"
                  :key="challenge.id"
                  class="challenge-item"
                  :class="{ solved: isChallengesSolved(challenge.id) }"
                  @click="handleChallengeClick(challenge)"
                >
                  <div class="challenge-category">{{ challenge.category }}</div>
                  <div class="challenge-title">{{ challenge.title }}</div>
                  <div class="challenge-points">{{ challenge.points }} pts</div>
                  <div v-if="isChallengesSolved(challenge.id)" class="solved-badge">✓</div>
                  <div v-if="isChallengesSolved(challenge.id)" class="solved-text">已攻破</div>
                </div>
              </div>
            </div>
          </n-tab-pane>

          <!-- 排行榜 Tab -->
          <n-tab-pane name="scoreboard" tab="排行榜">
            <div class="scoreboard-section">
              <n-data-table
                :columns="scoreboardColumns"
                :data="scoreboard"
                :pagination="{ pageSize: 20 }"
                :bordered="false"
                :single-line="false"
              />
            </div>
          </n-tab-pane>

          <!-- 个人统计 Tab -->
          <n-tab-pane name="stats" tab="个人统计">
            <div class="stats-section">
              <n-grid :cols="4" responsive="screen" :x-gap="12" :y-gap="12">
                <n-grid-item>
                  <n-card>
                    <n-statistic 
                      label="总分数"
                      :value="userStats?.total_points || 0"
                    />
                  </n-card>
                </n-grid-item>
                <n-grid-item>
                  <n-card>
                    <n-statistic 
                      label="已解决"
                      :value="userStats?.solved_challenges || 0"
                    />
                  </n-card>
                </n-grid-item>
                <n-grid-item>
                  <n-card>
                    <n-statistic 
                      label="排名"
                      :value="userStats?.rank || '-'"
                    />
                  </n-card>
                </n-grid-item>
                <n-grid-item>
                  <n-card>
                    <n-statistic 
                      label="准确率"
                      :value="`${calculateAccuracy()}%`"
                    />
                  </n-card>
                </n-grid-item>
              </n-grid>
            </div>
          </n-tab-pane>
        </n-tabs>
      </n-card>

      <!-- 题目详情Modal -->
      <n-modal
        v-model:show="showChallengeDetail"
        title="题目详情"
        preset="dialog"
        size="large"
      >
        <div v-if="selectedChallenge" class="challenge-detail">
          <div class="detail-content">
            <h3>{{ selectedChallenge.title }}</h3>
            <p><strong>分类：</strong> {{ selectedChallenge.category }}</p>
            <p><strong>分值：</strong> {{ selectedChallenge.points }}</p>
            <p><strong>解决人数：</strong> {{ challengeStats?.unique_solvers || 0 }}</p>
            <p><strong>通过率：</strong> {{ challengeStats?.solve_rate || '0%' }}</p>
            
            <!-- 容器启动/查看按钮 -->
            <div v-if="selectedChallenge.challenge_type && [1, 3].includes(selectedChallenge.challenge_type)" class="container-start-btn">
              <n-button 
                v-if="!containerInfo"
                type="success"
                @click="startContainer"
                :loading="startingContainer"
              >
                🚀 启动容器
              </n-button>
              <n-button 
                v-else
                type="info"
                @click="() => showContainerInfo = true"
              >
                👁️ 查看容器
              </n-button>
            </div>
            
            <div class="description">
              <strong>描述：</strong>
              <div class="desc-text" v-html="safeChallengeDescription"></div>
            </div>

            <div v-if="selectedChallenge.attachment_id" class="attachment">
              <strong>附件：</strong>
              <a :href="`/api/resources/${selectedChallenge.attachment_id}/content`" target="_blank">下载/查看附件</a>
            </div>

            <div v-if="selectedChallenge.hint" class="hint">
              <strong>提示：</strong>
              <p>{{ selectedChallenge.hint }}</p>
            </div>

            <div class="submission-area">
              <n-input-group>
                <n-input
                  v-model:value="flagInput"
                  type="text"
                  placeholder="输入 flag..."
                  :disabled="isChallengesSolved(selectedChallenge.id)"
                />
                <n-button
                  type="primary"
                  @click="submitFlag"
                  :loading="submitting"
                  :disabled="isChallengesSolved(selectedChallenge.id)"
                >
                  提交
                </n-button>
              </n-input-group>
            </div>

            <div v-if="submissionHistory.length > 0" class="history">
              <strong>提交历史：</strong>
              <n-list bordered>
                <n-list-item v-for="(sub, idx) in submissionHistory" :key="idx">
                  <div class="submission-item">
                    <span 
                      :class="{ 
                        correct: sub.is_correct,
                        wrong: !sub.is_correct 
                      }"
                    >
                      {{ sub.is_correct ? '✓ 正确' : '✗ 错误' }}
                    </span>
                    <span class="time">{{ formatTime(sub.submitted_at) }}</span>
                  </div>
                </n-list-item>
              </n-list>
            </div>
          </div>
        </div>
      </n-modal>

      <!-- 容器信息 Dialog -->
      <n-modal
        v-model:show="showContainerInfo"
        title="容器已启动"
        preset="dialog"
        positive-text="在新标签页打开"
        negative-text="关闭"
        @positive="() => { if(containerInfo?.connection_url) window.open(containerInfo.connection_url, '_blank') }"
      >
        <div v-if="containerInfo" class="container-info">
          <div class="info-item">
            <span class="label">容器地址：</span>
            <div class="value-container">
              <input 
                type="text" 
                :value="containerInfo.connection_url || 'N/A'" 
                class="value-input"
                readonly
              />
              <n-button 
                text 
                type="primary"
                @click="() => navigator.clipboard.writeText(containerInfo.connection_url || '')"
              >
                复制
              </n-button>
            </div>
          </div>
          
          <div v-if="containerInfo.port" class="info-item">
            <span class="label">端口：</span>
            <span class="value">{{ containerInfo.port }}</span>
          </div>
          
          <div v-if="containerInfo.instance_id" class="info-item">
            <span class="label">实例 ID：</span>
            <span class="value">{{ containerInfo.instance_id }}</span>
          </div>
          
          <div v-if="containerInfo.expires_at" class="info-item">
            <span class="label">过期时间：</span>
            <span class="value">{{ new Date(containerInfo.expires_at).toLocaleString('zh-CN') }}</span>
          </div>
          
          <div class="info-tips">
            <p>💡 提示：容器将在上述时间自动停止运行</p>
          </div>
          
          <div class="action-buttons">
            <n-button 
              type="error"
              @click="destroyContainer"
              :loading="destroyingContainer"
            >
              🗑️ 销毁容器
            </n-button>
          </div>
        </div>
      </n-modal>

      <!-- 创建竞赛 Dialog -->
      <n-modal
        v-model:show="showCreateDialog"
        title="创建竞赛"
        preset="dialog"
        positive-text="创建"
        negative-text="取消"
        @positive="createGame"
      >
        <n-form ref="formRef" :model="newGame" label-placement="left">
          <n-form-item label="竞赛名称" path="title">
            <n-input v-model:value="newGame.title" placeholder="输入竞赛名称" />
          </n-form-item>
          <n-form-item label="开始时间" path="start_time">
            <n-date-picker
              v-model:value="newGame.start_time"
              type="datetime"
              clearable
            />
          </n-form-item>
          <n-form-item label="结束时间" path="end_time">
            <n-date-picker
              v-model:value="newGame.end_time"
              type="datetime"
              clearable
            />
          </n-form-item>
          <n-form-item label="描述" path="description">
            <n-input 
              v-model:value="newGame.description"
              type="textarea"
              placeholder="输入竞赛描述"
            />
          </n-form-item>
        </n-form>
      </n-modal>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, inject, onMounted, watch, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NCard, NButton, NTabs, NTabPane, NInput, NInputGroup,
  NDataTable, NEmpty, NIcon, NGrid, NGridItem, NStatistic,
  NModal, NForm, NFormItem, NDatePicker, NList, NListItem,
  NSpin, NTag, useMessage, useDialog
} from 'naive-ui'
import { ArrowLeft } from '@vicons/tabler'
import { parseMarkdownSafe } from '../utils/markdown'
import {
  getContainerStatus,
  startContainer as apiStartContainer,
  stopContainer as apiStopContainer,
  pickRunningInstance,
} from '@/services/container'

export default {
  components: {
    NCard, NButton, NTabs, NTabPane, NInput, NInputGroup,
    NDataTable, NEmpty, NIcon, NGrid, NGridItem, NStatistic,
    NModal, NForm, NFormItem, NDatePicker, NList, NListItem,
    NSpin, NTag, ArrowLeft
  },
  setup() {
    const axios = inject('axios')
    const message = useMessage()
    const dialog = useDialog()
    const route = useRoute()
    const router = useRouter()
    
    const games = ref([])
    const challenges = ref([])
    const scoreboard = ref([])
    const selectedGame = ref(null)
    const selectedChallenge = ref(null)
    const showChallengeDetail = ref(false)
    const showCreateDialog = ref(false)
    const loading = ref(false)
    const submitting = ref(false)
    const joiningGame = ref(null)
    
    const flagInput = ref('')
    const userJoined = ref(new Set())
    const userStats = ref(null)
    const challengeStats = ref(null)
    const submissionHistory = ref([])
    const startingContainer = ref(false)
    const showContainerInfo = ref(false)
    const containerInfo = ref(null)
    const destroyingContainer = ref(false)
    const inviteCodeInput = ref('')
    
    const isAdmin = computed(() => {
      // 从localStorage或其他地方获取用户信息
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      return user.is_admin || false
    })

    const scoreboardColumns = [
      {
        title: '排名',
        key: 'rank',
        width: 80,
        align: 'center'
      },
      {
        title: '队伍',
        key: 'team_name',
        ellipsis: true
      },
      {
        title: '总分',
        key: 'total_points',
        width: 100,
        align: 'right'
      },
      {
        title: '已解决',
        key: 'solved_challenges',
        width: 100,
        align: 'center'
      },
      {
        title: '最后提交',
        key: 'last_submission_time',
        width: 180,
        render: (row) => formatTime(row.last_submission_time)
      }
    ]

    const newGame = reactive({
      title: '',
      start_time: null,
      end_time: null,
      description: ''
    })

    const formatTime = (timestamp) => {
      if (!timestamp) return '-'
      return new Date(timestamp).toLocaleString('zh-CN')
    }

    const isGameActive = (game) => {
      const now = new Date()
      return new Date(game.start_time) <= now && now <= new Date(game.end_time)
    }

    const isUserJoined = (gameId) => {
      return userJoined.value.has(gameId)
    }

    const isChallengesSolved = (challengeId) => {
      return submissionHistory.value.some(
        s => s.challenge_id === challengeId && s.is_correct
      )
    }

    const safeChallengeDescription = computed(() => {
      if (!selectedChallenge.value?.description) return ''
      return parseMarkdownSafe(selectedChallenge.value.description)
    })

    const calculateAccuracy = () => {
      if (submissionHistory.value.length === 0) return '0'
      const correct = submissionHistory.value.filter(s => s.is_correct).length
      return ((correct / submissionHistory.value.length) * 100).toFixed(0)
    }

    const fetchGames = async () => {
      try {
        loading.value = true
        const response = await axios.get('/api/competitions/')
        games.value = response.data.data || []
        await fetchJoinedGames()
      } catch (error) {
        message.error('获取竞赛列表失败')
      } finally {
        loading.value = false
      }
    }

    const fetchJoinedGames = async () => {
      try {
        if (!games.value || games.value.length === 0) return
        const results = await Promise.all(
          games.value.map(g => axios.get(`/api/competitions/${g.id}/joined`).then(r => ({ id: g.id, joined: !!r.data?.joined })).catch(() => ({ id: g.id, joined: false })))
        )
        const next = new Set()
        for (const r of results) {
          if (r.joined) next.add(r.id)
        }
        userJoined.value = next
      } catch (e) {
        // ignore
      }
    }

    const selectGame = async (game) => {
      selectedGame.value = game
      await fetchChallenges(game.id)
      await fetchScoreboard(game.id)
      await fetchUserStats(game.id)
    }

    const openCompetition = (game) => {
      if (!game || !game.id) return
      router.push({ name: 'CompetitionDetail', params: { id: game.id } })
    }

    const backToList = () => {
      selectedGame.value = null
      selectedChallenge.value = null
      showChallengeDetail.value = false
      router.push({ name: 'CTFCompetitions' })
    }

    const fetchChallenges = async (gameId) => {
      try {
        const response = await axios.get(`/api/challenges/games/${gameId}/challenges`)
        challenges.value = response.data.data || []
      } catch (error) {
        message.error('获取题目列表失败')
      }
    }

    const fetchScoreboard = async (gameId) => {
      try {
        // 主路径：/api/ctf/games/:id/scoreboard（与 Scoreboard.vue 一致）
        const response = await axios.get(`/api/ctf/games/${gameId}/scoreboard`)
        scoreboard.value = response.data.data || []
      } catch (error) {
        message.error('获取排行榜失败')
      }
    }

    const fetchUserStats = async (gameId) => {
      try {
        // 个人/队伍榜视角仅存在于 /api/ctf/.../scoreboard/user
        const response = await axios.get(`/api/ctf/games/${gameId}/scoreboard/user`)
        userStats.value = response.data.data
      } catch (error) {
        console.error('获取用户统计失败', error)
      }
    }

    const selectChallenge = async (challenge) => {
      // 重置容器状态和输入框
      containerInfo.value = null
      flagInput.value = ''
      
      // open modal first to keep UX responsive
      showChallengeDetail.value = true
      try {
        const response = await axios.get(`/api/challenges/${challenge.id}`)
        const data = response.data.data
        // use backend-provided full challenge data (includes attachment_id, flag, description, etc.)
        selectedChallenge.value = data
        submissionHistory.value = data.submissions || []

        // 检查用户是否已有该题目的容器实例
        if (data.challenge_type && [1, 3].includes(data.challenge_type)) {
          try {
            const statusPayload = await getContainerStatus(challenge.id)
            containerInfo.value = pickRunningInstance(statusPayload)
          } catch (e) {
            console.error('获取容器实例失败', e)
            containerInfo.value = null
          }
        }

        const statsResponse = await axios.get(`/api/challenges/${challenge.id}/stats`)
        challengeStats.value = statsResponse.data.data
      } catch (error) {
        message.error('获取题目信息失败')
        // fallback: still show minimal data
        selectedChallenge.value = challenge
      }
    }

    const handleChallengeClick = (challenge) => {
      if (!challenge || !challenge.id) return
      router.push({ name: 'ChallengeDetail', params: { id: challenge.id } })
    }

    const openCompetitionById = async (gameId) => {
      if (!gameId) return
      let game = games.value.find(g => String(g.id) === String(gameId))
      if (!game) {
        await fetchGames()
        game = games.value.find(g => String(g.id) === String(gameId))
      }
      if (!game) {
        message.error('竞赛不存在')
        return
      }
      await selectGame(game)
    }

    const openChallengeById = async (challengeId) => {
      if (!challengeId) return
      try {
        const challengeRes = await axios.get(`/api/challenges/${challengeId}`)
        const detail = challengeRes.data?.data
        if (!detail) {
          message.error('题目不存在')
          return
        }

        if (detail.game_id) {
          await openCompetitionById(detail.game_id)
        }

        selectedChallenge.value = detail
        submissionHistory.value = detail.submissions || []
        showChallengeDetail.value = true

        try {
          const statsResponse = await axios.get(`/api/challenges/${challengeId}/stats`)
          challengeStats.value = statsResponse.data?.data || null
        } catch (e) {
          challengeStats.value = null
        }
      } catch (error) {
        message.error('获取题目信息失败')
      }
    }

    const syncRouteState = async () => {
      const routeName = route.name
      const id = route.params.id
      if (routeName === 'CompetitionDetail') {
        await openCompetitionById(id)
        return
      }
      if (routeName === 'ChallengeDetail') {
        await openChallengeById(id)
        return
      }
      if (routeName === 'CTFCompetitions') {
        selectedGame.value = null
        selectedChallenge.value = null
        showChallengeDetail.value = false
      }
    }

    const submitFlag = async () => {
      if (!flagInput.value || submitting.value) {
        if (!flagInput.value) message.warning('请输入flag')
        return
      }

      try {
        submitting.value = true
        
        // 统一走主提交路径（容器题亦由后端按题型处理）
        let endpoint = `/api/challenges/${selectedChallenge.value.id}/submit`
        
        const requestBody = {
              answer: flagInput.value,
              flag: flagInput.value,
            }
        
        const response = await axios.post(endpoint, requestBody, {
          headers: { 'Content-Type': 'application/json' }
        })

        const payload = response.data?.data || response.data || {}
        const correct = !!(payload.is_correct || payload.correct || response.data?.correct)
        const ok = response.data?.code === 200 || response.data?.success || payload.is_correct != null

        if (ok && correct) {
          if (payload.container_closed || response.data?.container_closed) {
            message.success('✓ 答案正确！容器已自动关闭')
            containerInfo.value = null
            showContainerInfo.value = false
          } else {
            message.success('✓ 答案正确！' + (response.data?.msg || response.data?.message || ''))
          }
          
          flagInput.value = ''
          submissionHistory.value.push(payload.submission || {})
          await fetchUserStats(selectedGame.value.id)
          await fetchScoreboard(selectedGame.value.id)
        } else if (ok && !correct) {
          message.error('✗ 答案错误')
        } else {
          message.error(response.data?.msg || response.data?.message || '提交失败')
        }
      } catch (error) {
        message.error(error.response?.data?.message || error.response?.data?.msg || '提交失败')
      } finally {
        submitting.value = false
      }
    }

    const startContainer = async () => {
      if (startingContainer.value) return
      try {
        startingContainer.value = true
        const payload = await apiStartContainer(selectedChallenge.value.id, { asyncMode: false })
        const running = pickRunningInstance(payload)
        if (running || payload?.code === 200 || payload?.success) {
          if (running) {
            containerInfo.value = running
          } else {
            const statusPayload = await getContainerStatus(selectedChallenge.value.id)
            containerInfo.value = pickRunningInstance(statusPayload)
          }
          showContainerInfo.value = true
          message.success('✓ 容器启动成功！所有流量将被自动捕获')
        } else {
          message.error(payload?.msg || payload?.message || '启动失败')
        }
      } catch (error) {
        message.error(error.response?.data?.msg || error.response?.data?.message || '启动容器失败')
      } finally {
        startingContainer.value = false
      }
    }

    const destroyContainer = async () => {
      if (destroyingContainer.value) return
      try {
        if (!containerInfo.value?.instance_id) {
          message.error('实例ID不存在')
          return
        }
        
        destroyingContainer.value = true
        const payload = await apiStopContainer(containerInfo.value.instance_id)
        
        if (payload?.code === 200 || payload?.success !== false) {
          message.success('容器已销毁，可以重新启动')
          showContainerInfo.value = false
          containerInfo.value = null
          // 关闭题目详情对话框，用户可以重新打开题目
          showChallengeDetail.value = false
        } else {
          message.error(payload?.msg || payload?.message || '销毁失败')
        }
      } catch (error) {
        message.error(error.response?.data?.msg || error.response?.data?.message || '销毁容器失败')
      } finally {
        destroyingContainer.value = false
      }
    }

    const joinGame = async (gameId) => {
      try {
        joiningGame.value = gameId
        
        // 1. 先获取比赛信息，判断是否需要邀请码
        const game = games.value.find(g => g.id === gameId)
        
        let inviteCode = ''
        
        // 2. 如果不是公开比赛，需要输入邀请码
        if (game && !game.is_public) {
            inviteCodeInput.value = ''
          const result = await new Promise((resolve) => {
            const dialogInstance = dialog.create({
              title: '请输入邀请码',
              content: () => {
                return h('div', { style: 'padding: 10px 0;' }, [
                  h('p', { style: 'margin-bottom: 10px; color: #666;' }, 
                    '该比赛需要邀请码才能参加，请输入您的邀请码：'
                  ),
                  h(NInput, {
                      value: inviteCodeInput.value,
                      'onUpdate:value': (val) => { inviteCodeInput.value = val },
                    placeholder: '请输入邀请码',
                    type: 'text',
                    maxlength: 128,
                    showCount: true,
                      clearable: true
                  })
                ])
              },
              positiveText: '确定',
              negativeText: '取消',
              onPositiveClick: () => {
                  const code = inviteCodeInput.value || ''
                if (!code.trim()) {
                  message.warning('请输入邀请码')
                  return false
                }
                resolve({ ok: true, code: code.trim() })
              },
              onNegativeClick: () => {
                resolve({ ok: false })
              },
              onClose: () => {
                resolve({ ok: false })
              }
            })
          })
          
          if (!result.ok) {
            joiningGame.value = null
            return
          }
          
          inviteCode = result.code
        }
        
        // 3. 发起加入请求
        const response = await axios.post(`/api/competitions/${gameId}/join`, {
          invite_code: inviteCode
        }, {
          headers: { 'Content-Type': 'application/json' }
        })
        
        const divisionName = response.data.division_name
        if (divisionName) {
          message.success(`成功加入竞赛！您已加入 ${divisionName} 赛道`)
        } else {
          message.success('加入竞赛成功')
        }
        
        userJoined.value.add(gameId)
        await fetchGames()
      } catch (error) {
        message.error(error.response?.data?.msg || '加入失败')
      } finally {
        joiningGame.value = null
      }
    }

    const createGame = async () => {
      try {
        await axios.post('/api/competitions/admin/create', {
          title: newGame.title,
          start_time: new Date(newGame.start_time).toISOString(),
          end_time: new Date(newGame.end_time).toISOString(),
          description: newGame.description,
          is_public: true
        }, {
          headers: { 'Content-Type': 'application/json' }
        })
        message.success('竞赛创建成功')
        showCreateDialog.value = false
        Object.assign(newGame, {
          title: '',
          start_time: null,
          end_time: null,
          description: ''
        })
        await fetchGames()
      } catch (error) {
        message.error('创建失败')
      }
    }

    onMounted(async () => {
      await fetchGames()
      await syncRouteState()
    })

    watch(() => route.fullPath, () => {
      syncRouteState()
    })

    return {
      games,
      challenges,
      scoreboard,
      selectedGame,
      selectedChallenge,
      safeChallengeDescription,
      showChallengeDetail,
      showCreateDialog,
      showContainerInfo,
      containerInfo,
      loading,
      submitting,
      startingContainer,
      destroyingContainer,
      joiningGame,
      flagInput,
      userStats,
      challengeStats,
      submissionHistory,
      isAdmin,
      scoreboardColumns,
      newGame,
      formatTime,
      isGameActive,
      isUserJoined,
      isChallengesSolved,
      calculateAccuracy,
      selectGame,
      openCompetition,
      backToList,
      selectChallenge,
      handleChallengeClick,
      submitFlag,
      startContainer,
      destroyContainer,
      joinGame,
      createGame
    }
  }
}
</script>

<style scoped>
.header-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.games-grid {
  display: grid;
  margin-top: var(--fib-21);
}

.game-card {
  cursor: pointer;
  transition: all 0.3s ease;
}

.game-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.game-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.game-header h3 {
  margin: 0;
  font-size: 18px;
}

.clickable-title {
  cursor: pointer;
}

.game-info {
  font-size: var(--text-sm);
  line-height: 1.8;
  color: var(--muted);
}

.game-info p {
  margin: 8px 0;
}

.game-actions {
  display: flex;
  gap: 10px;
  justify-content: space-between;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 15px;
}

.challenges-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(calc(var(--card-grid-min-golden) / var(--phi)), 1fr));
  gap: var(--space-gutter);
  margin-top: var(--fib-21);
}

.challenge-item {
  padding: var(--fib-21);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.challenge-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(102, 126, 234, 0.4);
}

.challenge-item.solved {
  background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
  cursor: default;
  transform: none;
  box-shadow: none;
}

.challenge-category {
  font-size: 12px;
  opacity: 0.9;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.challenge-title {
  font-size: 16px;
  font-weight: bold;
  margin: 10px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.challenge-points {
  font-size: 14px;
  margin-top: 10px;
}

.solved-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 24px;
  height: 24px;
  background: var(--gradient-card-bg, var(--card-bg));
  color: #84fab0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 16px;
}

.solved-text {
  position: absolute;
  bottom: 10px;
  right: 10px;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.85);
  color: #2e7d32;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 600;
}


.detail-content h3 {
  margin-top: 0;
  font-size: 24px;
}

.container-start-btn {
  margin: 15px 0;
}


.info-item {
  margin: 15px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.label {
  font-weight: bold;
  min-width: 100px;
  color: var(--text);
}

.value {
  color: var(--muted);
  font-family: monospace;
}

.value-container {
  display: flex;
  gap: 8px;
  flex: 1;
}

.value-input {
  flex: 1;
  padding: var(--fib-8) var(--fib-13);
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  font-family: monospace;
  font-size: var(--text-sm);
  background: var(--code-bg, var(--hover));
  color: var(--text);
  cursor: text;
}

.value-input:focus {
  outline: none;
  border-color: var(--primary);
  background: var(--card-bg);
}

.info-tips {
  margin-top: 20px;
  padding: 12px;
  background: #e6f7ff;
  border-left: 4px solid #1890ff;
  border-radius: 4px;
}

.info-tips p {
  margin: 0;
  color: #0050b3;
  font-size: 14px;
}

.action-buttons {
  margin-top: 20px;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.description {
  margin: var(--fib-21) 0;
  padding: var(--fib-13);
  background: var(--hover);
  border-radius: var(--card-radius);
  border: 1px solid var(--border);
}

.desc-text {
  margin-top: 10px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.hint {
  margin: 20px 0;
  padding: 15px;
  background: #fff7e6;
  border-radius: 8px;
  border-left: 4px solid #ffc069;
}

.submission-area {
  margin: 20px 0;
}

.history {
  margin-top: 20px;
}

.submission-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.submission-item span {
  padding: 8px 12px;
  border-radius: 4px;
  font-weight: bold;
}

.submission-item .correct {
  background: #f0f9ff;
  color: #059669;
}

.submission-item .wrong {
  background: #fef2f2;
  color: #dc2626;
}

.submission-item .time {
  color: #999;
  font-size: 12px;
}


</style>
