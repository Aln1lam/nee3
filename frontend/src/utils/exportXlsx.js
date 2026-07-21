/**
 * 轻量 SpreadsheetML 导出，Excel / WPS 可直接打开，无需额外依赖
 */
function escapeXml(v) {
  return String(v ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

export function exportXlsx(rows, filename = 'export.xlsx', sheetName = 'Sheet1') {
  const safeName = sheetName.replace(/[^\w\u4e00-\u9fff-]/g, '_').slice(0, 31) || 'Sheet1'
  const rowsXml = (rows || []).map(row =>
    `<Row>${row.map(c => `<Cell><Data ss:Type="String">${escapeXml(c)}</Data></Cell>`).join('')}</Row>`,
  ).join('')

  const xml = `<?xml version="1.0"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
<Worksheet ss:Name="${escapeXml(safeName)}">
<Table>${rowsXml}</Table>
</Worksheet>
</Workbook>`

  const blob = new Blob([`\ufeff${xml}`], { type: 'application/vnd.ms-excel;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename.endsWith('.xlsx') ? filename : `${filename}.xlsx`
  a.click()
  URL.revokeObjectURL(a.href)
}
