/**
 * Playwright 自定义 Reporter：测试结束后写出带截图的 HTML 扫描报告。
 */
import { writeHtmlReport, resetScanState } from '../helpers/scan-report.js'

class ScanHtmlReporter {
  onBegin() {
    resetScanState()
  }

  onEnd() {
    const out = writeHtmlReport()
    console.log(`\n[e2e] 扫描 HTML 报告已生成: ${out}\n`)
  }
}

export default ScanHtmlReporter
