# history-cleaner

게시글/댓글 일괄 삭제 도구

## 기능
- 앱 API 삭제 (app.dcinside.com) — 갤로그를 거치지 않아 속도 제한을 피함
- 갤로그로만 지울 수 있는 항목(원글이 삭제된 댓글)은 모아서 마지막에 처리
- 삭제 조건 — 기간, 정규식, 대댓글, 비밀글 (`filter`)
- 대왕콘 받기 — 글 10개·댓글 20개 자동 작성 (`wang`)
- Playwright 가상브라우저 기반 로그인 (JS 보안, 리다이렉트 우회)
- ddddocr 로그인 캡차 로컬 처리
- 2captcha (데스크톱 갤로그 경로)
- 쿠키 자동 저장 (재로그인 생략)
- 중단 후 이어하기, 프록시

## 설치

```bash
pip install -r requirements.txt
playwright install chromium
```

리눅스 서버라면 `playwright install-deps`로 시스템 의존성도 설치

## 실행

```bash
python3 main.py
```

명령어는 `help` 참고

## Credit
[dlcjsdltlq/dcinside-cleaner (v1.2)](https://github.com/dlcjsdltlq/dcinside-cleaner)에서 갈라져 나온 프로젝트
