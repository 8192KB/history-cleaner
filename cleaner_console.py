from dcinside_cleaner import Cleaner
from getpass import getpass
from tqdm import tqdm
import traceback
import json
import re
import os
import sys

class Console:
    p_type = {'-p': 'posting', '-c': 'comment'}
    ACCOUNTS_FILE = 'dcinside-cleaner-accounts.json'
    COOKIE_FILE = 'dcinside-cleaner-login.json'

    def __init__(self):
        self.cleaner = Cleaner()
        self.login_flag = False
        self.g_list = {'type':  None}
        self.user_id = ''
        self.user_pw = ''
        
        # Check for cookie file and perform automatic login
        if os.path.exists(self.COOKIE_FILE):
            try:
                with open(self.COOKIE_FILE, 'r', encoding='utf-8') as f:
                    cookie_data = json.load(f)
                    if 'cookies' in cookie_data:
                        print("저장된 쿠키 정보를 사용하여 로그인을 시도합니다...")
                        if self.cleaner.loginFromCookies(cookie_data['cookies']):
                            self.user_id = self.cleaner.getUserId()
                            if self.cleaner.verifyLogin():
                                self.login_flag = True
                                print(f"쿠키 로그인에 성공했습니다! (ID: {self.user_id})")
                            else:
                                self.cleaner.session.cookies.clear()
                                print("쿠키가 만료되었습니다. 다시 로그인해주세요.")
            except Exception as e:
                print(f"쿠키 파일 로드 중 오류 발생: {e}")
                
        if not self.login_flag:
            self.show_account_list()
            print('\n※ "cookie" 명령어로 브라우저 쿠키를 입력하여 로그인하는 것을 권장합니다.')
            print('  (ID/PW 로그인은 디시인사이드 보안 정책으로 차단될 수 있습니다.)\n')
            
        self.getCommand()

    def show_account_list(self):
        if os.path.exists(self.ACCOUNTS_FILE):
            with open(self.ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                accounts = json.load(f)
                if accounts:
                    print('\n[저장된 계정 목록]')
                    for slot in sorted(accounts.keys()):
                        print(f'{slot}: {accounts[slot]["user_id"]}')
                    print('번호(1, 2...)를 입력하여 즉시 로그인할 수 있습니다.\n')
    
    def save_account(self, slot):
        accounts = {}
        if os.path.exists(self.ACCOUNTS_FILE):
            with open(self.ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                accounts = json.load(f)
        accounts[slot] = {
            'user_id': self.cleaner.getUserId(),
            'user_pw': self.user_pw
        }
        with open(self.ACCOUNTS_FILE, 'wt', encoding='utf-8') as f:
            f.write(json.dumps(accounts, indent=4))
        print(f'{slot}번에 계정이 저장되었습니다.')
    
    def save_cookies(self):
        """현재 세션 쿠키를 파일에 저장합니다."""
        try:
            data = {
                'cookies': self.cleaner.getCookies(),
                'user_id': self.cleaner.getUserId()
            }
            with open(self.COOKIE_FILE, 'wt', encoding='utf-8') as f:
                f.write(json.dumps(data))
        except Exception:
            pass
        
    def load_and_login(self, slot):
        if not os.path.exists(self.ACCOUNTS_FILE):
            print('저장된 계정 파일이 없습니다.')
            return False
        with open(self.ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
            accounts = json.load(f)
            if slot not in accounts:
                print(f'{slot}번 계정 정보가 없습니다.')
                return False
            data = accounts[slot]
            print(f'{slot}번 계정({data["user_id"]})으로 로그인을 시도합니다...')
            res = self.cleaner.login(data['user_id'], data['user_pw'])
            if res:
                self.user_pw = data['user_pw']
                self.save_account(slot)
                print('ID/PW를 사용하여 로그인되었습니다.')
                return True
            print('로그인에 실패하였습니다. 비밀번호가 변경되었는지 확인해주세요.')
            return False

    def parseAndExecute(self, cmd_input : str) -> int:
        cmd = cmd_input.split()
        if not cmd: return 0

        if cmd[0] == 'help':
            print('1, 2, ... - 저장된 번호로 즉시 로그인합니다.')
            print('login - 수동으로 로그인합니다. (비밀번호 변경 캠페인, JS 로그인 시 실패 가능)')
            print('cookie - 브라우저 쿠키를 직접 입력하여 로그인합니다. (강력 권장)')
            print('export [번호] - 현재 로그인 정보를 해당 번호에 저장합니다. (예: export 1)')
            print('p - 작성한 글 리스트를 가져옵니다.')
            print('c - 작성한 댓글 리스트를 가져옵니다.')
            print('getglist -p, -c로도 사용 가능')
            print('del all | 1 2 3 4 ... | 1 ~ 4 - 선택한 갤러리에 대해 삭제를 수행합니다.')
            print('proxy load [파일명] - 프록시 리스트(txt)를 불러옵니다.')
            print('proxy off - 프록시 사용을 중지합니다.')
            print('2captcha [api_key] - 2captcha API 키를 설정합니다.')
            print('logout - 로그아웃합니다.')
            print('help - 도움말을 봅니다.')
            print('exit - 종료합니다.')
            return 0
        if cmd[0] == 'exit': return 0

        if cmd[0] == 'proxy':
            if len(cmd) > 1 and cmd[1] == 'load':
                filename = cmd[2] if len(cmd) > 2 else 'proxies.txt'
                if os.path.exists(filename):
                    with open(filename, 'r', encoding='utf-8') as f:
                        raw_proxies = [line.strip() for line in f if line.strip()]
                    
                    print(f'[{filename}]에서 {len(raw_proxies)}개의 프록시를 읽었습니다.')
                    print('현재 작동하는 프록시를 검사 중입니다... (최대 3초 소요)')
                    
                    import concurrent.futures
                    import requests
                    
                    valid_proxies = []
                    
                    def check_proxy(p):
                        try:
                            # proxy format handling
                            proxy_dict = {'http': p, 'https': p} if '://' in p else {'http': f'http://{p}', 'https': f'http://{p}'}
                            # check connection to dcinside with a strict 2-second timeout
                            requests.get('https://www.dcinside.com/', proxies=proxy_dict, timeout=2)
                            return p
                        except:
                            return None

                    # Use multithreading to check dozens of proxies simultaneously
                    from tqdm import tqdm
                    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
                        results = list(tqdm(executor.map(check_proxy, raw_proxies), total=len(raw_proxies), desc="프록시 테스트"))
                        
                    valid_proxies = [r for r in results if r]
                    
                    self.cleaner.setProxyList(valid_proxies)
                    if valid_proxies:
                        print(f'검사 완료! 정상 작동하는 프록시 {len(valid_proxies)}개를 추려내어 적용했습니다.')
                    else:
                        print('검사 완료. 작동하는 프록시가 하나도 없습니다. 다른 프록시 목록을 구해보세요.')
                else:
                    print(f'{filename} 파일을 찾을 수 없습니다.')
            elif len(cmd) > 1 and cmd[1] == 'off':
                self.cleaner.setProxyList([])
                print('프록시 사용이 중지되었습니다.')
            else:
                print('사용법: proxy load [파일명] | proxy off')
            return 0

        if cmd[0] == '2captcha':
            if len(cmd) > 1:
                if self.cleaner.set2CaptchaKey(cmd[1]):
                    print('2captcha API 키가 정상적으로 설정되었습니다.')
                else:
                    print('2captcha API 키가 올바르지 않거나 잔액이 부족합니다.')
            else:
                print('사용법: 2captcha [api_key]')
            return 0

        if not self.login_flag and cmd[0].isdigit():
            if self.load_and_login(cmd[0]):
                self.login_flag = True
            return 0

        if self.login_flag and cmd[0].isdigit() and len(cmd) == 1:
            if self.g_list.get('type'):
                print(f'{cmd[0]}번 갤러리 삭제를 시도합니다...')
                self.delete(self.g_list[int(cmd[0])], self.g_list['type'])
            else:
                print('먼저 리스트를 불러와주세요. (p 또는 c)')
            return 0

        elif cmd[0] == 'login':
            if self.login_flag:
                print('이미 로그인되었습니다.')
                return 0
            
            self.user_id = input('ID >> ')
            self.user_pw = getpass('PW >> ')
            res = self.cleaner.login(self.user_id, self.user_pw)
            if res:
                print('로그인되었습니다! (캡차 자동 풀기 포함)')
                print('※ 갤로그에서 글 목록이 안 보이면 "cookie" 명령어로 재시도하세요.')
                self.login_flag = True
                self.save_cookies()
            else:
                print('로그인에 실패하였습니다.')
                print('원인: 캡차 인식 실패 / 보안 정책 차단 / ID·PW 오류')
                print('대신 "cookie" 명령어를 사용하여 브라우저 쿠키로 로그인해보세요.')
                return 0

        elif cmd[0] == 'cookie':
            if self.login_flag:
                print('이미 로그인되었습니다.')
                return 0
            
            self.user_id = input('갤로그 ID (비워두면 쿠키에서 자동 추출 시도) >> ').strip()
            print('브라우저 F12 -> Network -> 아무 요청 클릭 -> Request Headers 내의 Cookie 문자열을 붙여넣으세요.')
            raw_cookie = input('Cookie >> ')
            
            import http.cookies
            parsed_cookies = {}
            try:
                simple_cookie = http.cookies.SimpleCookie()
                simple_cookie.load(raw_cookie)
                for key, morsel in simple_cookie.items():
                    parsed_cookies[key] = morsel.value
            except Exception as e:
                print(f'쿠키 파싱 실패: {e}')
                return 0
                
            res = self.cleaner.loginFromCookies(parsed_cookies)
            if self.user_id:
                self.cleaner.user_id = self.user_id
            else:
                self.user_id = self.cleaner.user_id
                
            if res or self.cleaner.verifyLogin():
                print(f'쿠키 로그인 성공! (ID: {self.user_id})')
                self.login_flag = True
                self.save_cookies()
                print('쿠키가 자동 저장되었습니다. 다음 실행 시 자동 로그인됩니다.')
            else:
                print('쿠키 로그인 상태가 유효하지 않습니다. (올바른 쿠키인지 확인하세요)')
                return 0

        elif cmd[0] == 'export':
            if not self.login_flag:
                print('로그인해 주십시오.')
                return 0
            slot = cmd[1] if len(cmd) > 1 else '1'
            self.save_account(slot)

        elif not self.login_flag: 
            print('로그인해 주십시오. (또는 저장된 번호 입력)')
            return 0

        elif cmd[0] in ['p', 'c', 'getglist']:
            if cmd[0] == 'p': 
                post_type = 'posting'
            elif cmd[0] == 'c': 
                post_type = 'comment'
            else:
                if len(cmd) < 2 or cmd[1] not in self.p_type:
                    print('옵션을 입력하십시오. (p: 글, c: 댓글)')
                    return 0
                post_type = self.p_type[cmd[1]]

            g_list = self.cleaner.getGallList(post_type)
            
            if g_list == 'BLOCKED':
                print('IP 차단이 감지되었습니다.')
                return 0
            if not g_list:
                print('갤러리 리스트가 없습니다.')
                return 0

            self.g_list = {'type': post_type}
            idx = 1
            for k, v in g_list.items():
                self.g_list[idx] = k
                print(f'{idx}. {v}')
                idx += 1

        elif cmd[0] == 'del':
            if self.g_list.get('type') == None:
                print('갤러리 리스트를 선택하지 않았습니다.')
                return 0
            del_list = []
            if len(cmd) < 2:
                print('삭제할 번호를 입력하십시오.')
                return 0
            if cmd[1] == 'all':
                del_list = [str(k) for k in self.g_list.keys() if isinstance(k, int)]
            elif '~' in cmd_input:
                regex = re.compile(r'(\d+)~(\d+)')
                numbers = regex.findall(cmd_input)
                for number in numbers:
                    a, b = map(int, number)
                    del_list += [str(i) for i in range(a, b+1)]
            else:
                del_list = cmd[1:]
            
            del_list = sorted(list(set(del_list)))
            for del_no in del_list:
                if del_no.isdigit() and int(del_no) in self.g_list:
                    self.delete(self.g_list[int(del_no)], self.g_list['type'])

        elif cmd[0] == 'logout':
            self.login_flag = False
            self.user_id = ''
            self.user_pw = ''
            print('로그아웃되었습니다.')

    def delete(self, gno, post_type):
        print('글 목록 가져오는 중... (취소: Ctrl+C)')
        try:
            page_count = self.cleaner.getPageCount(gno, post_type)
            if page_count == 'ipblocked':
                print('IP 차단이 감지되었습니다.')
                return
            with tqdm(total=page_count) as pbar:
                for i in self.cleaner.aggregatePosts(gno, post_type):
                    if i == 'ipblocked': 
                        print('IP 차단이 감지되었습니다.')
                        return
                    pbar.update(1)
        except KeyboardInterrupt:
            print('\n작업이 취소되었습니다.')
            return

        print('글 지우는 중... (일시정지: Ctrl+C)')
        try:
            with tqdm(total=len(self.cleaner.post_list)) as pbar:
                generator = self.cleaner.deletePosts(post_type)
                while True:
                    try:
                        i = next(generator)
                        if i == 'ipblocked': 
                            print('IP 차단이 감지되었습니다.')
                            return
                        if i == 'captcha':
                            print('reCAPTCHA Detected!')
                            input('캡차를 해제한 후 엔터키를 눌러주십시오.')
                        pbar.update(1)
                    except StopIteration:
                        break
                    except KeyboardInterrupt:
                        print('\n[일시정지] 계속 진행하시겠습니까? (y/n)')
                        ans = input('>> ').strip().lower()
                        if ans != 'y':
                            print('삭제가 취소되었습니다.')
                            return
                        print('이어서 삭제를 진행합니다...')
        except KeyboardInterrupt:
            print('\n삭제가 취소되었습니다.')
            return
        print('\n삭제 완료.')

    def getCommand(self):
        print('dcinside cleaner')
        print('사용법은 help를 입력하세요.')
        while True:
            try:
                cmd = input('>> ')
                if cmd == 'exit':
                    break
                self.parseAndExecute(cmd)
            except KeyboardInterrupt:
                break
            except Exception:
                traceback.print_exc()
                print('문제가 발생하였습니다.')
