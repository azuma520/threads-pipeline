#!/usr/bin/env bash
# anti-template-grep.sh — Step 8 反模板化檢查的機械訊號（不是判死規則）
#
# 用法：bash anti-template-grep.sh <文章路徑>
# Output：列出命中的訊號、給 sense 自審 + user 對齊 reference
# 退出碼：0（永遠 ── 命中不是 fail）；命中數量在 stderr

set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: bash anti-template-grep.sh <article-path>" >&2
  exit 2
fi

ARTICLE="$1"
if [ ! -f "$ARTICLE" ]; then
  echo "Error: file not found: $ARTICLE" >&2
  exit 2
fi

echo "=== anti-template grep signals (not判死、only reference signal) ==="
echo ""

# 條 1：教學語氣字眼
echo "[條 2] 強命令式教學語氣字眼："
grep -nE "你(應該|必須|一定要|需要|可以這樣做|只要|最好|千萬不要)" "$ARTICLE" || echo "  (no hits)"
echo ""

# 條 2：勵志公式字眼
echo "[條 3] 勵志公式字眼："
grep -nE "(正能量|加油|不要放棄|相信自己|你值得|努力就會|終有一天|堅持下去)" "$ARTICLE" || echo "  (no hits)"
echo ""

# 條 3：空泛開頭
echo "[條 1] 空泛開頭句式（前 50 字）："
head -c 200 "$ARTICLE" | grep -nE "^(最近有一些想法|我想分享一件事|關於.+我有一些心得|今天來談談|這陣子一直在想)" || echo "  (no hits)"
echo ""

echo "=== End of signals ==="
echo "提醒：命中只是訊號、需要 sense + 上下文判斷 + user 對齊。grep 不判死。"
