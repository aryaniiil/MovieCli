import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import sys
import re
from urllib.parse import quote


class TMDBSearcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })

    def search(self, query, max_results=8):
        try:
            search_query = f"{query} tmdb"
            results = self._search_duckduckgo(search_query, max_results)
            if not results:
                results = self._search_direct(query, max_results)
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def _search_duckduckgo(self, query, max_results):
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
            response = self.session.get(url, timeout=10)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            for result in soup.find_all('a', class_='result__a'):
                href = result.get('href', '')
                if 'uddg=' in href:
                    actual_url = href.split('uddg=')[1].split('&')[0]
                    from urllib.parse import unquote
                    actual_url = unquote(actual_url)
                else:
                    actual_url = href
                
                tmdb_match = re.search(r'themoviedb\.org/(movie|tv)/(\d+)', actual_url)
                if tmdb_match:
                    content_type = tmdb_match.group(1)
                    tmdb_id = int(tmdb_match.group(2))
                    
                    title = result.get_text(strip=True)
                    title = re.sub(r'\s*[-—]\s*The Movie Database.*', '', title, flags=re.IGNORECASE)
                    title = re.sub(r'\s*\|\s*TMDB.*', '', title, flags=re.IGNORECASE)
                    
                    year = ''
                    year_match = re.search(r'\((\d{4})\)', title)
                    if year_match:
                        year = year_match.group(1)
                        title = re.sub(r'\s*\(\d{4}\)', '', title).strip()
                    
                    results.append({
                        'type': content_type,
                        'id': tmdb_id,
                        'title': title,
                        'year': year,
                        'similarity': 1.0 - (len(results) * 0.1),
                        'popularity': 100 - len(results) * 10
                    })
                    
                    if len(results) >= max_results:
                        break
            return results
        except Exception as e:
            print(f"DuckDuckGo search failed: {e}")
            return []

    def _search_direct(self, query, max_results):
        try:
            search_url = f"https://www.themoviedb.org/search?query={quote(query)}"
            response = self.session.get(search_url, timeout=10)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            cards = soup.find_all('div', class_='card')
            
            for card in cards[:max_results]:
                try:
                    link = card.find('a', class_='result')
                    if not link:
                        continue
                    
                    href = link.get('href', '')
                    match = re.search(r'/(movie|tv)/(\d+)', href)
                    if not match:
                        continue
                    
                    content_type = match.group(1)
                    tmdb_id = int(match.group(2))
                    
                    title_elem = card.find('h2')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    
                    year = ''
                    year_elem = card.find('span', class_='release_date')
                    if year_elem:
                        year_match = re.search(r'\d{4}', year_elem.get_text())
                        if year_match:
                            year = year_match.group(0)
                    
                    results.append({
                        'type': content_type,
                        'id': tmdb_id,
                        'title': title,
                        'year': year,
                        'similarity': 1.0 - (len(results) * 0.1),
                        'popularity': 100 - len(results) * 10
                    })
                except Exception:
                    continue
            return results
        except Exception as e:
            print(f"Direct TMDB search failed: {e}")
            return []


class VidlinkCapture:
    def __init__(self, brave_path=None, headless=True):
        if brave_path is None:
            import platform
            system = platform.system()
            if system == "Windows":
                brave_path = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
            elif system == "Darwin":
                brave_path = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
            else:
                brave_path = "/usr/bin/brave-browser"
        
        self.brave_path = brave_path
        self.headless = headless

    def get_m3u8_url(self, tmdb_id, content_type, season=1, episode=1, wait_time=10):
        if content_type == 'movie':
            url = f"https://vidlink.pro/movie/{tmdb_id}"
        else:
            url = f"https://vidlink.pro/tv/{tmdb_id}/{season}/{episode}"
        
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        import json
        import time
        
        options = Options()
        options.binary_location = self.brave_path
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        if self.headless:
            options.add_argument('--headless=new')
            options.add_argument('--disable-gpu')
        
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--mute-audio')
        options.add_argument('--disable-webgl')
        options.add_argument('--disable-gpu-sandbox')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-backgrounding-occluded-windows')
        
        driver = None
        captured_urls = []
        
        try:
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            time.sleep(3)
            
            try:
                videos = driver.find_elements(By.CSS_SELECTOR, 'video')
                for video in videos:
                    driver.execute_script("arguments[0].play();", video)
                    break
            except:
                pass
            
            time.sleep(wait_time)
            
            logs = driver.get_log('performance')
            all_m3u8_urls = []
            
            for log in logs:
                try:
                    log_data = json.loads(log['message'])
                    message = log_data.get('message', {})
                    
                    if message.get('method') == 'Network.requestWillBeSent':
                        request_url = message.get('params', {}).get('request', {}).get('url', '')
                        
                        if '.m3u8' in request_url:
                            if request_url not in all_m3u8_urls:
                                all_m3u8_urls.append(request_url)
                except:
                    continue
            
            for m3u8_url in all_m3u8_urls:
                if any(domain in m3u8_url for domain in ['storm.vodvidl', 'vodvidl', 'hailmist', 'frostveil']):
                    captured_urls.append(m3u8_url)
            
            if not captured_urls:
                captured_urls = all_m3u8_urls
                
        except Exception as e:
            print(f"Error capturing m3u8: {e}")
        finally:
            if driver:
                driver.quit()
        
        return captured_urls if captured_urls else None
    
    def download_playlist(self, m3u8_url, output_file, quality_preference='highest'):
        session = requests.Session()
        session.headers.update({
            "sec-ch-ua-platform": '"Android"',
            "Referer": "https://vidlink.pro/",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Brave";v="140"',
            "sec-ch-ua-mobile": "?1",
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36"
        })
        
        try:
            response = session.get(m3u8_url, timeout=30)
            response.raise_for_status()
            content = response.text
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            lines = content.strip().split('\n')
            is_master = any('EXT-X-STREAM-INF' in line for line in lines)
            
            if is_master:
                quality_streams = []
                for i, line in enumerate(lines):
                    if 'EXT-X-STREAM-INF' in line:
                        resolution = 'unknown'
                        if 'RESOLUTION=' in line:
                            resolution = line.split('RESOLUTION=')[1].split(',')[0]
                        
                        stream_url = lines[i+1] if i+1 < len(lines) else ''
                        quality_streams.append({
                            'resolution': resolution,
                            'url': stream_url
                        })
                
                if quality_preference == 'highest':
                    selected_stream = quality_streams[0]
                elif quality_preference == 'lowest':
                    selected_stream = quality_streams[-1]
                elif quality_preference == '360p':
                    selected_stream = next(
                        (s for s in quality_streams if '360' in s['resolution']),
                        quality_streams[-1]  # fallback to lowest
                    )
                elif quality_preference == '720p':
                    selected_stream = next(
                        (s for s in quality_streams if '720' in s['resolution']),
                        quality_streams[0]  # fallback to highest
                    )
                elif quality_preference == '1080p':
                    selected_stream = next(
                        (s for s in quality_streams if '1080' in s['resolution']),
                        quality_streams[0]  # fallback to highest
                    )
                else:
                    selected_stream = next(
                        (s for s in quality_streams if quality_preference in s['resolution']),
                        quality_streams[0]
                    )
                
                stream_url = selected_stream['url']
                
                if stream_url.startswith('/'):
                    base_url = m3u8_url.split('/proxy/')[0] if '/proxy/' in m3u8_url else 'https://storm.vodvidl.site'
                    stream_url = base_url + stream_url
                
                segment_file = output_file.replace('.m3u8', f'_segments.m3u8')
                response = session.get(stream_url, timeout=30)
                response.raise_for_status()
                
                with open(segment_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                return segment_file
            else:
                return output_file
                
        except Exception as e:
            print(f"Error downloading playlist: {e}")
            return None


def create_session(pool_connections=30, pool_maxsize=30):
    session = requests.Session()
    
    adapter = HTTPAdapter(
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize,
        max_retries=Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504]
        )
    )
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    session.headers.update({
        "sec-ch-ua-platform": '"Android"',
        "Referer": "https://vidlink.pro/",
        "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Brave";v="140"',
        "sec-ch-ua-mobile": "?1",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36"
    })
    
    return session


def download_segment(segment_info, session, base_url):
    i, segment_url = segment_info
    full_url = base_url + segment_url
    
    try:
        response = session.get(full_url, timeout=20)
        response.raise_for_status()
        return (i, response.content, None)
    except Exception as e:
        return (i, None, e)


def download_m3u8_video(m3u8_file, output_file, max_workers=20, base_url="https://storm.vodvidl.site"):
    if not os.path.exists(m3u8_file):
        print(f"✗ M3U8 file not found: {m3u8_file}")
        return False
    
    with open(m3u8_file, 'r') as f:
        lines = f.readlines()

    segment_urls = [line.strip() for line in lines if line.strip() and not line.startswith('#')]

    if not segment_urls:
        print("✗ No segment URLs found in the m3u8 file.")
        return False

    session = create_session(pool_connections=max_workers, pool_maxsize=max_workers)
    
    segments_data = {}
    failed_segments = []
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_segment = {
            executor.submit(download_segment, (i, url), session, base_url): i 
            for i, url in enumerate(segment_urls)
        }
        
        completed = 0
        last_print_time = start_time
        
        for future in as_completed(future_to_segment):
            i, content, error = future.result()
            completed += 1
            
            if error:
                failed_segments.append(i)
            else:
                segments_data[i] = content
            
            current_time = time.time()
            if current_time - last_print_time >= 0.5 or completed % 20 == 0 or completed == len(segment_urls):
                elapsed = current_time - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                percent = (completed / len(segment_urls)) * 100
                
                total_bytes = sum(len(segments_data[i]) for i in segments_data)
                speed_mbps = (total_bytes * 8) / (elapsed * 1_000_000) if elapsed > 0 else 0
                
                bar_length = 40
                filled_length = int(bar_length * completed // len(segment_urls))
                bar = '█' * filled_length + '-' * (bar_length - filled_length)
                
                print(f"\r|{bar}| {percent:.1f}% | {rate:.1f}/s | {speed_mbps:.2f}Mbps | {completed}/{len(segment_urls)}", end='', flush=True)
                
                last_print_time = current_time
    
    print()
    
    if failed_segments:
        print(f"Retrying {len(failed_segments)} failed segments...")
        retry_success = 0
        
        for i in failed_segments[:]:
            _, content, error = download_segment((i, segment_urls[i]), session, base_url)
            if not error:
                segments_data[i] = content
                failed_segments.remove(i)
                retry_success += 1
        
        print(f"Retry successful: {retry_success}/{len(failed_segments) + retry_success}")
    
    print(f"Writing segments to {output_file}...")
    missing_count = 0
    
    with open(output_file, 'wb') as f_out:
        for i in range(len(segment_urls)):
            if i in segments_data:
                f_out.write(segments_data[i])
            else:
                missing_count += 1
    
    total_time = time.time() - start_time
    total_bytes = sum(len(segments_data[i]) for i in segments_data)
    total_mb = total_bytes / (1024 * 1024)
    avg_speed_mbps = (total_bytes * 8) / (total_time * 1_000_000)
    
    print(f"Download Complete!")
    print(f"File: {output_file}")
    print(f"Size: {total_mb:.2f} MB")
    print(f"Time: {total_time:.2f}s")
    print(f"Speed: {avg_speed_mbps:.2f} Mbps")
    
    if missing_count > 0:
        print(f"Warning: {missing_count} segments missing")
        return False
    
    return True


def parse_command_line():
    args = sys.argv[1:]
    if not args:
        return None, None, None, '720p'
    
    query_parts = []
    season = 1
    episode = 1
    quality = '720p'
    i = 0
    
    while i < len(args):
        arg = args[i]
        if arg.startswith('-s') and 'e' in arg:
            match = re.search(r'-s(\d+)e(\d+)', arg, re.IGNORECASE)
            if match:
                season = int(match.group(1))
                episode = int(match.group(2))
        elif arg.startswith('-') and not arg.startswith('-s'):
            quality = arg[1:]
        else:
            query_parts.append(arg)
        i += 1
    
    query = ' '.join(query_parts)
    return query, season, episode, quality


def main():
    query, season, episode, quality = parse_command_line()
    
    if not query:
        print("Usage: python main.py <title> [-s01e01] [-360p]")
        return
    
    searcher = TMDBSearcher()
    results = searcher.search(query)
    
    if not results:
        print("No results found")
        return
    
    selected = results[0]
    print(f"Selected: {selected['title']} ({selected['year']})")
    
    content_type = selected['type']
    
    if content_type == 'tv':
        if season is None or episode is None:
            print("Season and episode required for TV shows")
            return
    
    safe_title = "".join(c for c in selected['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
    folder_path = os.path.join(os.getcwd(), safe_title)
    os.makedirs(folder_path, exist_ok=True)
    
    if content_type == 'tv':
        output_file = os.path.join(folder_path, f"{safe_title}_S{season:02d}E{episode:02d}.ts")
    else:
        output_file = os.path.join(folder_path, f"{safe_title}.ts")
    
    capture = VidlinkCapture(headless=True)
    m3u8_urls = capture.get_m3u8_url(selected['id'], content_type, season, episode, wait_time=10)
    
    if not m3u8_urls:
        print("Failed to capture m3u8 URL")
        return
    
    m3u8_url = m3u8_urls[0]
    playlist = capture.download_playlist(m3u8_url, output_file.replace('.ts', '.m3u8'), quality)
    
    if not playlist:
        print("Failed to download playlist")
        return
    
    success = download_m3u8_video(playlist, output_file)
    
    try:
        os.remove(playlist)
    except:
        pass
    
    if success:
        mp4_output = output_file.replace('.ts', '.mp4')
        os.rename(output_file, mp4_output)
        print(f"Saved as: {mp4_output}")


if __name__ == "__main__":
    main()