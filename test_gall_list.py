import requests
from bs4 import BeautifulSoup
import urllib3
import re
import http.cookies
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

user_id = "minatoo"
user_pw = "alsrb1582%"

common_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'

session = requests.Session()
session.verify = False
session.headers.update({'User-Agent': common_user_agent})

def force_cookies(session, response):
    raw_headers = response.raw.headers
    headers = []
    if hasattr(raw_headers, 'getlist'):
        headers = raw_headers.getlist('set-cookie') or raw_headers.getlist('Set-Cookie')
    else:
        headers = response.headers.get('Set-Cookie', [])
        if isinstance(headers, str):
            headers = [headers]
        elif headers is None:
            headers = []
            
    print("\n--- Manually Parsing Set-Cookie Headers ---")
    for header in headers:
        cookie = http.cookies.SimpleCookie()
        try:
            cookie.load(header)
        except Exception as e:
            print(f"Error parsing header: {e}")
            continue
            
        for key, morsel in cookie.items():
            domain = morsel['domain'] or '.dcinside.com'
            path = morsel['path'] or '/'
            val = morsel.value
            
            if morsel['expires'] == '0':
                morsel['expires'] = ''
                
            print(f"Forcing Cookie: {key}={val[:20]}... (Domain: {domain}, Path: {path})")
            session.cookies.set(key, val, domain=domain, path=path)

print("1. Fetching login form...")
res_form = session.get('https://sign.dcinside.com/login')
soup_form = BeautifulSoup(res_form.text, 'html.parser')
login_form = soup_form.find('form')
input_elements = login_form.select('input') if login_form else soup_form.select('input')
form = {el.get('name'): el.get('value', '') for el in input_elements if el.get('name')}
form['user_id'] = user_id
form['pw'] = user_pw
# Override s_url to mobile dcinside
form['s_url'] = 'https://m.dcinside.com/'

print("2. Submitting login credentials with mobile s_url...")
session.headers.update({
    "Referer": "https://sign.dcinside.com/login",
    'User-Agent': common_user_agent
})
res_post = session.post('https://sign.dcinside.com/login/member_check', data=form)
print(f"Login Response Text: {res_post.text}")

force_cookies(session, res_post)

# Extract redirect url and follow it
redirect_match = re.search(r'location\.replace\("([^"]+)"\)', res_post.text)
if redirect_match:
    redirect_url = redirect_match.group(1)
    print(f"\n3. Following JS redirect to: {redirect_url}")
    session.headers.update({
        "Referer": "https://sign.dcinside.com/login/member_check",
        'User-Agent': common_user_agent
    })
    res_redirect = session.get(redirect_url)
    print(f"Redirect URL status code: {res_redirect.status_code}")
    print(f"Redirect final URL: {res_redirect.url}")
    force_cookies(session, res_redirect)
else:
    print("\n[Warning] No redirection script found!")

print("\n--- Session Cookies after Mobile SSO ---")
for cookie in session.cookies:
    print(f"Name: {cookie.name}, Domain: {cookie.domain}, Value: {cookie.value[:25]}...")


# Now fetch Minor Gallery posting page and check
minor_url = f'https://gallog.dcinside.com/{user_id}/posting/minor'
print(f"\n4. Fetching Minor Gallery posting page: {minor_url}")
session.headers.update({
    "Referer": "https://www.dcinside.com/",
    'User-Agent': common_user_agent
})
res_minor = session.get(minor_url)
print(f"Minor Gallog Status Code: {res_minor.status_code}")
soup_minor = BeautifulSoup(res_minor.text, 'html.parser')

minor_posts = soup_minor.select('.cont_listbox > li')
print(f"Number of minor gallery posts on page 1: {len(minor_posts)}")
minor_galls = soup_minor.select('div.option_sort.gallog > div > ul > li')
print(f"Minor Gallery dropdown size: {len(minor_galls)}")
for idx, el in enumerate(minor_galls):
    print(f"  - {idx}: {el.text.strip()} (value: {el.get('data-value')})")

# Now fetch Comment page and check
comment_url = f'https://gallog.dcinside.com/{user_id}/comment'
print(f"\n5. Fetching Comment page: {comment_url}")
res_comment = session.get(comment_url)
print(f"Comment Status Code: {res_comment.status_code}")
soup_comment = BeautifulSoup(res_comment.text, 'html.parser')

comments = soup_comment.select('.cont_listbox > li')
print(f"Number of comments on page 1: {len(comments)}")
comment_galls = soup_comment.select('div.option_sort.gallog > div > ul > li')
print(f"Comment Gallery dropdown size: {len(comment_galls)}")
for idx, el in enumerate(comment_galls):
    print(f"  - {idx}: {el.text.strip()} (value: {el.get('data-value')})")
