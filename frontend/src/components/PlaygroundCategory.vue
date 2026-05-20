<template>
  <div class="category-page">
    <n-card>
      <template #header>
        <div class="card-title">{{ title }}</div>
      </template>
      <div class="cat-desc">{{ desc }}</div>
      <div class="cat-actions" style="margin-top:12px">
        <n-button v-for="entry in examples" :key="entry.id" size="small" @click="openExample(entry)">
          {{ entry.title }}
        </n-button>
      </div>
    </n-card>
  </div>
</template>

<script>
import { useRoute, useRouter } from 'vue-router'
import { ref } from 'vue'
export default {
  name: 'PlaygroundCategory',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const slug = route.params.slug || ''
    const meta = {
      web: { title: 'Web 渗透', desc: 'Web 漏洞练习与实战靶场', examples: [{id:1,title:'XSS 实验'}, {id:2,title:'SQLi 实验'}] },
      pwn: { title: '二进制 / Pwn', desc: '二进制漏洞与利用训练', examples: [{id:1,title:'堆练习'}, {id:2,title:'ROP 实验'}] },
      forensics: { title: '电子取证', desc: '取证、日志分析与文件恢复', examples: [{id:1,title:'磁盘取证'}, {id:2,title:'日志分析'}] },
      crypto: { title: '密码学', desc: '密码学小题与挑战', examples: [{id:1,title:'对称加密'}, {id:2,title:'RSA 实验'}] },
      ctf: { title: 'CTF 模拟赛', desc: '完整 CTF 比赛环境', examples: [{id:1,title:'练习赛'}, {id:2,title:'模拟赛'}] }
    }

    const info = meta[slug] || { title: '靶场', desc: '请选择一个练习方向', examples: [] }
    const title = ref(info.title)
    const desc = ref(info.desc)
    const examples = ref(info.examples)

    function openExample(e) {
      // 简易行为：跳转到 /games（或你们的题库）并可带上查询参数
      router.push({ path: '/games', query: { playground: slug, example: e.id } })
    }

    return { title, desc, examples, openExample }
  }
}
</script>

<style scoped>
.category-page { padding: 18px }
.card-title { font-weight: 700 }
.cat-desc { color: #666; margin-top: 8px }
</style>
