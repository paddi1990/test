import jsons as jsons
import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36',
    'Referer': 'https://domain.oray.com/suffix/xyz.html'
}

if __name__ == '__main__':
    i = 1
    while True:
        domain='%d.xyz' % i
        response = requests.get('https://mcheck.oray.com/domain/check?domain[]=%s&record=1' % domain, headers=headers)
        if response.status_code == 200:
            content = response.content.decode(response.apparent_encoding)
            if content.startswith('{') and content.endswith('}'):
                content = jsons.loads(content)
                if domain in content and 'avail' in content[domain] and content[domain]['avail']==1:
                    print('域名：%s未注册' % domain)
                else:
                    print('域名：%s已注册' % domain)
        else:
            print('error')
        i = i + 1
