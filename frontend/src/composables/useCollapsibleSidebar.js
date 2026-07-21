import { ref, watch } from 'vue'

export function useCollapsibleSidebar(storageKey = 'neepu_sidebar_collapsed') {
  const collapsed = ref(false)

  if (typeof window !== 'undefined') {
    collapsed.value = localStorage.getItem(storageKey) === '1'
  }

  function toggleSidebar() {
    collapsed.value = !collapsed.value
  }

  watch(collapsed, (value) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(storageKey, value ? '1' : '0')
    }
  })

  return { collapsed, toggleSidebar }
}
