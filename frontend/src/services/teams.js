/**
 * 队伍 API — 与 /api/teams/* 对齐
 */
import http from './http'

export async function getMyTeam(gameId) {
  const { data } = await http.get('/api/teams/me', {
    params: gameId != null ? { game_id: gameId } : {},
  })
  return data
}

export async function listTeams(gameId) {
  const { data } = await http.get('/api/teams/', {
    params: gameId != null ? { game_id: gameId } : {},
  })
  return data
}

export async function createTeam(payload) {
  const { data } = await http.post('/api/teams/', payload)
  return data
}

export async function joinTeam(payload) {
  const { data } = await http.post('/api/teams/join', payload)
  return data
}

export async function updateTeam(teamId, payload) {
  const { data } = await http.patch(`/api/teams/${teamId}`, payload)
  return data
}

export async function leaveTeam(teamId) {
  const { data } = await http.post(`/api/teams/${teamId}/leave`)
  return data
}

export async function getTeamSolves(teamId, gameId) {
  const { data } = await http.get(`/api/teams/${teamId}/solves`, {
    params: gameId != null ? { game_id: gameId } : {},
  })
  return data
}

export default {
  getMyTeam,
  listTeams,
  createTeam,
  joinTeam,
  updateTeam,
  leaveTeam,
  getTeamSolves,
}
