# history-cleaner

게시글/댓글 일괄 삭제 도구

## 기능
- Playwright 기반 로그인 (JS 보안, 리다이렉트 우회)
- ddddocr 로그인 캡차 로컬 처리
- 2captcha (삭제 시)
- 쿠키 자동 저장 (재로그인 생략)

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

## Credit
[dlcjsdltlq/dcinside-cleaner (v1.2)](https://github.com/dlcjsdltlq/dcinside-cleaner) 기반 포크
