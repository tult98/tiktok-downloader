import requests
import sys
import random
import string
import os, os.path
import time
import colorama
from colorama import Fore
sys.path.append("./libs/")

from bs4 import BeautifulSoup

headers = {
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0',
}

tikTokDomains = (
    'http://vt.tiktok.com', 'http://app-va.tiktokv.com', 'http://vm.tiktok.com', 'http://m.tiktok.com', 'http://tiktok.com', 'http://www.tiktok.com', 'http://link.e.tiktok.com', 'http://us.tiktok.com',
    'https://vt.tiktok.com', 'https://app-va.tiktokv.com', 'https://vm.tiktok.com', 'https://m.tiktok.com', 'https://tiktok.com', 'https://www.tiktok.com', 'https://link.e.tiktok.com', 'https://us.tiktok.com'
)

def getToken(url):
    try:
        response = requests.post('https://musicaldown.com/', headers=headers)
        
        cookies = response.cookies
        soup = BeautifulSoup(response.content, 'html.parser').find_all('input')

        data = {
            soup[0].get('name'):url,
            soup[1].get('name'):soup[1].get('value'),
            soup[2].get('name'):soup[2].get('value')
        }
        
        return True, cookies, data
    
    except Exception:
        return None, None, None

def getVideo(url):
    if not url.startswith('http'):
        url = 'https://' + url

    if url.lower().startswith(tikTokDomains):
        url = url.split('?')[0]
        
        status, cookies, data = getToken(url)

        if status:
            headers = {
                'Cookie': f"session_data={cookies['session_data']}",
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': '96',
                'Origin': 'https://musicaldown.com',
                'Referer': 'https://musicaldown.com/en/',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Te': 'trailers'
            }

            try:
                response = requests.post('https://musicaldown.com/download', data=data, headers=headers, allow_redirects=False)

                if 'location' in response.headers:
                    if response.headers['location'] == '/en/?err=url invalid!':
                        return {
                            'success': False,
                            'error': 'invalidUrl'
                        }

                    elif response.headers['location'] == '/en/?err=Video is private!':
                        return {
                            'success': False,
                            'error': 'privateVideo'
                        }

                    elif response.headers['location'] == '/mp3/download':
                        response = requests.post('https://musicaldown.com//mp3/download', data=data, headers=headers)
                        soup = BeautifulSoup(response.content, 'html.parser')

                        return {
                            'success': True,
                            'type': 'audio',
                            'description': soup.findAll('h2', attrs={'class':'white-text'})[0].get_text()[13:],
                            'thumbnail': None,
                            'link': soup.findAll('a',attrs={'class':'btn waves-effect waves-light orange'})[3]['href'],
                            'url': url
                        }

                    else:
                        return {
                            'success': False,
                            'error': 'unknownError'
                        }

                else:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    return {
                        'success': True,
                        'type': 'video',
                        'description': soup.findAll('h2', attrs={'class':'white-text'})[0].get_text()[23:-19],
                        'thumbnail': soup.findAll('img',attrs={'class':'responsive-img'})[0]['src'],
                        'link': soup.findAll('a',attrs={'class':'btn waves-effect waves-light orange'})[3]['href'],
                        'url': url
                    }

            except Exception as error:
                raise Exception("Fail to get the download's URL.")
        
        else:
            raise Exception("Fail to get download's token.")

    else:
        raise ValueError("Invalid TikTok's URL.")

def safe_open_w(path, operator = "wb"):
    ''' Open "path" for writing, creating any parent directories as needed.
    '''
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return open(path, operator)

def download_video(link, file_name): 
    try: 
        r = requests.get(link, stream = True, headers=headers) 
        if(not r.ok):
            raise Exception(f"{r.status_code} {r.reason}.")
        else:
            with safe_open_w(f"./output/{file_name}") as f:
                for chunk in r.iter_content(chunk_size = 1024*1024): 
                    if chunk: 
                        f.write(chunk)
                f.close() 
    except requests.exceptions.RequestException as error:
        raise Exception('Connection error.')

def handle_input_data(input_data):
    line_num, line = input_data
    input_arr = line.split('\t')
    if (len(input_arr) != 3):
        raise ValueError('Invalid input. The input format is: <vide_name> <video_url> <folder_name> (separate by tab)')
    formatted_input = []
    for input in input_arr:
        formatted_input.append(input.strip())
    
    return formatted_input

def main():
    timestr = time.strftime("%Y%m%d-%H%M%S")
    file = open("./input.txt", "r")
    log_file = safe_open_w(f"./logs/{timestr}.txt", "a")

    for line_data in enumerate(file):
        line_num, _ = line_data
        try:
            formatted_input = handle_input_data(line_data)
            video_name, video_url, folder_name = formatted_input
            url = getVideo(video_url)
            download_video(url["link"], f"{folder_name}/{video_name}.mp4")
            log_file.write(f"Line {line_num + 1}: {video_name} is downloaded.\n")
            print(Fore.GREEN + f"Line {line_num + 1}: {video_name} is downloaded.")
        except ValueError as error:
            log_file.write(f"Line {line_num + 1}: {error}.\n")
            print(Fore.RED + f"Line {line_num + 1}: {error}.")
            continue
        except Exception as error:
            log_file.write(f"Line {line_num + 1}: Downloading {video_name} is failed. {error}.\n")
            print(Fore.RED + f"Line {line_num + 1}: Downloading {video_name} is failed. {error}.")
            continue
    
    log_file.close()

if __name__ == "__main__":
    main()