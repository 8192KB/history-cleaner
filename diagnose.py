#!/usr/bin/env python3
"""DCInside 갤로그 접근 진단 스크립트"""
import requests
import urllib3
import re
import json
import os
import sys
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'
HEADERS = {
    'User-Agent': UA,
    'Sec-CH-UA': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    'Sec-CH-UA-Mobile': '?0',
    'Sec-CH-UA-Platform': '"Windows"',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
}

LOG_FILE = 'diag_output.log'

def log(msg, also_print=True):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')
    if also_print:
        print(msg)

def dump_html(label, html_text):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f'\n=== {label} HTML START ===\n')
        f.write(html_text[:5000])
        f.write(f'\n=== {label} HTML END (총 {len(html_text)} bytes) ===\n\n')

def main():
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write('=== DCInside 갤로그 진단 시작 ===\n\n')
    
    session = requests.Session()
    session.verify = False
    session.headers.update(HEADERS)
    
    accounts_file = 'dcinside-cleaner-accounts.json'
    if os.path.exists(accounts_file):
        with open(accounts_file, 'r') as f:
            accounts = json.load(f)
        acc = accounts.get('1', {})
        user_id = acc.get('user_id', '')
        user_pw = acc.get('user_pw', '')
        log(f'[계정] user_id: {user_id}')
    else:
        log('[오류] accounts 파일 없음')
        return

    # STEP 1: 로그인 페이지 GET
    log('\n[STEP 1] 로그인 페이지 GET...')
    try:
        res1 = session.get('https://sign.dcinside.com/login')
        log(f'  Status: {res1.status_code}')
        log(f'  URL: {res1.url}')
        log(f'  Content-Length: {len(res1.text)}')
        dump_html('STEP1_login_page', res1.text)
        
        soup1 = BeautifulSoup(res1.text, 'html.parser')
        login_form = soup1.find('form')
        if login_form:
            inputs = login_form.select('input')
            log(f'  Form 발견! input 개수: {len(inputs)}')
            for inp in inputs:
                name = inp.get('name', '(없음)')
                val = inp.get('value', '')[:30]
                log(f'    - {name} = {val}')
        else:
            log('  !! Form을 찾을 수 없음!')
            inputs = soup1.select('input')
            log(f'  페이지 전체 input 개수: {len(inputs)}')
    except Exception as e:
        log(f'  오류: {e}')
        return

    # STEP 2: 로그인 POST
    log('\n[STEP 2] 로그인 POST...')
    login_data = {}
    form_el = soup1.find('form')
    target_inputs = form_el.select('input') if form_el else soup1.select('input')
    for el in target_inputs:
        name = el.get('name')
        if name:
            login_data[name] = el.get('value', '')
    login_data['user_id'] = user_id
    login_data['pw'] = user_pw
    login_data['checksaveid'] = 'on'
    
    log(f'  전송 필드: {list(login_data.keys())}')
    
    session.headers.update({"Referer": "https://sign.dcinside.com/login"})
    try:
        res2 = session.post('https://sign.dcinside.com/login/member_check', data=login_data)
        log(f'  Status: {res2.status_code}')
        log(f'  Response 길이: {len(res2.text)}')
        log(f'  Response 앞 500자: {res2.text[:500]}')
        dump_html('STEP2_login_response', res2.text)
    except Exception as e:
        log(f'  오류: {e}')
        return

    # STEP 3: 리다이렉트 따라가기
    log('\n[STEP 3] 리다이렉트 처리...')
    redirect_match = re.search(r'location\.replace\("([^"]+)"\)', res2.text)
    if redirect_match:
        redirect_url = redirect_match.group(1)
        log(f'  리다이렉트 URL: {redirect_url}')
        try:
            res3 = session.get(redirect_url)
            log(f'  Status: {res3.status_code}')
            log(f'  Final URL: {res3.url}')
            dump_html('STEP3_redirect', res3.text)
            
            soup3 = BeautifulSoup(res3.text, 'html.parser')
            camp_form = soup3.find('form')
            if camp_form:
                log('  캠페인 폼 발견, 제출 시도...')
                camp_data = {el.get('name'): el.get('value', '') for el in camp_form.select('input') if el.get('name')}
                action = camp_form.get('action', '')
                if action.startswith('/'): action = 'https://sign.dcinside.com' + action
                if not action: action = res3.url
                res3b = session.post(action, data=camp_data)
                log(f'  캠페인 POST Status: {res3b.status_code}')
                dump_html('STEP3b_campaign', res3b.text)
                
                match2 = re.search(r'location\.replace\("([^"]+)"\)', res3b.text)
                if match2:
                    res3c = session.get(match2.group(1))
                    log(f'  2차 리다이렉트 Status: {res3c.status_code}')
            
            match2 = re.search(r'location\.replace\("([^"]+)"\)', res3.text)
            if match2:
                log(f'  2차 리다이렉트 URL: {match2.group(1)}')
                session.get(match2.group(1))
        except Exception as e:
            log(f'  오류: {e}')
    else:
        log('  !! location.replace를 찾을 수 없음 - 로그인 실패 가능성')

    cookies = session.cookies.get_dict()
    for k, v in cookies.items():
        session.cookies.set(k, v, domain='.dcinside.com')
        session.cookies.set(k, v, domain='.gallog.dcinside.com')
        session.cookies.set(k, v, domain='gallog.dcinside.com')

    # STEP 4: 쿠키 확인
    log('\n[STEP 4] 세션 쿠키 확인...')
    all_cookies = session.cookies.get_dict()
    for k, v in all_cookies.items():
        log(f'  {k} = {v[:40]}...' if len(v) > 40 else f'  {k} = {v}')
    
    essential = ['ci_c', 'mc_enc', 'PHPSESSID', 'unicro_id', 'csid']
    for e in essential:
        status = 'OK' if e in all_cookies else 'MISSING'
        log(f'  필수쿠키 {e}: {status}')

    # STEP 5: 갤로그 posting 페이지
    log('\n[STEP 5] 갤로그 posting 페이지 접근...')
    session.headers.update({'User-Agent': UA, 'Referer': 'https://www.dcinside.com/'})
    gallog_url = f'https://gallog.dcinside.com/{user_id}/posting'
    try:
        res5 = session.get(gallog_url)
        log(f'  Status: {res5.status_code}')
        log(f'  URL: {res5.url}')
        log(f'  Content-Length: {len(res5.text)}')
        dump_html('STEP5_gallog_posting', res5.text)
        
        soup5 = BeautifulSoup(res5.text, 'html.parser')
        
        body = soup5.select_one('body')
        log(f'  body 태그: {"있음" if body else "없음 (IP차단?)"}')
        
        gall_elements = soup5.select('div.option_sort.gallog > div > ul > li')
        log(f'  갤러리 드롭다운 (div.option_sort.gallog > div > ul > li): {len(gall_elements)}개')
        for i, el in enumerate(gall_elements[:10]):
            log(f'    [{i}] text="{el.text.strip()}" data-value="{el.get("data-value", "없음")}"')
        
        log('\n  [대안 셀렉터 탐색]')
        alt_selectors = [
            'div.option_sort',
            '.option_sort',
            'select',
            '.gallog',
            '.option_box',
            'ul.option_box',
            '.option_sort ul li',
            '[data-value]',
        ]
        for sel in alt_selectors:
            found = soup5.select(sel)
            if found:
                log(f'    "{sel}" -> {len(found)}개 발견')
                for j, f_el in enumerate(found[:3]):
                    attrs_preview = dict(list(f_el.attrs.items())[:3])
                    log(f'       [{j}] tag={f_el.name} text="{f_el.text.strip()[:50]}" attrs={attrs_preview}')
            else:
                log(f'    "{sel}" -> 0개')
        
        posts = soup5.select('.cont_listbox > li')
        log(f'\n  글 목록 (.cont_listbox > li): {len(posts)}개')
        for i, p in enumerate(posts[:5]):
            log(f'    [{i}] data-no="{p.get("data-no", "없음")}" text="{p.text.strip()[:60]}"')
        
        alt_post_selectors = ['.cont_listbox', '.listbox', 'li[data-no]']
        for sel in alt_post_selectors:
            found = soup5.select(sel)
            if found:
                log(f'    "{sel}" -> {len(found)}개')
        
        sc = soup5.select_one('input[name="service_code"]')
        log(f'\n  service_code: {sc["value"][:30] + "..." if sc else "없음"}')
        
        title = soup5.select_one('title')
        log(f'  페이지 타이틀: {title.text.strip() if title else "없음"}')
        
    except Exception as e:
        log(f'  오류: {e}')
        import traceback
        log(traceback.format_exc())

    # STEP 6: 갤로그 comment 페이지
    log('\n[STEP 6] 갤로그 comment 페이지 접근...')
    try:
        res6 = session.get(f'https://gallog.dcinside.com/{user_id}/comment')
        soup6 = BeautifulSoup(res6.text, 'html.parser')
        log(f'  Status: {res6.status_code}')
        dump_html('STEP6_gallog_comment', res6.text)
        
        gall_elements6 = soup6.select('div.option_sort.gallog > div > ul > li')
        log(f'  갤러리 드롭다운: {len(gall_elements6)}개')
        posts6 = soup6.select('.cont_listbox > li')
        log(f'  댓글 목록: {len(posts6)}개')
    except Exception as e:
        log(f'  오류: {e}')

    log(f'\n=== 진단 완료 ===')
    log(f'상세 HTML 로그: {os.path.abspath(LOG_FILE)}')

if __name__ == '__main__':
    main()
