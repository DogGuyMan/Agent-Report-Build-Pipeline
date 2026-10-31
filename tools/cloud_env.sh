#!/bin/bash
# 클라우드 환경의 설정 스크립트 원본. claude.ai/code 환경 설정의 Setup script 칸에 그대로 붙여 넣는다.
# Ubuntu 24.04 에서 root 로, Claude Code 가 뜨기 전에 돈다. 저장소의 의존성은 tools/setup.sh 가 맡는다.
#
# Ubuntu 24.04 apt 의 graphviz 는 -Tsvg_inline 이 없는 판이라 Graphviz 공식 .deb 를 깐다.
# 이 .deb 는 Depends 가 비어 있어 바깥 라이브러리를 따로 깐다 — dot 과 core 플러그인은 expat · ltdl,
# PNG 를 굽는 pango · gd 플러그인은 cairo · pango · gd. apt 의 graphviz 는 함께 깔지 않는다.
# 두 판 모두 libcdt.so.6 이라는 같은 이름의 라이브러리를 갖는다.
set -e
apt-get update
apt-get install -y curl libexpat1 libltdl7 libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgd3
curl -fsSLo /tmp/graphviz.deb \
  https://gitlab.com/api/v4/projects/4207231/packages/generic/graphviz-releases/15.1.1/ubuntu_24.04_graphviz-15.1.1-cmake.deb
echo "02c70b9d42149f5e2ba0e3882643b22904720de50a0a3da84a30b8f32e8a1497  /tmp/graphviz.deb" | sha256sum -c -
apt-get install -y /tmp/graphviz.deb
dot -V
echo 'digraph { a -> b }' | dot -Tsvg_inline > /dev/null
echo 'digraph { a -> b }' | dot -Tpng > /dev/null
