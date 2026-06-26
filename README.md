# Community History Cleaner

게시글 및 댓글 등 커뮤니티 활동 내역을 손쉽게 정리하고 관리할 수 있도록 돕는 유틸리티입니다.

## 🚀 주요 기능
- **Playwright 가상 브라우저 적용:** 복잡한 자바스크립트 보안이나 리다이렉트를 우회하여 안정적인 로그인을 지원합니다.
- **로컬 AI 캡차 자동 해독 (ddddocr):** N100 등의 저사양 CPU에서도 빠르게 4자리 영숫자 캡차를 자체적으로 인식하고 통과합니다. 유료 API가 필요 없습니다.
- **로컬 쿠키 자동 저장:** 한 번 로그인하면 세션 쿠키를 `.json` 형태로 로컬에 보관하여 다음 번 실행 시 번거로운 로그인 과정을 건너뜁니다.
- **백그라운드 자동화 지원:** 서버 환경에서 장시간 구동하기 적합하도록 설계되었습니다.

## 📦 설치 방법

### 1. 파이썬 환경 설정
Python 3.8 이상을 권장합니다.

```bash
# 필수 라이브러리 설치
pip install -r requirements.txt
pip install playwright ddddocr

# Playwright 가상 브라우저 엔진(크로미움) 설치
playwright install chromium
```
*(참고: 리눅스 서버 등에서는 브라우저 구동을 위해 추가 시스템 패키지 설치가 필요할 수 있습니다. `playwright install-deps`를 활용하세요)*

### 2. 사용 방법
```bash
python3 main.py
```
프롬프트가 나타나면 아이디와 비밀번호를 입력하거나 저장된 계정을 선택하여 로그인을 진행할 수 있습니다. 캡차가 발생하면 프로그램이 백그라운드에서 이미지를 캡처한 뒤 ddddocr로 자동 해독하여 로그인을 완료합니다.

---

## 📜 Credit
본 프로젝트는 [dlcjsdltlq 님의 dcinside-cleaner (v1.2)](https://github.com/dlcjsdltlq/dcinside-cleaner)의 핵심 로직에서 깊은 영감을 받아 작성되었습니다. 기존 1.2 버전의 뛰어난 인터페이스와 설계 구조를 바탕으로, 최신 사이트 보안 정책(JS 난독화, 캠페인 리다이렉트 등)을 우회할 수 있는 Playwright 및 무료 로컬 캡차 인식 기능을 더하여 개선한 버전입니다. 원작자분께 진심으로 감사드립니다.
