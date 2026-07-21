import { spawnSync } from 'child_process'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const REPO_ROOT = path.resolve(__dirname, '..', '..')
const SCRIPT = path.join(__dirname, 'provision_user.py')

/**
 * 创建并验证一个 E2E 账号（默认提权管理员，以便扫完拓扑 §2.5）。
 * @param {{ admin?: boolean, prefix?: string }} [opts]
 */
export function provisionE2EUser(opts = {}) {
  const args = [SCRIPT]
  if (opts.admin !== false) args.push('--admin')
  if (opts.prefix) args.push('--prefix', opts.prefix)

  const r = spawnSync('python', args, {
    cwd: REPO_ROOT,
    encoding: 'utf8',
    env: process.env,
    timeout: 60_000,
  })

  const stdout = (r.stdout || '').trim()
  const stderr = (r.stderr || '').trim()
  let data
  try {
    // 取最后一行 JSON（前面可能有 Flask 日志）
    const lines = stdout.split(/\r?\n/).filter(Boolean)
    const jsonLine = [...lines].reverse().find((l) => l.startsWith('{'))
    data = JSON.parse(jsonLine || stdout)
  } catch {
    throw new Error(
      `provision_user 解析失败\nexit=${r.status}\nstdout=${stdout}\nstderr=${stderr}`,
    )
  }

  if (!data?.ok) {
    throw new Error(`provision_user 失败: ${data?.error || stdout || stderr}`)
  }

  // 注入给 tryLogin 使用
  process.env.E2E_USER = data.account
  process.env.E2E_PASSWORD = data.password
  process.env.E2E_EMAIL = data.email

  return data
}
