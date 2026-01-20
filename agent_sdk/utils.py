from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse, urljoin, urlunparse
import time
import requests

def safe_scrape(full_path, user_agent="My_bot", delay=1):
    """
    Polite and safe web scraping
    Parameters:
    - full_path : full URL to fetch
    - user_agent: User-Agent to use for requests
    - delay     : delay between requests (seconds)
    """
    parsed = urlparse(full_path)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    # robots.txt check
    robots_url = urljoin(base_url, "/robots.txt")
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        robots_available = True
    except:
        robots_available = False
        print(f"[INFO] robots.txt not found: {robots_url}")

    if robots_available and not rp.can_fetch(user_agent, full_path):
        print(f"[WARNING] {full_path} is blocked by robots.txt. Aborting.")
        return None
    elif not robots_available:
        print("[INFO] robots.txt missing; proceed politely and ethically.")

    # Polite request
    headers = {"User-Agent": user_agent}
    try:
        time.sleep(delay)
        resp = requests.get(full_path, headers=headers)
        if resp.status_code == 200:
            return resp.text
        else:
            return None
    except Exception as e:
        return None
    


def _parse_crawl_delays(robots_text):
    """
    Extracts Crawl-delay directives from robots.txt by block.
    Returns: {agent_lower: crawl_delay_seconds (float)} (takes the first found value per agent)
    """
    lines = [ln.split('#',1)[0].strip() for ln in robots_text.splitlines()]
    delays = {}
    current_agents = []
    for ln in lines:
        if not ln:
            continue
        parts = [p.strip() for p in ln.split(':', 1)]
        if len(parts) != 2:
            continue
        key, val = parts[0].lower(), parts[1]
        if key == 'user-agent':
            current_agents = [a.strip().lower() for a in val.split()]
        elif key == 'crawl-delay' and current_agents:
            try:
                d = float(val)
            except ValueError:
                continue
            for a in current_agents:
                if a not in delays:
                    delays[a] = d
    return delays

def is_scrapable(full_path: str, user_agent: str="My_bot", delay: float=2) -> bool:
    """
    full_path: full URL (eg. "https://example.com/some/page")
    user_agent: the agent string making the request (eg. "my-bot" or "Mozilla/5.0")
    delay: planned delay between your requests (float, seconds)
    Returns: True => scrapable, False => disallowed or insufficient delay
    """
    try:
        parsed = urlparse(full_path)
        if not parsed.scheme:
            # if scheme missing, default to http
            parsed = parsed._replace(scheme='http')
        base = urlunparse((parsed.scheme, parsed.netloc, '/robots.txt', '', '', ''))
        resp = requests.get(base, timeout=6)
    except Exception:
        # if robots.txt cannot be read, act cautiously
        return False

    # if robots.txt is missing (404) => allow
    if resp.status_code == 404:
        return True
    if resp.status_code != 200:
        return False

    robots_text = resp.text

    # 1) Use RobotFileParser for Allow/Disallow checks
    parser = RobotFileParser()
    # parser.parse expects lines
    parser.parse([ln + '\n' for ln in robots_text.splitlines()])
    can = parser.can_fetch(user_agent, full_path)
    if not can:
        return False

    # 2) Check Crawl-delay (if present)
    delays = _parse_crawl_delays(robots_text)  # agent_lower -> seconds
    ua_lower = user_agent.strip().lower()
    matched_delay = None

    # Doğrudan exact agent, yoksa wildcard '*' bak
    if ua_lower in delays:
        matched_delay = delays[ua_lower]
    elif '*' in delays:
        matched_delay = delays['*']
    else:
        # robots.txt içinde agent isimleri bazen kısa veya kısmi olabilir.
        # Daha iyi eşleşme için agent parçalarını kontrol et:
        for agent_key, dval in delays.items():
            if agent_key != '*' and agent_key in ua_lower:
                matched_delay = dval
                break

    if matched_delay is None:
        # no crawl-delay specified => sufficient
        return True

    # If robots.txt specifies a crawl-delay, disallow if your delay is
    # smaller (i.e., you would request more frequently).
    return delay >= matched_delay