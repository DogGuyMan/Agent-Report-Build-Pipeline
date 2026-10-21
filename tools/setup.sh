#!/bin/bash
# 저장소의 파이썬 · npm 의존성을 고정된 판으로 깔고 doctor 로 점검한다. 어느 기계에서나 돈다.
# Graphviz 같은 시스템 도구는 깔지 않는다 — 클라우드는 tools/cloud_env.sh, 로컬은 README 의 "필요한 것".
# 부르는 곳: `npm run setup` · .claude/settings.json 의 SessionStart 훅(클라우드에서만)
set -e
cd "$(dirname "$0")/.."

[ -x .venv/bin/python ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt

# package-lock.json 은 npm 11 이 썼다. npm 10 의 npm ci 는 이것을 EUSAGE 로 거부하므로 판을 고정해 부른다.
# lockfile 이 지난 설치 때와 같으면 건너뛴다.
if ! cmp -s package-lock.json node_modules/.setup-lock.json; then
  npx --yes npm@11.11.0 ci --no-audit --no-fund
  cp package-lock.json node_modules/.setup-lock.json
fi

# test_components 와 CLAUDE.md 의 인용이 .tmp/lib.mjs 를 읽는다. npm test 의 pretest 와 같은 굽기다.
node viz/lib.mjs

# Claude Code 의 SessionStart 훅에서 불렸으면 bin/ 을 그 세션의 PATH 에 남긴다.
# CLAUDE_ENV_FILE 은 세션의 다음 명령부터 들으므로 아래 doctor 를 위해 이 프로세스의 PATH 에도 넣는다.
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo "export PATH=\"$PWD/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
  export PATH="$PWD/bin:$PATH"
fi

python3 tools/doctor.py
