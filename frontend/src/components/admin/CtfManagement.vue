<template>
  <div class="ctf-management">
    <!-- 选项卡 -->
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab"
        type="button"
        :class="['tab-btn', { active: activeTab === tab }]"
        @click="activeTab = tab"
      >
        <span class="tab-code">{{ getTabCode(tab) }}</span>
        <span>{{ getTabLabel(tab) }}</span>
      </button>
    </div>

    <!-- 竞赛管理 -->
    <div v-show="activeTab === 'games'" class="tab-content">
      <div class="card">
        <div class="card-header">
          <h3>竞赛列表</h3>
          <button class="btn-primary" @click="showCreateGameModal = true">新建竞赛</button>
        </div>
        <div class="games-filters">
          <label class="filter-item">
            类型
            <select v-model="gameTypeFilter" class="form-input filter-select" @change="loadGames">
              <option value="">全部</option>
              <option value="official">正式赛</option>
              <option value="training">训练场</option>
              <option value="practice">练习</option>
            </select>
          </label>
          <label class="filter-item">
            <input v-model="showEphemeral" type="checkbox" @change="loadGames">
            显示探针/E2E
          </label>
          <span class="filter-meta">共 {{ games.length }} 场</span>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>竞赛名称</th>
              <th>类型</th>
              <th>开始时间</th>
              <th>结束时间</th>
              <th>参赛人数</th>
              <th>题目数</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="game in games" :key="game.id">
            <tr>
              <td>{{ game.id }}</td>
              <td>{{ game.title }}</td>
              <td>
                <span class="badge" :class="gameTypeBadgeClass(game)">{{ gameTypeLabel(game) }}</span>
              </td>
              <td>{{ formatTime(game.start_time) }}</td>
              <td>{{ formatTime(game.end_time) }}</td>
              <td>
                <span class="badge badge-blue">{{ game.participation_count || 0 }}</span>
              </td>
              <td>
                <span class="badge badge-green">{{ game.challenge_count || 0 }}</span>
              </td>
              <td>
                <span v-if="game.archived_at" class="badge badge-gray">已归档</span>
                <span v-else class="badge badge-success">进行中</span>
              </td>
              <td>
                <button class="btn-small btn-edit" @click="editGame(game)">编辑</button>
                <button v-if="!game.archived_at" class="btn-small btn-warning" @click="archiveGame(game)">归档</button>
                <button class="btn-small btn-danger" @click="deleteGame(game.id)">删除</button>
                <button class="btn-small btn-info" @click="toggleGameDivisions(game.id)">
                  {{ expandedGameId === game.id ? '隐藏分组' : '显示分组' }}
                </button>
              </td>
            </tr>
            <tr v-if="expandedGameId === game.id">
              <td colspan="9">
                <div class="game-divisions-section">
                  <div class="divisions-header">
                    <div class="divisions-title">分组 / 邀请码</div>
                    <button class="btn-small btn-primary" @click="openCreateDivisionModal(game.id)">新建分组</button>
                  </div>

                  <div v-if="loadingDivisions[game.id]" class="text-muted">加载中...</div>
                  <div v-else>
                    <div v-if="!gameDivisions[game.id] || gameDivisions[game.id].length === 0" class="empty-state">暂无分组</div>
                    <div v-for="division in (gameDivisions[game.id] || [])" :key="division.id" class="division-item">
                      <div class="division-meta">
                        <div class="division-name">{{ division.name }}</div>
                        <div class="division-sub">
                          邀请码：<span class="code-pill">{{ division.invite_code || '未设置' }}</span>
                        </div>
                        <div class="division-sub">学校范围：{{ division.school_scope || '全局' }}</div>
                        <div class="division-sub">成员数：{{ division.member_count || 0 }}</div>
                      </div>
                      <div class="division-actions">
                        <button class="btn-small btn-info" :disabled="!division.invite_code" @click="copyToClipboard(division.invite_code)">复制邀请码</button>
                        <button class="btn-small" @click="viewDivisionMembers(game.id, division)">查看成员</button>
                        <button class="btn-small btn-edit" @click="openEditDivisionModal(game.id, division)">编辑</button>
                        <button class="btn-small btn-danger" @click="deleteDivision(game.id, division)">删除</button>
                      </div>
                    </div>
                  </div>
                </div>
              </td>
            </tr>
            </template>
          </tbody>
        </table>
      </div>

      <!-- 新建竞赛模态框 -->
      <div v-if="showCreateGameModal" class="modal-overlay" @click="showCreateGameModal = false">
        <div class="modal" @click.stop>
          <div class="modal-header">
            <h4>{{ editingGame ? '编辑竞赛' : '新建竞赛' }}</h4>
            <button class="btn-close" @click="showCreateGameModal = false">×</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>竞赛名称</label>
              <input v-model="gameForm.title" type="text" placeholder="输入竞赛名称" class="form-input">
            </div>
            <div class="form-group">
              <label>开始时间</label>
              <input v-model="gameForm.start_time" type="datetime-local" class="form-input">
            </div>
            <div class="form-group">
              <label>结束时间</label>
              <input v-model="gameForm.end_time" type="datetime-local" class="form-input">
            </div>
            <div class="form-group">
              <label>竞赛类型</label>
              <select v-model="gameForm.game_type" class="form-input">
                <option value="official">正式赛</option>
                <option value="training">训练场</option>
                <option value="practice">练习</option>
              </select>
            </div>
            <div class="form-group">
              <label>
                <input v-model="gameForm.is_public" type="checkbox">
                公开竞赛
              </label>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="showCreateGameModal = false">取消</button>
            <button class="btn-primary" @click="saveGame">保存</button>
          </div>
        </div>
      </div>

      <!-- 新建/编辑分组模态框 -->
      <div v-if="showDivisionModal" class="modal-overlay" @click="closeDivisionModal">
        <div class="modal" @click.stop>
          <div class="modal-header">
            <h4>{{ editingDivision ? '编辑分组' : '新建分组' }}</h4>
            <button class="btn-close" @click="closeDivisionModal">×</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>分组名称 *</label>
              <input v-model="divisionForm.name" type="text" placeholder="输入分组名称" class="form-input">
            </div>
            <div class="form-group">
              <label>邀请码</label>
              <input v-model="divisionForm.invite_code" type="text" placeholder="可为空；写入后用于报名分流" class="form-input">
            </div>
            <div class="form-group">
              <label>学校范围</label>
              <input v-model="divisionForm.school_scope" type="text" placeholder="留空=全局；可填「高校」或具体校名" class="form-input">
              <small class="form-hint">与邀请码一起校验；写入后列表应能回读。</small>
            </div>
            <div class="form-group">
              <label>描述</label>
              <textarea v-model="divisionForm.description" placeholder="可选" class="form-input" rows="3"></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="closeDivisionModal">取消</button>
            <button class="btn-primary" @click="saveDivision">保存</button>
          </div>
        </div>
      </div>

      <!-- 分组成员模态框 -->
      <div v-if="showDivisionMembersModal" class="modal-overlay" @click="closeDivisionMembersModal">
        <div class="modal large-modal" @click.stop>
          <div class="modal-header">
            <h4>分组成员 - {{ currentDivisionName }}</h4>
            <button class="btn-close" @click="closeDivisionMembersModal">×</button>
          </div>
          <div class="modal-body">
            <table class="data-table">
              <thead>
                <tr>
                  <th>用户ID</th>
                  <th>昵称</th>
                  <th>邮箱</th>
                  <th>邀请码</th>
                  <th>验证时间</th>
                  <th>加入时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="m in divisionMembers" :key="m.user_id">
                  <td>{{ m.user_id }}</td>
                  <td>{{ m.nickname || '-' }}</td>
                  <td>{{ m.email || '-' }}</td>
                  <td>{{ m.invite_code_used || '-' }}</td>
                  <td>{{ formatTime(m.verified_at) }}</td>
                  <td>{{ formatTime(m.joined_at) }}</td>
                </tr>
                <tr v-if="divisionMembers.length === 0">
                  <td colspan="6" class="empty-state">暂无成员</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="closeDivisionMembersModal">关闭</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 题目管理 -->
    <div v-show="activeTab === 'challenges'" class="tab-content">
      <div class="card">
        <div class="card-header">
          <h3>题目列表</h3>
          <div style="display: flex; gap: 10px;">
            <select v-model="selectedGameId" class="form-input" style="width: 200px;">
              <option value="">选择竞赛...</option>
              <option v-for="game in games" :key="game.id" :value="game.id">
                {{ game.title }}
              </option>
            </select>
            <button class="btn-primary" @click="showCreateChallengeModal = true">新建题目</button>
          </div>
        </div>

        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>题目名称</th>
              <th>分类</th>
              <th>原始分值</th>
              <th>难度系数</th>
              <th>题目类型</th>
              <th>解题数</th>
              <th>附件</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="challenge in filteredChallenges" :key="challenge.id">
              <td>{{ challenge.id }}</td>
              <td>{{ challenge.title }}</td>
              <td>{{ challenge.category }}</td>
              <td>{{ challenge.original_points }}</td>
              <td>{{ challenge.difficulty }}</td>
              <td>
                <span class="badge">{{ getChallengeType(challenge.challenge_type) }}</span>
              </td>
              <td>
                <span class="badge badge-orange">{{ challenge.solved_count || 0 }}</span>
              </td>
              <td>
                <button v-if="challenge.attachment_id" class="btn-small btn-info" @click.stop="viewAttachment(challenge)">有附件</button>
                <span v-else class="text-muted">无附件</span>
              </td>
              <td>
                <button class="btn-small btn-edit" @click="editChallenge(challenge)">编辑</button>
                <button class="btn-small btn-danger" @click="deleteChallenge(challenge.id, challenge.game_id, challenge.title)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 创建/编辑题目模态框 -->
      <div v-if="showCreateChallengeModal" class="modal-overlay" @click="showCreateChallengeModal = false">
        <div class="modal large-modal" @click.stop>
          <div class="modal-header">
            <h4>{{ editingChallenge ? '编辑题目' : '新建题目' }}</h4>
            <button class="btn-close" @click="showCreateChallengeModal = false">×</button>
          </div>
          <div class="modal-body">
            <div class="form-row">
              <div class="form-group">
                <label>题目名称 *</label>
                <input v-model="challengeForm.title" type="text" placeholder="题目名称" class="form-input">
              </div>
              <div class="form-group">
                <label>分类 *</label>
                <input v-model="challengeForm.category" type="text" placeholder="Web/PWN/Crypto等" class="form-input">
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>原始分值</label>
                <input v-model.number="challengeForm.original_points" type="number" placeholder="1000" class="form-input">
              </div>
              <div class="form-group">
                <label>最小分值率</label>
                <input v-model.number="challengeForm.min_score_rate" type="number" placeholder="0.25" step="0.01" class="form-input">
              </div>
              <div class="form-group">
                <label>难度系数</label>
                <input v-model.number="challengeForm.difficulty" type="number" placeholder="5.0" step="0.1" class="form-input">
              </div>
            </div>

            <div class="form-group">
              <label>Flag 答案 *</label>
              <input v-model="challengeForm.flag" type="text" placeholder="flag{testflag}" class="form-input">
            </div>

            <div class="form-group">
              <label>题目描述</label>
              <textarea v-model="challengeForm.description" placeholder="题目描述" class="form-input" rows="4"></textarea>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>题目类型</label>
                <select v-model.number="challengeForm.challenge_type" class="form-input">
                  <option :value="0">静态附件 (所有队相同答案)</option>
                  <option :value="1">静态容器 (共享容器)</option>
                  <option :value="2">动态附件 (每队不同答案)</option>
                  <option :value="3">动态容器 (每队独立容器)</option>
                </select>
              </div>
              <div class="form-group">
                <label>提交限制 (0=无限)</label>
                <input v-model.number="challengeForm.submission_limit" type="number" placeholder="10" class="form-input">
              </div>
            </div>

            <!-- 动态 Flag 模板（动态附件 / 动态容器） -->
            <div v-if="[2, 3].includes(challengeForm.challenge_type)" class="form-group">
              <label>动态 Flag 模板 *</label>
              <input v-model="challengeForm.flag_template" type="text" placeholder="flag{{{team_hash}}}" class="form-input">
              <small class="form-hint">动态题必填；静态 Flag 字段可作为兜底答案。</small>
            </div>

            <!-- 容器相关配置 -->
            <div v-if="[1, 3].includes(challengeForm.challenge_type)" class="container-config">
              <h4 class="docker-heading"><DockerWhaleIcon class="docker-heading-ico" /> 容器配置</h4>
              <div class="form-row">
                <div class="form-group">
                  <label>Docker 镜像 *</label>
                  <input v-model="challengeForm.docker_image" type="text" placeholder="challenge-image:latest" class="form-input">
                </div>
                <div class="form-group">
                  <label>端口</label>
                  <input v-model.number="challengeForm.docker_port" type="number" placeholder="80" class="form-input">
                </div>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>内存限制 (MB)</label>
                  <input v-model.number="challengeForm.memory_limit" type="number" placeholder="256" class="form-input">
                </div>
                <div class="form-group">
                  <label>CPU核心数</label>
                  <input v-model.number="challengeForm.cpu_count" type="number" placeholder="1" class="form-input">
                </div>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>磁盘限制 (MB)</label>
                  <input v-model.number="challengeForm.storage_limit" type="number" placeholder="1024" class="form-input">
                </div>
                <div class="form-group">
                  <label>网络模式</label>
                  <select v-model="challengeForm.network_mode" class="form-input">
                    <option value="Open">Open</option>
                    <option value="Isolated">Isolated</option>
                    <option value="Custom">Custom</option>
                  </select>
                </div>
              </div>
              <div class="form-group">
                <label>
                  <input v-model="challengeForm.enable_traffic_capture" type="checkbox">
                  启用流量捕获（选手须使用 connection_url）
                </label>
              </div>
            </div>

            <!-- 附件上传：静态/动态附件题 -->
            <div v-if="[0, 2].includes(challengeForm.challenge_type)" class="attachment-section">
              <h4>题目附件</h4>
              <div class="form-group">
                <label>上传题目附件（单文件，建议 &lt; 20MB）</label>
                <div class="file-upload-box">
                  <input 
                    type="file" 
                    @change="handleFileUpload" 
                    class="file-input"
                    id="attachment"
                  >
                  <label for="attachment" class="file-label">
                    点击选择文件
                    <span v-if="challengeForm.attachment_file" style="display: block; margin-top: 8px;">
                      {{ challengeForm.attachment_file.name }}
                    </span>
                  </label>
                </div>
                <div v-if="challengeForm.attachment_meta" style="margin-top:8px;">
                  <small>已上传附件：<a :href="`/api/resources/${challengeForm.attachment_meta.id}/content`" target="_blank">{{ challengeForm.attachment_meta.filename }}</a></small>
                </div>
              </div>
            </div>

            <div class="form-group">
              <label>
                <input v-model="challengeForm.disable_blood_bonus" type="checkbox">
                禁用血液奖励
              </label>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="showCreateChallengeModal = false">取消</button>
            <button class="btn-primary" @click="saveChallenge">保存题目</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 作弊检测 -->
    <div v-show="activeTab === 'cheat'" class="tab-content">
      <div class="card">
        <div class="card-header">
          <h3>作弊检测记录</h3>
          <div style="display: flex; gap: 10px; flex-wrap: wrap; align-items: center;">
            <select v-model="selectedCheatGameId" class="form-input" style="width: 200px;">
              <option value="">全部竞赛</option>
              <option v-for="game in games" :key="game.id" :value="game.id">
                {{ game.title }}
              </option>
            </select>
            <select v-model="cheatStatusFilter" class="form-input" style="width: 140px;">
              <option value="">全部状态</option>
              <option value="pending">待审核</option>
              <option value="confirmed">已确认</option>
              <option value="dismissed">已驳回</option>
            </select>
            <button class="btn-small" @click="loadCheatRecords(selectedCheatGameId)">刷新</button>
          </div>
        </div>

        <div v-if="cheatRecords.length === 0" class="empty-state">
          <p>暂无作弊记录</p>
        </div>

        <div v-else class="cheat-list">
          <div v-for="record in cheatRecords" :key="record.id" class="cheat-card">
            <div class="cheat-header">
              <span class="cheat-id">#{{ record.id }}</span>
              <span class="cheat-type-badge" :class="`type-${record.cheat_type}`">
                {{ record.cheat_type === 'flag_origin' ? 'Flag来源' : record.cheat_type === 'similar_flag' ? '相似答案' : record.cheat_type === 'rapid_submission' ? '快速提交' : record.cheat_type }}
              </span>
              <span class="cheat-status-badge" :class="`status-${record.status}`">
                {{ record.status === 'pending' ? '待审核' : record.status === 'confirmed' ? '已确认' : record.status === 'dismissed' ? '已驳回' : record.status }}
              </span>
              <span class="cheat-time">{{ formatTime(record.detection_time) }}</span>
              <span v-if="record.similarity" class="cheat-similarity">
                相似度: 
                <span :class="['similarity-badge', { high: record.similarity > 0.9 }]">
                  {{ (record.similarity * 100).toFixed(1) }}%
                </span>
              </span>
            </div>
            <div class="cheat-content">
              <div class="user-pair">
                <div class="user-box">
                  <span class="user-label">提交者</span>
                  <span class="user-name">{{ record.source_user_name }}</span>
                  <span class="user-id">ID: {{ record.source_user_id }}</span>
                </div>
                <span class="vs-mark">vs</span>
                <div class="user-box">
                  <span class="user-label">被检测用户</span>
                  <span class="user-name">{{ record.target_user_name }}</span>
                  <span class="user-id">ID: {{ record.target_user_id }}</span>
                </div>
                <div v-if="record.flag_origin_user_name" class="user-box">
                  <span class="user-label">Flag原所有者</span>
                  <span class="user-name">{{ record.flag_origin_user_name }}</span>
                  <span class="user-id">ID: {{ record.flag_origin_user_id }}</span>
                </div>
              </div>
              <div class="reason-box">
                <strong>作弊原因：</strong>
                <p>{{ record.cheat_reason }}</p>
              </div>
              <div v-if="record.admin_note" class="admin-note-box">
                <strong>管理员备注：</strong>
                <p>{{ record.admin_note }}</p>
              </div>
            </div>
            <div class="cheat-actions">
              <button class="btn-small btn-warning" @click="handleCheatRecord(record, 'review')">
                备注
              </button>
              <template v-if="(record.status || 'pending') === 'pending'">
                <button class="btn-small btn-danger" @click="handleCheatRecord(record, 'confirm')">
                  确认作弊
                </button>
                <button class="btn-small btn-secondary" @click="handleCheatRecord(record, 'dismiss')">
                  驳回
                </button>
              </template>
              <span v-else class="text-muted">已处理，可刷新查看最新状态</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 排行榜统计 -->
    <div v-show="activeTab === 'scoreboard'" class="tab-content">
      <div class="card">
        <div class="card-header">
          <h3>排行榜 / 赛事统计</h3>
          <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
            <select v-model="selectedScoreboardGameId" class="form-input" style="width: 200px;">
              <option value="">选择竞赛...</option>
              <option v-for="game in games" :key="game.id" :value="game.id">
                {{ game.title }}
              </option>
            </select>
            <button
              class="btn-primary btn-small"
              :disabled="!selectedScoreboardGameId || exportingScoreboard"
              @click="exportScoreboardCsv"
            >导出 CSV</button>
          </div>
        </div>

        <div v-if="selectedScoreboardGameId && gameStats" class="game-stats-grid">
          <div class="stat-chip"><span>参赛人数</span><strong>{{ gameStats.participant_count || gameStats.participation_count || 0 }}</strong></div>
          <div class="stat-chip"><span>队伍数</span><strong>{{ gameStats.team_count || 0 }}</strong></div>
          <div class="stat-chip"><span>题目数</span><strong>{{ gameStats.challenge_count || 0 }}</strong></div>
          <div class="stat-chip"><span>总提交</span><strong>{{ gameStats.total_submissions || 0 }}</strong></div>
          <div class="stat-chip"><span>正确提交</span><strong>{{ gameStats.correct_submissions || 0 }}</strong></div>
          <div class="stat-chip"><span>正确率</span><strong>{{ gameStats.correct_rate || 0 }}%</strong></div>
          <div class="stat-chip"><span>待审作弊</span><strong>{{ gameStats.cheat_pending || 0 }}</strong></div>
          <div class="stat-chip"><span>已确认作弊</span><strong>{{ gameStats.cheat_confirmed || gameStats.cheat_count || 0 }}</strong></div>
        </div>

        <div v-if="selectedScoreboardGameId" class="scoreboard-container">
          <table class="data-table">
            <thead>
              <tr>
                <th style="width: 60px;">排名</th>
                <th>用户</th>
                <th style="width: 100px;">总分</th>
                <th style="width: 100px;">解题数</th>
                <th style="width: 150px;">最后提交</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in scoreboard" :key="item.team_id" :class="{ 'podium': index < 3 }">
                <td style="text-align: center; font-weight: bold;">
                  <span v-if="index === 0" class="medal">#1</span>
                  <span v-else-if="index === 1" class="medal">#2</span>
                  <span v-else-if="index === 2" class="medal">#3</span>
                  <span v-else>{{ index + 1 }}</span>
                </td>
                <td>{{ item.team_name }}</td>
                <td style="text-align: right; font-weight: bold;">{{ item.total_points }}</td>
                <td style="text-align: center;">{{ item.solved_challenges }}</td>
                <td>{{ formatTime(item.last_submission_time) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 首解 / 血榜 -->
    <div v-show="activeTab === 'firstsolve'" class="tab-content">
      <div class="card">
        <div class="card-header">
          <h3>首解 / 血榜</h3>
          <select v-model="selectedFirstSolveGameId" class="form-input" style="width: 220px;">
            <option value="">选择竞赛...</option>
            <option v-for="game in games" :key="game.id" :value="game.id">{{ game.title }}</option>
          </select>
        </div>
        <div v-if="!selectedFirstSolveGameId" class="empty-state"><p>请选择竞赛查看首解</p></div>
        <div v-else-if="firstSolves.length === 0" class="empty-state"><p>暂无首解记录</p></div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>时间</th>
              <th>题目</th>
              <th>用户</th>
              <th>队伍</th>
              <th>血</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="fs in firstSolves" :key="fs.id">
              <td>{{ formatTime(fs.solved_at) }}</td>
              <td>{{ fs.challenge_title || ('#' + fs.challenge_id) }}</td>
              <td>{{ fs.user_name || fs.username || ('#' + fs.user_id) }}</td>
              <td>{{ fs.team_name || '-' }}</td>
              <td>{{ fs.blood_level != null ? (['一血','二血','三血'][fs.blood_level] || fs.blood_level) : '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 锤子聚合 -->
    <div v-show="activeTab === 'hammer'" class="tab-content">
      <div class="card">
        <div class="card-header">
          <h3>锤子消息</h3>
          <div style="display:flex;gap:10px;align-items:center;">
            <select v-model="selectedHammerGameId" class="form-input" style="width: 220px;">
              <option value="">全部竞赛</option>
              <option v-for="game in games" :key="game.id" :value="game.id">{{ game.title }}</option>
            </select>
            <button class="btn-small" @click="loadHammerMessages">刷新</button>
          </div>
        </div>
        <div v-if="hammerMessages.length === 0" class="empty-state"><p>暂无锤子消息</p></div>
        <div v-else class="cheat-list">
          <div v-for="m in hammerMessages" :key="m.id" class="cheat-card">
            <div class="cheat-header">
              <span class="cheat-id">#{{ m.id }}</span>
              <span class="cheat-type-badge">{{ m.challenge_title || ('题目#' + m.challenge_id) }}</span>
              <span class="cheat-status-badge" :class="m.is_staff ? 'status-confirmed' : 'status-pending'">
                {{ m.is_staff ? '裁判' : '选手' }}
              </span>
              <span class="cheat-time">{{ formatTime(m.created_at) }}</span>
            </div>
            <div class="cheat-content">
              <strong>{{ m.nickname || ('用户#' + m.user_id) }}</strong>
              <p>{{ m.content }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 动态附件包 -->
    <div v-show="activeTab === 'traffic'" class="tab-content">
      <div class="card">
        <TrafficCapturePanel :game-id-prop="selectedGameId || null" />
      </div>
    </div>

    <div v-show="activeTab === 'packages'" class="tab-content">
      <div class="card">
        <DynamicPackageManager :game-id="selectedGameId || null" />
      </div>
    </div>

    <div v-show="activeTab === 'seasons'" class="tab-content">
      <div class="card">
        <SeasonManager />
      </div>
    </div>

    <div v-show="activeTab === 'teams'" class="tab-content">
      <div class="card">
        <div class="card-header" style="align-items:center; gap:12px;">
          <h3 style="margin:0;">管理端：战队列表</h3>

          <div style="margin-left:12px; flex:1; display:flex; gap:12px; align-items:center;">
            <input v-model="searchQuery" placeholder="搜索队名、邀请码或成员" class="form-input" style="max-width:360px;" />
            <select v-model.number="pageSize" @change="setPageSize(pageSize)" class="form-input" style="width:120px;">
              <option v-for="s in pageSizes" :key="s" :value="s">每页 {{ s }}</option>
            </select>
          </div>

          <div style="display:flex; gap:10px;">
            <button class="btn-primary" @click="loadAdminTeams">刷新</button>
            <button class="btn-danger" @click="deleteAllAdminTeams">删除全部</button>
          </div>
        </div>

        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>队伍名</th>
              <th>邀请码</th>
              <th>成员数</th>
              <th>成员列表</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in adminTeams" :key="t.id">
              <td>{{ t.id }}</td>
              <td>{{ t.name }}</td>
              <td>{{ t.invite_code }}</td>
              <td>{{ t.members.length }}</td>
              <td>
                <div v-for="m in t.members" :key="m.id">{{ m.nickname || m.email }}</div>
              </td>
              <td>
                <button class="btn-small btn-danger" @click="deleteAdminTeam(t.id)">删除</button>
              </td>
            </tr>
            <tr v-if="adminTeams.length === 0">
              <td colspan="6" class="empty-state">暂无队伍</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
<script>
import DynamicPackageManager from './DynamicPackageManager.vue'
import SeasonManager from './SeasonManager.vue'
import TrafficCapturePanel from './TrafficCapturePanel.vue'
import { useMessage } from 'naive-ui'
import { apiErrorFromPayload } from '@/utils/apiError'
import { ctfAdmin } from '@/services/admin/ctf'
import { parseJsonResponse, isApiSuccess } from '@/utils/http'

import DockerWhaleIcon from '@/components/icons/DockerWhaleIcon.vue'

export default {
  name: 'CtfManagement',
  components: {
    DockerWhaleIcon,
    DynamicPackageManager,
    SeasonManager,
    TrafficCapturePanel,
  },
  setup() {
    let message
    try {
      message = useMessage()
    } catch (e) {
      message = {
        info: (t) => console.info('[message.info]', t),
        success: (t) => console.log('[message.success]', t),
        warning: (t) => console.warn('[message.warning]', t),
        error: (t) => console.error('[message.error]', t),
      }
    }
    return { message }
  },
  data() {
    return {
      activeTab: 'games',
      tabs: ['games', 'challenges', 'packages', 'seasons', 'traffic', 'cheat', 'scoreboard', 'firstsolve', 'hammer', 'teams'],
      gameTypeFilter: '',
      showEphemeral: false,
      games: [],
      challenges: [],
      cheatRecords: [],
      scoreboard: [],
      firstSolves: [],
      hammerMessages: [],
      selectedHammerGameId: '',

      selectedGameId: '',
      selectedCheatGameId: '',
      cheatStatusFilter: '',
      selectedScoreboardGameId: '',
      gameStats: null,
      exportingScoreboard: false,
      selectedFirstSolveGameId: '',

      showCreateGameModal: false,
      showCreateChallengeModal: false,
      showDivisionModal: false,
      showDivisionMembersModal: false,

      editingGame: null,
      editingChallenge: null,
      editingDivision: null,
      editingGameId: null,

      gameForm: {},
      challengeForm: {},
      divisionForm: {},

      expandedGameId: null,
      gameDivisions: {},
      loadingDivisions: {},
      divisionMembers: [],
      currentDivisionName: '',

      loading: false,

      adminTeams: [],
      searchQuery: '',
      page: 1,
      pageSize: 10,
      pageSizes: [5, 10, 20, 50]
    };
  },

  computed: {
    filteredChallenges() {
      if (!this.selectedGameId) return this.challenges;
      return this.challenges.filter(c => c.game_id === parseInt(this.selectedGameId));
    }
  },

  watch: {
    activeTab() { this.onActiveTabChanged(); },
    selectedGameId(newVal) {
      if (!newVal) {
        this.challenges = [];
        return;
      }
      this.loadChallenges(newVal);
    },
    selectedCheatGameId(newVal) {
      this.loadCheatRecords(newVal);
    },
    cheatStatusFilter() {
      this.loadCheatRecords(this.selectedCheatGameId);
    },
    selectedScoreboardGameId(newVal) {
      if (!newVal) {
        this.scoreboard = [];
        this.gameStats = null;
        return;
      }
      this.loadScoreboard(newVal);
      this.loadGameStats(newVal);
    },
    selectedHammerGameId() {
      this.loadHammerMessages();
    },
    selectedFirstSolveGameId(newVal) {
      if (!newVal) {
        this.firstSolves = [];
        return;
      }
      this.loadFirstSolves(newVal);
    }
  },

  methods: {
    getTabCode(tab) {
      const codes = {
        games: 'GMS',
        challenges: 'CHL',
        packages: 'PKG',
        seasons: 'SEA',
        traffic: 'TRF',
        cheat: 'CHT',
        scoreboard: 'SCR',
        firstsolve: 'FST',
        hammer: 'HMR',
        teams: 'TMS',
      };
      return codes[tab] || 'TAB';
    },
    getTabLabel(tab) {
      const labels = {
        games: '竞赛管理',
        challenges: '题目管理',
        cheat: '作弊检测',
        scoreboard: '排行榜',
        firstsolve: '首解',
        hammer: '锤子',
        traffic: '流量捕获',
        packages: '动态附件包',
        seasons: '赛季管理',
        teams: '队伍管理',
      };
      return labels[tab] || tab;
    },

    async loadAdminTeams() {
      try {
        // JWT 仅在 HttpOnly Cookie；必须 credentials:include（ctfAdmin/authFetch）
        const res = await ctfAdmin.listTeams()
        let data = null
        try {
          data = await res.json()
        } catch (e) {
          const txt = await res.text()
          console.error('loadAdminTeams: non-JSON response', res.status, txt.slice(0, 200))
          throw new Error(`Unexpected response (${res.status}): see console for details`)
        }
        this.adminTeams = data.teams || data.data?.teams || []
        this.page = 1
      } catch (e) { console.error('加载管理员队伍失败', e); this.adminTeams = []; }
    },

    async deleteAdminTeam(teamId) {
      if (!confirm('确定要删除该队伍并解散？')) return;
      try {
        const res = await ctfAdmin.deleteTeam(teamId)
        if (res.ok) { this.message.success('已删除'); await this.loadAdminTeams(); }
        else {
          try {
            const d = await res.json();
            this.message.error(apiErrorFromPayload(d, '删除失败'));
          } catch (e) {
            this.message.error('删除失败: HTTP ' + res.status);
          }
        }
      } catch (e) { this.message.error(e.message || '删除失败'); }
    },

    async deleteAllAdminTeams() {
      if (!confirm('确定要删除所有队伍并解散？此操作不可逆')) return;
      try {
        const res = await ctfAdmin.deleteAllTeams()
        try {
          const d = await res.json();
          if (res.ok) { this.message.success('已删除 ' + (d.deleted || d.data?.deleted || 0) + ' 个队伍'); await this.loadAdminTeams(); }
          else { this.message.error(apiErrorFromPayload(d, '删除失败')); }
        } catch (e) {
          this.message.error('删除失败: HTTP ' + res.status);
        }
      } catch (e) { this.message.error(e.message || '删除失败'); }
    },

    filteredAdminTeams() {
      const q = (this.searchQuery || '').trim().toLowerCase();
      if (!q) return this.adminTeams;
      return this.adminTeams.filter(t => {
        if ((t.name || '').toLowerCase().includes(q)) return true;
        if ((t.invite_code || '').toLowerCase().includes(q)) return true;
        for (const m of (t.members||[])) {
          if ((m.nickname||m.email||'').toLowerCase().includes(q)) return true;
        }
        return false;
      });
    },

    paginatedAdminTeams() {
      const list = this.filteredAdminTeams();
      const start = (this.page - 1) * this.pageSize;
      return list.slice(start, start + this.pageSize);
    },

    totalFilteredTeams() { return this.filteredAdminTeams().length; },
    totalPages() { return Math.max(1, Math.ceil(this.totalFilteredTeams() / this.pageSize)); },
    goPrevPage() { if (this.page > 1) this.page--; },
    goNextPage() { if (this.page < this.totalPages()) this.page++; },
    setPageSize(size) { this.pageSize = size; this.page = 1; },

    async loadGames() {
      try {
        const res = await ctfAdmin.listGames(200, {
          game_type: this.gameTypeFilter || undefined,
          include_ephemeral: !!this.showEphemeral,
        });
        const parsed = await parseJsonResponse(res);
        if (!isApiSuccess(parsed)) {
          if (parsed.status === 401) {
            this.message.warning('登录已过期，请重新登录');
            try { localStorage.removeItem('neepu_token'); localStorage.removeItem('neepu_user'); } catch (e) {}
            this.$router && this.$router.push('/auth');
            return;
          }
          this.games = [];
          this.message.error(apiErrorFromPayload(parsed.data, '加载竞赛列表失败'));
          return;
        }
        const raw = parsed.data?.data;
        this.games = Array.isArray(raw) ? raw : (raw?.items || []);
        if (!this.selectedGameId && this.games.length > 0 && this.activeTab === 'challenges') {
          this.selectedGameId = this.games[0].id;
        }
      } catch (e) {
        this.games = [];
        this.message.error(e.message || '加载竞赛列表失败');
      }
    },

    async toggleGameDivisions(gameId) {
      if (this.expandedGameId === gameId) {
        this.expandedGameId = null;
        return;
      }
      this.expandedGameId = gameId;
      await this.loadGameDivisions(gameId);
    },

    async loadGameDivisions(gameId) {
      try {
        this.loadingDivisions[gameId] = true;
        const res = await ctfAdmin.listDivisions(gameId);
        const parsed = await parseJsonResponse(res);
        if (!isApiSuccess(parsed)) {
          this.message.error(apiErrorFromPayload(parsed.data, '加载分组失败'));
          this.gameDivisions[gameId] = [];
          return;
        }
        const rows = parsed.data?.data || parsed.data || [];
        this.gameDivisions[gameId] = Array.isArray(rows) ? rows.filter(d => d && d.id !== -1) : [];
      } catch (e) {
        console.error('loadGameDivisions error', e);
        this.message.error(e.message || '加载分组失败');
        this.gameDivisions[gameId] = [];
      } finally {
        this.loadingDivisions[gameId] = false;
      }
    },

    openCreateDivisionModal(gameId) {
      this.editingDivision = null;
      this.editingGameId = gameId;
      this.divisionForm = this.getEmptyDivisionForm();
      this.showDivisionModal = true;
    },

    openEditDivisionModal(gameId, division) {
      this.editingDivision = division;
      this.editingGameId = gameId;
      this.divisionForm = {
        name: division.name || '',
        invite_code: division.invite_code || '',
        school_scope: division.school_scope || '',
        description: division.description || ''
      };
      this.showDivisionModal = true;
    },

    closeDivisionModal() {
      this.showDivisionModal = false;
      this.editingDivision = null;
      this.editingGameId = null;
      this.divisionForm = this.getEmptyDivisionForm();
    },

    async saveDivision() {
      if (!this.editingGameId) return;
      if (!String(this.divisionForm.name || '').trim()) {
        this.message.warning('分组名称不能为空');
        return;
      }
      try {
        const gameId = this.editingGameId;
        const payload = {
          name: String(this.divisionForm.name).trim(),
          invite_code: String(this.divisionForm.invite_code || '').trim() || null,
          school_scope: String(this.divisionForm.school_scope || '').trim() || null,
          description: String(this.divisionForm.description || '').trim() || null,
        };
        let res;
        if (this.editingDivision && this.editingDivision.id) {
          res = await ctfAdmin.updateDivision(gameId, this.editingDivision.id, payload);
        } else {
          res = await ctfAdmin.createDivision(gameId, payload);
        }
        const parsed = await parseJsonResponse(res);
        if (!isApiSuccess(parsed)) {
          this.message.error(apiErrorFromPayload(parsed.data, '保存失败'));
          return;
        }
        const updated = parsed.data?.data || parsed.data || null;
        if (updated) {
          if (payload.invite_code && updated.invite_code !== payload.invite_code) {
            this.message.warning('已保存，但邀请码回读不一致，请刷新核对');
          }
          if ((payload.school_scope || null) !== (updated.school_scope || null)) {
            this.message.warning('已保存，但学校范围回读不一致，请刷新核对');
          }
        }
        if (this.expandedGameId !== gameId) this.expandedGameId = gameId;
        this.message.success(this.editingDivision ? '分组已更新' : '分组已创建');
        this.closeDivisionModal();
        await this.loadGameDivisions(gameId);
      } catch (e) {
        this.message.error(e.message || '保存失败');
      }
    },

    async deleteDivision(gameId, division) {
      const name = (division && division.name) || ('#' + (division && division.id));
      const divisionId = division && division.id;
      if (!divisionId || divisionId < 0) {
        this.message.warning('该条目不是可删除的赛道');
        return;
      }
      if (!confirm('确认删除分组「' + name + '」？此操作不可恢复。')) return;
      try {
        const res = await ctfAdmin.deleteDivision(gameId, divisionId);
        const parsed = await parseJsonResponse(res);
        if (isApiSuccess(parsed)) {
          this.message.success('已删除「' + name + '」');
          await this.loadGameDivisions(gameId);
        } else {
          this.message.error(apiErrorFromPayload(parsed.data, '删除失败'));
        }
      } catch (e) {
        this.message.error(e.message || '删除失败');
      }
    },

    async viewDivisionMembers(gameId, division) {
      if (!division?.id || division.id < 0) {
        this.message.warning('公开赛聚合视图无成员明细，请先创建真实赛道');
        return;
      }
      try {
        const res = await ctfAdmin.listDivisionMembers(gameId, division.id);
        const parsed = await parseJsonResponse(res);
        if (!isApiSuccess(parsed)) {
          this.message.error(apiErrorFromPayload(parsed.data, '获取成员失败'));
          return;
        }
        const body = parsed.data?.data || parsed.data || {};
        this.divisionMembers = body.members || [];
        this.currentDivisionName = division.name || body.division?.name || '';
        this.showDivisionMembersModal = true;
      } catch (e) {
        this.message.error(e.message || '获取成员失败');
      }
    },

    closeDivisionMembersModal() {
      this.showDivisionMembersModal = false;
      this.divisionMembers = [];
      this.currentDivisionName = '';
    },

    async copyToClipboard(text) {
      if (!text) return;
      try {
        await navigator.clipboard.writeText(text);
        this.message.success('已复制');
      } catch (e) {
        const input = document.createElement('input');
        input.value = text;
        document.body.appendChild(input);
        input.select();
        document.execCommand('copy');
        document.body.removeChild(input);
        this.message.success('已复制');
      }
    },

    async editGame(game) {
      this.editingGame = game;
      this.gameForm = { title: game.title, start_time: game.start_time, end_time: game.end_time, is_public: game.is_public, game_type: game.game_type || 'official' };
      this.showCreateGameModal = true;
    },

    async deleteGame(gameId) {
      if (!confirm('确认删除此比赛？')) return;
      try {
        const res = await ctfAdmin.deleteGame(gameId);
        const parsed = await parseJsonResponse(res);
        if (isApiSuccess(parsed)) {
          this.message.success('已删除');
          await this.loadGames();
        } else {
          this.message.error(apiErrorFromPayload(parsed.data, '删除失败'));
        }
      } catch (e) { this.message.error(e.message || '删除失败'); }
    },

    async archiveGame(game) {
      if (!confirm(`确认归档 "${game.title}" ？归档后将不能加入和计分。`)) return;
      try {
        const res = await ctfAdmin.archiveGame(game.id);
        const parsed = await parseJsonResponse(res);
        if (isApiSuccess(parsed)) {
          this.message.success('已归档');
          await this.loadGames();
        } else {
          this.message.error(apiErrorFromPayload(parsed.data, '归档失败'));
        }
      } catch (e) { this.message.error(e.message || '归档失败'); }
    },

    async saveGame() {
      // 创建或更新比赛（主路径 /api/competitions/admin/*）
      try {
        const payload = {
          title: this.gameForm.title,
          start_time: this.gameForm.start_time,
          end_time: this.gameForm.end_time,
          is_public: !!this.gameForm.is_public,
          game_type: this.gameForm.game_type || 'official'
        };
        let res;
        if (this.editingGame && this.editingGame.id) {
          res = await ctfAdmin.updateGame(this.editingGame.id, payload);
        } else {
          res = await ctfAdmin.createGame(payload);
        }
        const parsed = await parseJsonResponse(res);
        if (isApiSuccess(parsed)) {
          this.showCreateGameModal = false;
          this.editingGame = null;
          this.gameForm = this.getEmptyGameForm();
          await this.loadGames();
          this.message.success('已保存');
        } else {
          this.message.error(apiErrorFromPayload(parsed.data, '保存失败'));
        }
      } catch (e) {
        this.message.error(e.message || '保存失败');
      }
    },

    handleFileUpload(e) {
      const f = e.target.files && e.target.files[0];
      if (f) this.challengeForm.attachment_file = f;
    },

    async viewAttachment(challenge) {
      try {
        const id = challenge.attachment_id || (challenge.attachment && challenge.attachment.id) || (this.challengeForm && this.challengeForm.attachment_meta && this.challengeForm.attachment_meta.id);
        if (!id) { this.message.warning('未找到附件 ID'); return };
        // open the resource content endpoint in a new tab for preview/download
        const url = `/api/resources/${id}/content`;
        window.open(url, '_blank');
      } catch (e) {
        console.error('viewAttachment error', e);
        this.message.error('无法打开附件');
      }
    },

    async saveChallenge() {
      try {
        if (!this.selectedGameId && !(this.editingChallenge && this.editingChallenge.game_id)) {
          this.message.warning('请选择所属竞赛');
          return;
        }
        const gameId = this.selectedGameId || (this.editingChallenge && this.editingChallenge.game_id);
        const t = Number(this.challengeForm.challenge_type || 0);
        if (!String(this.challengeForm.title || '').trim() || !String(this.challengeForm.category || '').trim()) {
          this.message.warning('请填写题目名称与分类');
          return;
        }
        if (!String(this.challengeForm.flag || '').trim() && ![2, 3].includes(t)) {
          this.message.warning('请填写 Flag 答案');
          return;
        }
        if ([1, 3].includes(t) && !String(this.challengeForm.docker_image || '').trim()) {
          this.message.warning('容器题必须填写 Docker 镜像');
          return;
        }
        if ([2, 3].includes(t) && !String(this.challengeForm.flag_template || '').trim()) {
          this.message.warning('动态题必须填写 Flag 模板');
          return;
        }
        if (this.challengeForm.attachment_file && this.challengeForm.attachment_file.size > 20 * 1024 * 1024) {
          this.message.warning('附件过大（上限约 20MB）');
          return;
        }

        const fields = [
          'title', 'category', 'original_points', 'min_score_rate', 'difficulty', 'flag', 'flag_template',
          'description', 'challenge_type', 'submission_limit', 'docker_image', 'docker_port',
          'memory_limit', 'cpu_count', 'storage_limit', 'network_mode',
        ];
        const payload = {};
        for (const k of fields) {
          if (this.challengeForm[k] !== undefined && this.challengeForm[k] !== null && this.challengeForm[k] !== '') {
            payload[k] = this.challengeForm[k];
          }
        }
        payload.disable_blood_bonus = !!this.challengeForm.disable_blood_bonus;
        payload.enable_traffic_capture = !!this.challengeForm.enable_traffic_capture;
        if (!payload.flag && payload.flag_template) payload.flag = 'dynamic';

        const isUpdate = !!(this.editingChallenge && this.editingChallenge.id);
        let challengeId = isUpdate ? this.editingChallenge.id : null;

        if (isUpdate) {
          const res = await ctfAdmin.updateChallenge(gameId, challengeId, payload);
          const parsed = await parseJsonResponse(res);
          if (!isApiSuccess(parsed)) {
            this.message.error(apiErrorFromPayload(parsed.data, '保存失败'));
            return;
          }
        } else {
          const res = await ctfAdmin.createChallenge(gameId, payload);
          const parsed = await parseJsonResponse(res);
          if (!isApiSuccess(parsed)) {
            this.message.error(apiErrorFromPayload(parsed.data, '保存失败'));
            return;
          }
          challengeId = parsed.data?.data?.id || parsed.data?.id;
          if (!challengeId) {
            this.message.error('创建成功但未返回题目 ID');
            return;
          }
        }

        if (this.challengeForm.attachment_file) {
          if (![0, 2].includes(t)) {
            this.message.warning('当前题型不支持附件，已跳过上传');
          } else {
            const form = new FormData();
            form.append('file', this.challengeForm.attachment_file);
            const attachRes = await ctfAdmin.uploadChallengeAttachment(gameId, challengeId, form);
            const attachParsed = await parseJsonResponse(attachRes);
            if (!isApiSuccess(attachParsed)) {
              this.message.error(apiErrorFromPayload(attachParsed.data, '题目已保存，但附件上传失败'));
              await this.loadChallenges(gameId);
              return;
            }
            this.message.success('题目与附件已保存');
          }
        } else {
          this.message.success('题目已保存');
        }

        this.showCreateChallengeModal = false;
        this.editingChallenge = null;
        this.challengeForm = this.getEmptyChallengeForms();
        if (gameId) await this.loadChallenges(gameId);
      } catch (e) {
        this.message.error(e.message || '保存失败');
      }
    },

    async deleteChallenge(challengeId, gameId, title) {
      const name = title || ('#' + challengeId);
      if (!confirm('确认删除题目「' + name + '」？此操作不可恢复。')) return;
      try {
        const gid = gameId || this.selectedGameId;
        const res = await ctfAdmin.deleteChallenge(gid, challengeId);
        const parsed = await parseJsonResponse(res);
        if (isApiSuccess(parsed)) {
          this.message.success('已删除「' + name + '」');
          await this.loadChallenges(gid);
          await this.loadGames();
        } else {
          if (parsed.status === 403) {
            this.message.warning('需要管理员权限或登录已过期，请重新登录');
            return;
          }
          this.message.error(apiErrorFromPayload(parsed.data, '删除失败'));
        }
      } catch (e) {
        this.message.error(e.message || '删除失败');
      }
    },

    async editChallenge(challenge) {
      // populate form for editing — fetch full admin detail to include flag and attachment meta
      this.editingChallenge = challenge;
      this.challengeForm = this.getEmptyChallengeForms();
      try {
        const gid = challenge.game_id || this.selectedGameId;
        const res = await ctfAdmin.getChallenge(gid, challenge.id);
        if (res.ok) {
          const d = await res.json();
          const c = d.data || {};
          this.challengeForm = Object.assign(this.getEmptyChallengeForms(), {
            title: c.title || '',
            category: c.category || '',
            original_points: c.original_points || c.points || 1000,
            min_score_rate: c.min_score_rate || 0.25,
            difficulty: c.difficulty || 5.0,
            flag: c.flag || '',
            flag_template: c.flag_template || '',
            description: c.description || '',
            challenge_type: c.challenge_type || 0,
            submission_limit: c.submission_limit || 0,
            docker_image: c.docker_image || '',
            docker_port: c.docker_port || 80,
            memory_limit: c.memory_limit || 256,
            cpu_count: c.cpu_count || 1,
            storage_limit: c.storage_limit || 1024,
            network_mode: c.network_mode || 'Open',
            enable_traffic_capture: !!c.enable_traffic_capture,
            disable_blood_bonus: !!c.disable_blood_bonus,
            attachment_file: null,
            attachment_meta: c.attachment || (c.attachment_id ? { id: c.attachment_id, filename: '附件#' + c.attachment_id } : null)
          });
        } else {
          // fallback to using provided challenge object
          this.challengeForm = Object.assign(this.getEmptyChallengeForms(), {
            title: challenge.title || '',
            category: challenge.category || '',
            original_points: challenge.original_points || 1000,
            min_score_rate: challenge.min_score_rate || 0.25,
            difficulty: challenge.difficulty || 5.0,
            flag: '',
            flag_template: challenge.flag_template || '',
            description: challenge.description || '',
            challenge_type: challenge.challenge_type || 0,
            submission_limit: challenge.submission_limit || 0,
            docker_image: challenge.docker_image || '',
            docker_port: challenge.docker_port || 80,
            memory_limit: challenge.memory_limit || 256,
            cpu_count: challenge.cpu_count || 1,
            storage_limit: challenge.storage_limit || 1024,
            network_mode: challenge.network_mode || 'Open',
            enable_traffic_capture: !!challenge.enable_traffic_capture,
            disable_blood_bonus: !!challenge.disable_blood_bonus,
            attachment_file: null,
            attachment_meta: null
          });
        }
      } catch (e) {
        console.error('editChallenge: failed to fetch detail', e);
      }
      this.showCreateChallengeModal = true;
    },

    onActiveTabChanged() {
      if (this.activeTab === 'teams') {
        this.loadAdminTeams();
      }
      if (this.activeTab === 'challenges') {
        // ensure games are loaded, then select first game if none
        if (!this.games || this.games.length === 0) {
          this.loadGames().then(() => {
            if (!this.selectedGameId && this.games.length > 0) this.selectedGameId = this.games[0].id;
          }).catch(() => {});
        } else {
          if (!this.selectedGameId && this.games.length > 0) this.selectedGameId = this.games[0].id;
          if (this.selectedGameId) this.loadChallenges(this.selectedGameId);
        }
      }
      if (this.activeTab === 'cheat') {
        // 加载竞赛列表用于选择
        if (!this.games || this.games.length === 0) {
          this.loadGames();
        }
        // 加载作弊记录
        this.loadCheatRecords('');
      }
      if (this.activeTab === 'scoreboard') {
        // 加载竞赛列表用于选择
        if (!this.games || this.games.length === 0) {
          this.loadGames();
        }
      }
      if (this.activeTab === 'firstsolve') {
        // 加载竞赛列表用于选择
        if (!this.games || this.games.length === 0) {
          this.loadGames();
        }
      }
    },

    async loadChallenges(gameId) {
      try {
        console.debug('loadChallenges: requesting', gameId);
        const res = await ctfAdmin.listAdminChallenges(gameId);
        const parsed = await parseJsonResponse(res);
        if (!isApiSuccess(parsed)) {
          console.error('loadChallenges failed', parsed.status);
          this.challenges = [];
          return;
        }
        const body = parsed.data?.data || parsed.data;
        this.challenges = body?.items || body?.challenges || (Array.isArray(body) ? body : []);
      } catch (e) {
        console.error('加载题目列表失败:', e);
        this.challenges = [];
      }
    },

    async loadScoreboard(gameId) {
      try {
        const res = await ctfAdmin.getScoreboard(gameId);
        const parsed = await parseJsonResponse(res);
        if (!isApiSuccess(parsed)) {
          console.error('loadScoreboard failed', parsed.status);
          this.scoreboard = [];
          return;
        }
        const body = parsed.data?.data || parsed.data;
        this.scoreboard = body?.rankings || body?.items || [];
      } catch (e) {
        console.error('加载排行榜失败:', e);
        this.scoreboard = [];
      }
    },

    async loadGameStats(gameId) {
      try {
        const res = await ctfAdmin.getGameStats(gameId);
        const parsed = await parseJsonResponse(res);
        if (!isApiSuccess(parsed)) {
          this.gameStats = null;
          this.message.error(apiErrorFromPayload(parsed.data, '加载赛事统计失败'));
          return;
        }
        const body = parsed.data?.data || parsed.data || {};
        this.gameStats = body.statistics || body;
      } catch (e) {
        this.gameStats = null;
        this.message.error(e.message || '加载赛事统计失败');
      }
    },

    async exportScoreboardCsv() {
      if (!this.selectedScoreboardGameId) {
        this.message.warning('请先选择竞赛');
        return;
      }
      this.exportingScoreboard = true;
      try {
        const res = await ctfAdmin.exportScoreboard(this.selectedScoreboardGameId);
        if (!res.ok) {
          const parsed = await parseJsonResponse(res);
          this.message.error(apiErrorFromPayload(parsed.data, '导出失败'));
          return;
        }
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `scoreboard_${this.selectedScoreboardGameId}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        this.message.success('已导出排行榜 CSV');
      } catch (e) {
        this.message.error(e.message || '导出失败');
      } finally {
        this.exportingScoreboard = false;
      }
    },

    async loadHammerMessages() {
      try {
        let params = 'page=1&per_page=50';
        if (this.selectedHammerGameId) params += `&game_id=${this.selectedHammerGameId}`;
        const res = await ctfAdmin.listHammerMessages(params);
        const parsed = await parseJsonResponse(res);
        if (!isApiSuccess(parsed)) {
          this.hammerMessages = [];
          this.message.error(apiErrorFromPayload(parsed.data, '加载锤子消息失败'));
          return;
        }
        this.hammerMessages = parsed.data?.data?.items || parsed.data?.items || [];
      } catch (e) {
        this.hammerMessages = [];
        this.message.error(e.message || '加载锤子消息失败');
      }
    },

    async loadFirstSolves(gameId) {
      try {
        const res = await ctfAdmin.listFirstSolves(gameId);
        const parsed = await parseJsonResponse(res);
        if (!isApiSuccess(parsed)) {
          console.error('loadFirstSolves failed', parsed.status);
          this.firstSolves = [];
          return;
        }
        const body = parsed.data?.data || parsed.data;
        const rows = body?.items || body || [];
        this.firstSolves = (Array.isArray(rows) ? rows : []).map(fs => ({
          ...fs,
          challenge_title: fs.challenge_title || `题目 ${fs.challenge_id}`
        }));
      } catch (e) {
        console.error('加载一血二血失败:', e);
        this.firstSolves = [];
      }
    },

    async loadCheatRecords(gameId = '') {
      try {
        let params = 'page=1&per_page=50';
        if (gameId) params += `&game_id=${gameId}`;
        if (this.cheatStatusFilter) params += `&status=${this.cheatStatusFilter}`;
        const res = await ctfAdmin.listCheatRecords(params);
        const parsed = await parseJsonResponse(res);
        if (!isApiSuccess(parsed)) {
          console.error('loadCheatRecords failed', parsed.status);
          this.cheatRecords = [];
          return;
        }
        this.cheatRecords = parsed.data?.data?.items || parsed.data?.items || [];
      } catch (e) {
        console.error('加载作弊记录失败:', e);
        this.cheatRecords = [];
      }
    },

    async handleCheatRecord(record, action) {
      let payload = {};
      if (action === 'review') {
        const note = prompt('请输入审核备注：');
        if (note === null) return;
        payload = { admin_note: note };
      } else if (action === 'confirm') {
        payload = {};
      } else if (action === 'dismiss') {
        const note = prompt('请输入驳回原因：');
        if (note === null) return;
        payload = { admin_note: note };
      } else {
        console.error('Unknown action:', action);
        return;
      }

      try {
        let res;
        if (action === 'review') res = await ctfAdmin.reviewCheatRecord(record.id, payload);
        else if (action === 'confirm') res = await ctfAdmin.confirmCheatRecord(record.id, payload);
        else res = await ctfAdmin.dismissCheatRecord(record.id, payload);

        const parsed = await parseJsonResponse(res);
        if (isApiSuccess(parsed)) {
          const actionLabel = { review: '审核', confirm: '确认', dismiss: '驳回' }[action];
          this.message.success(`已${actionLabel}此作弊记录`);
          await this.loadCheatRecords(this.selectedCheatGameId);
        } else {
          this.message.error(apiErrorFromPayload(parsed.data, '操作失败'));
        }
      } catch (e) {
        this.message.error(e.message || '操作失败');
      }
    },

    getChallengeName(submissionId) {
      // 这里可以根据submission ID查找对应的challenge name
      // 目前返回占位符，可以通过维护challenge缓存来优化
      return '题目';
    },

    formatTime(t) { if (!t) return '-'; return new Date(t).toLocaleString('zh-CN'); },

    getChallengeType(type) {
      // human friendly label for challenge types
      const map = {
        0: '静态附件',
        1: '静态容器',
        2: '动态附件',
        3: '动态容器'
      };
      return map[type] || '未知类型';
    },

    getEmptyGameForm() { return { title: '', start_time: '', end_time: '', is_public: true, game_type: 'official' }; },
    gameTypeLabel(game) {
      const t = (game && game.game_type) || 'official';
      if (game && game.is_ephemeral) return '探针';
      if (t === 'training') return '训练';
      if (t === 'practice') return '练习';
      return '正式';
    },
    gameTypeBadgeClass(game) {
      if (game && game.is_ephemeral) return 'badge-gray';
      const t = (game && game.game_type) || 'official';
      if (t === 'training' || t === 'practice') return 'badge-blue';
      return 'badge-green';
    },
    getEmptyDivisionForm() { return { name: '', invite_code: '', school_scope: '', description: '' }; },
    getEmptyChallengeForms() {
      return {
        title: '', category: '', original_points: 1000, min_score_rate: 0.25, difficulty: 5.0,
        flag: '', flag_template: '', description: '', challenge_type: 0, submission_limit: 0,
        docker_image: '', docker_port: 80, memory_limit: 256, cpu_count: 1,
        storage_limit: 1024, network_mode: 'Open', enable_traffic_capture: false,
        disable_blood_bonus: false, attachment_file: null, attachment_meta: null,
      };
    }
  },

  mounted() {
    const qTab = this.$route?.query?.tab;
    if (qTab && this.tabs.includes(qTab)) this.activeTab = qTab;
    const qGid = this.$route?.query?.game_id;
    if (qGid) this.selectedGameId = Number(qGid);

    console.log('CtfManagement mounted');
    try {
      this.gameForm = this.getEmptyGameForm();
      this.challengeForm = this.getEmptyChallengeForms();
      this.divisionForm = this.getEmptyDivisionForm();
      this.loadGames().catch(e => console.error('loadGames failed:', e));
    } catch (e) {
      console.error('mounted error:', e);
    }
  }
};
</script>
<style>
.form-hint {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #888;
}
.game-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 20px;
  align-items: center;
  padding: 0 4px 14px;
}
.game-filters .filter-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #555;
}
.game-filters .filter-select {
  width: auto;
  min-width: 120px;
  padding: 4px 8px;
}
.game-filters .filter-meta {
  margin-left: auto;
  font-size: 12px;
  color: #888;
}
.ctf-management {
  padding: var(--fib-21);
}

.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  border-bottom: 2px solid #e0e0e0;
  overflow-x: auto;
}

.tab-btn {
  padding: 10px 20px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  border-bottom: 3px solid transparent;
  transition: all 0.3s;
  white-space: nowrap;
}

.tab-btn.active {
  color: #0066cc;
  border-bottom-color: #0066cc;
}

.tab-btn:hover {
  color: #0066cc;
}

.tab-content {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.card {
  background: var(--gradient-card-bg, var(--card-bg));
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
}

.card-header {
  padding: var(--fib-21);
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--gradient-card-bg, var(--card-bg));
}

.data-table thead {
  background: rgba(20, 30, 38, 0.8);
  font-weight: 600;
}

.data-table th,
.data-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  color: #e5e7eb;
  font-weight: 500;
}
.data-table th {
  color: #9ca3af;
  font-weight: 600;
}

.data-table tbody tr:hover {
  background: #fafafa;
}

.badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  background: #e0e0e0;
  color: #333;
}

.badge-blue { background: #cce5ff; color: #0066cc; }
.badge-green { background: #ccf0dd; color: #00b359; }
.badge-orange { background: #ffd9b3; color: #ff8c00; }
.badge-red { background: #ffcccc; color: #cc0000; }
.badge-yellow { background: #fff4e6; color: #ffaa00; }

.btn-small {
  padding: 6px 12px;
  font-size: 12px;
  margin: 0 2px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  background: #f0f0f0;
  color: #333;
  transition: all 0.2s;
}

.btn-small:hover {
  background: #e0e0e0;
}

.btn-edit { color: #0066cc; }
.btn-edit:hover { background: #e6f2ff; }

.btn-danger { color: #cc0000; }
.btn-danger:hover { background: #ffcccc; }

.btn-info { color: #0066cc; }
.btn-warning { color: #ff8c00; }

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--gradient-card-bg, var(--card-bg));
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.large-modal {
  max-width: 700px;
}

.modal-header {
  padding: var(--fib-21);
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h4 {
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.modal-body {
  padding: var(--fib-21);
}

.form-group {
  margin-bottom: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #333;
}

.form-input,
.form-input input,
.form-input textarea,
.form-input select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
}

.form-input input:focus,
.form-input textarea:focus,
.form-input select:focus {
  outline: none;
  border-color: #0066cc;
  box-shadow: 0 0 0 3px rgba(0,102,204,0.1);
}

.file-upload-box {
  position: relative;
  border: 2px dashed #ddd;
  border-radius: 4px;
  padding: var(--fib-21);
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.file-upload-box:hover {
  border-color: #0066cc;
  background: #f5f9ff;
}

.file-input {
  display: none;
}

.file-label {
  cursor: pointer;
  color: #666;
  display: block;
}

.container-config {
  background: #f9f9f9;
  padding: 16px;
  border-radius: 4px;
  margin: 16px 0;
}

.attachment-section {
  background: #f9f9f9;
  padding: 16px;
  border-radius: 4px;
  margin: 16px 0;
}

.modal-footer {
  padding: var(--fib-21);
  border-top: 1px solid #e0e0e0;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.btn-primary {
  padding: 10px 20px;
  background: #0066cc;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: #0052a3;
}

.btn-secondary {
  padding: 10px 20px;
  background: #f0f0f0;
  color: #333;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.cheat-list {
  padding: var(--fib-21);
}

.cheat-card {
  background: #fff9f0;
  border-left: 4px solid #ff8c00;
  padding: 16px;
  margin-bottom: 16px;
  border-radius: 4px;
}

.cheat-header {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  font-size: 14px;
  flex-wrap: wrap;
  align-items: center;
}

.cheat-id { font-weight: bold; color: #333; }
.cheat-time { color: #999; }

.cheat-type-badge {
  padding: 4px 8px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: bold;
  white-space: nowrap;
}

.cheat-type-badge.type-flag_origin {
  background: #ffcccc;
  color: #990000;
}

.cheat-type-badge.type-similar_flag {
  background: #ffebe6;
  color: #d32f2f;
}

.cheat-type-badge.type-rapid_submission {
  background: #fff9c4;
  color: #f57f17;
}

.cheat-status-badge {
  padding: 4px 8px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: bold;
  white-space: nowrap;
}

.cheat-status-badge.status-pending {
  background: #e3f2fd;
  color: #1976d2;
}

.cheat-status-badge.status-confirmed {
  background: #ffcccc;
  color: #990000;
}

.cheat-status-badge.status-dismissed {
  background: #e0f2f1;
  color: #00695c;
}

.similarity-badge {
  padding: 2px 6px;
  border-radius: 3px;
  background: #ffe6e6;
  color: #cc0000;
  font-weight: bold;
}

.similarity-badge.high {
  background: #ffcccc;
  color: #990000;
}

.user-pair {
  display: flex;
  align-items: stretch;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.user-box {
  flex: 1;
  min-width: 150px;
  padding: 12px;
  background: var(--gradient-card-bg, var(--card-bg));
  border-radius: 4px;
  border-left: 3px solid #0066cc;
}

.user-label {
  display: block;
  font-weight: bold;
  color: #333;
  margin-bottom: 4px;
  font-size: 12px;
}

.user-name {
  display: block;
  color: #333;
  font-weight: 500;
  margin-bottom: 2px;
}

.user-id {
  display: block;
  color: #999;
  font-size: 11px;
}

.vs-mark {
  color: #ff8c00;
  font-weight: bold;
  font-size: 12px;
  padding: 0 4px;
}

.reason-box {
  background: #fff5e6;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 12px;
  font-size: 14px;
}

.reason-box p {
  margin: 6px 0 0 0;
  color: #666;
  white-space: pre-wrap;
  word-break: break-word;
}

.admin-note-box {
  background: #f0f0f0;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 12px;
  font-size: 14px;
  border-left: 3px solid #666;
}

.admin-note-box p {
  margin: 6px 0 0 0;
  color: #666;
  white-space: pre-wrap;
  word-break: break-word;
}

.submission-info {
  background: var(--gradient-card-bg, var(--card-bg));
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 12px;
  font-size: 14px;
}

.submission-info p {
  margin: 6px 0;
}

.cheat-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.game-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
  margin: 0 0 16px;
}
.stat-chip {
  padding: 10px 12px;
  background: #f7f8fa;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-chip span { font-size: 12px; color: #888; }
.stat-chip strong { font-size: 18px; color: #222; }
.scoreboard-container {

  padding: var(--fib-21);
}

.game-divisions-section {
  background: #f9fafb;
  border: 1px solid #e6e6e6;
  border-radius: 6px;
  padding: 12px;
}

.divisions-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.divisions-title {
  font-weight: bold;
  color: #333;
}

.division-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: var(--gradient-card-bg, var(--card-bg));
  border: 1px solid #eee;
  border-radius: 6px;
  margin-bottom: 8px;
  gap: 10px;
  flex-wrap: wrap;
}

.division-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.division-name {
  font-weight: 600;
}

.division-sub {
  font-size: 12px;
  color: #666;
}

.division-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.code-pill {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  background: #eef5ff;
  color: #1a73e8;
  font-weight: 600;
}

.text-muted {
  color: #888;
  font-size: 12px;
}

.podium {
  background: #fff9e6;
  font-weight: bold;
}

.medal {
  display: inline-block;
  font-size: 20px;
  margin-right: 4px;
}

.empty-state {
  padding: 40px;
  text-align: center;
  color: #999;
}

.form-input[placeholder] {
  padding: 8px 10px;
}
.docker-heading {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.docker-heading-ico {
  width: 18px !important;
  height: 18px !important;
  font-size: 18px;
  color: var(--primary);
}
</style>
