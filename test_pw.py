import asyncio
from playwright.async_api import async_playwright
import ddddocr

async def test_login():
    ocr = ddddocr.DdddOcr(show_ad=False)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'
        )
        
        # Block campaign page so cookies don't get destroyed
        await context.route("**/*campaign/password_change*", lambda route: route.abort())
        
        page = await context.new_page()
        
        print("로그인 페이지 이동 중...")
        await page.goto("https://sign.dcinside.com/login")
        
        await page.fill("#id", "minatoo")
        await page.fill("#pw", "alsrb1582%")
        
        # Check if CAPTCHA is visible
        captcha_visible = await page.is_visible("#kcaptcha_code")
        if captcha_visible:
            print("캡차 발견, 풀기 시도...")
            # We need to wait for captcha to fully load
            await page.wait_for_timeout(500)
            captcha_img = await page.locator("#kcaptcha").screenshot()
            
            captcha_text = ocr.classification(captcha_img).lower()
            print(f"인식된 캡차: {captcha_text}")
            await page.fill("#kcaptcha_code", captcha_text)
            
        print("로그인 버튼 클릭...")
        try:
            async with page.expect_navigation(timeout=5000):
                await page.click(".btn_blue.small.btn_wfull")
        except Exception:
            print("네비게이션 실패 (또는 타임아웃), 대기 중...")
        
        await page.wait_for_timeout(2000)
        print(f"현재 URL: {page.url}")
        
        print("갤로그 확인 중...")
        await page.goto("https://gallog.dcinside.com/minatoo/posting")
        
        login_btn = await page.query_selector(".btn_top_loginout")
        btn_text = await login_btn.inner_text() if login_btn else "없음"
        print(f"갤로그 로그인 버튼 텍스트: {btn_text.strip()}")
        
        if btn_text.strip() == "로그아웃":
            print("🎉 플레이라이트 로그인 성공!")
            cookies = await context.cookies()
            print(f"추출된 쿠키 수: {len(cookies)}")
            for c in cookies:
                print(f"  {c['name']} : {c['domain']}")
        else:
            print("❌ 로그인 실패 (비인증 상태)")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_login())
