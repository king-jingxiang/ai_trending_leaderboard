import requests
from bs4 import BeautifulSoup
from github import Github
from github.GithubException import GithubException
from .config import Config
import time
import logging
import random
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self):
        tokens = Config.GITHUB_TOKENS if Config.GITHUB_TOKENS else [None]
        self._token_states = []
        for token in tokens:
            client = Github(token) if token else Github()
            self._token_states.append({
                "token": token,
                "client": client,
                "cooldown_until": 0.0,
                "last_request_at": 0.0
            })
        self._token_lock = threading.Lock()
        self._token_cursor = 0
        self.max_retries = 5
        self.base_delay = 2
        self.max_delay = 900
        self.jitter_ratio = 0.3
        self.request_delay = max(0.0, Config.GITHUB_REQUEST_DELAY)

    @property
    def max_concurrency(self):
        return max(1, len(self._token_states))

    def _get_rate_limit_reset_delay(self, exception):
        headers = getattr(exception, "headers", None) or {}
        reset_value = headers.get("X-RateLimit-Reset") or headers.get("x-ratelimit-reset")
        if not reset_value:
            return None
        try:
            reset_ts = int(reset_value)
        except ValueError:
            return None
        now_ts = int(time.time())
        return max(0, reset_ts - now_ts) + 5

    def _compute_backoff(self, attempt, exception=None):
        delay = min(self.max_delay, self.base_delay * (2 ** (attempt - 1)))
        jitter = random.uniform(0, delay * self.jitter_ratio)
        delay = delay + jitter
        if exception and getattr(exception, "status", None) in (403, 429):
            reset_delay = self._get_rate_limit_reset_delay(exception)
            if reset_delay is not None:
                delay = max(delay, reset_delay)
        return delay

    def _is_rate_limited(self, exception):
        if getattr(exception, "status", None) != 403:
            return False
        data = getattr(exception, "data", None)
        if isinstance(data, dict):
            message = str(data.get("message", "")).lower()
            if "rate limit" in message:
                return True
        headers = getattr(exception, "headers", None) or {}
        remaining = headers.get("X-RateLimit-Remaining") or headers.get("x-ratelimit-remaining")
        return remaining == "0"

    def _mark_rate_limited(self, token_index, exception):
        delay = self._get_rate_limit_reset_delay(exception)
        if delay is None:
            delay = max(self.base_delay, 60)
        with self._token_lock:
            self._token_states[token_index]["cooldown_until"] = time.monotonic() + delay

    def _select_token_index(self):
        while True:
            now = time.monotonic()
            with self._token_lock:
                available = [
                    i for i, state in enumerate(self._token_states)
                    if state["cooldown_until"] <= now
                ]
                if available:
                    start = self._token_cursor
                    for offset in range(len(self._token_states)):
                        idx = (start + offset) % len(self._token_states)
                        if idx in available:
                            self._token_cursor = (idx + 1) % len(self._token_states)
                            return idx
                next_ready = min(state["cooldown_until"] for state in self._token_states)
                wait_for = max(0, next_ready - now)
            if wait_for > 0:
                time.sleep(wait_for)

    def _wait_for_request_slot(self, token_index):
        if self.request_delay <= 0:
            return
        while True:
            with self._token_lock:
                last_request_at = self._token_states[token_index]["last_request_at"]
                now = time.monotonic()
                wait_for = self.request_delay - (now - last_request_at)
                if wait_for <= 0:
                    self._token_states[token_index]["last_request_at"] = now
                    return
            time.sleep(wait_for)

    def _with_retry(self, action, label):
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                token_index = self._select_token_index()
                self._wait_for_request_slot(token_index)
                client = self._token_states[token_index]["client"]
                return action(client)
            except GithubException as e:
                last_exception = e
                if self._is_rate_limited(e):
                    self._mark_rate_limited(token_index, e)
                    continue
                if e.status in (403, 429, 500, 502, 503, 504):
                    delay = self._compute_backoff(attempt, e)
                    logger.info(f"{label} failed with {e.status}, retrying in {delay:.2f}s")
                    time.sleep(delay)
                    continue
                raise
            except Exception as e:
                last_exception = e
                delay = self._compute_backoff(attempt)
                logger.info(f"{label} failed, retrying in {delay:.2f}s")
                time.sleep(delay)
                continue
        if last_exception:
            raise last_exception

    def get_trending(self, time_range='daily'):
        """
        Scrapes GitHub trending page.
        time_range: 'daily', 'weekly', 'monthly'
        """
        url = f"https://github.com/trending?since={time_range}"
        print(f"Fetching trending from {url}...")
        try:
            response = requests.get(url)
            response.raise_for_status()
        except Exception as e:
            print(f"Error fetching trending page: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        repos = []
        
        for article in soup.select('article.Box-row'):
            try:
                # Get repo name (owner/repo)
                h1 = article.select_one('h2.h3 a')
                if not h1: continue
                full_name = h1.get_text(strip=True).replace(' ', '')
                owner, repo_name = full_name.split('/')
                
                # Get description
                p = article.select_one('p.col-9')
                description = p.get_text(strip=True) if p else ""
                
                # Get meta info
                div = article.select_one('div.f6')
                
                # Language
                lang_span = div.select_one('span[itemprop="programmingLanguage"]')
                language = lang_span.get_text(strip=True) if lang_span else "Unknown"
                
                # Stars and Forks
                # This part can be tricky as selectors change, but usually they are links
                links = div.select('a.Link--muted')
                stars = 0
                forks = 0
                if len(links) >= 1:
                    stars_text = links[0].get_text(strip=True).replace(',', '')
                    stars = int(stars_text)
                if len(links) >= 2:
                    forks_text = links[1].get_text(strip=True).replace(',', '')
                    forks = int(forks_text)
                    
                # Growth (Today stars)
                # Usually the last span in the div
                growth_span = div.select_one('span.d-inline-block.float-sm-right')
                growth = 0
                if growth_span:
                    growth_text = growth_span.get_text(strip=True).replace(',', '').replace(' stars today', '').replace(' stars this week', '').replace(' stars this month', '')
                    try:
                        growth = int(growth_text)
                    except ValueError:
                        pass

                repos.append({
                    "owner": owner,
                    "repo": repo_name,
                    "description": description,
                    "language": language,
                    "stars": stars,
                    "forks": forks,
                    "growth": growth,
                    "since": time_range
                })
            except Exception as e:
                print(f"Error parsing repo: {e}")
                continue
                
        return repos

    def get_repo_details(self, owner, repo_name):
        try:
            repo = self._with_retry(
                lambda client: client.get_repo(f"{owner}/{repo_name}"),
                f"GET /repos/{owner}/{repo_name}"
            )
            try:
                readme = self._with_retry(
                    lambda client: self._get_readme_content(client, owner, repo_name),
                    f"GET /repos/{owner}/{repo_name}/readme"
                )
            except GithubException as e:
                if e.status == 404:
                    readme = ""
                else:
                    raise
            return {
                "owner": owner,
                "repo": repo_name,
                "full_name": repo.full_name,
                "description": repo.description,
                "html_url": repo.html_url,
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat(),
                "pushed_at": repo.pushed_at.isoformat(),
                "stargazers_count": repo.stargazers_count,
                "forks_count": repo.forks_count,
                "language": repo.language,
                "topics": self._with_retry(
                    lambda client: client.get_repo(f"{owner}/{repo_name}").get_topics(),
                    f"GET /repos/{owner}/{repo_name}/topics"
                ),
                "readme": readme
            }
        except GithubException as e:
            print(f"Error getting repo details for {owner}/{repo_name}: {e}")
            return None

    def _get_readme_content(self, client, owner, repo_name):
        repo = client.get_repo(f"{owner}/{repo_name}")
        content = repo.get_readme()
        return content.decoded_content.decode('utf-8')

    def get_star_history(self, owner, repo_name, current_history=None):
        """
        Fetches star history. 
        If current_history is provided, it tries to append only new data (optimized).
        Otherwise, it fetches full history (expensive).
        
        NOTE: Getting full star history via API is expensive (1 request per 100 stars).
        For this MVP, we will use a simplified approach:
        1. If no history, we fetch sample points or use a 3rd party service if available.
           Actually, the design doc suggests using `/repos/{owner}/{repo}/stargazers`.
           Let's implement a sampler for large repos to avoid rate limits.
        2. If history exists, we just append today's count.
        """
        
        # Optimization: Just append today's count if history exists
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        if current_history:
            # Check if today is already in history
            if current_history[-1]['date'] == today_str:
                return current_history
            
            # Get current stars
            repo = self._with_retry(
                lambda client: client.get_repo(f"{owner}/{repo_name}"),
                f"GET /repos/{owner}/{repo_name}"
            )
            current_history.append({
                "date": today_str,
                "count": repo.stargazers_count
            })
            return current_history

        # If no history, we need to fetch it.
        # Strategy: 
        # For small repos (< 2000 stars), fetch all.
        # For large repos, we might need a better strategy or just fetch the last few pages 
        # to get recent growth, and assume linear growth before? 
        # Or better: just record "First Seen" as today.
        
        # The design doc says: 
        # "First Seen: Call GitHub API ... (sample for large projects)"
        # "Daily Update: Append (Today, Current Stars)"
        
        # Let's try to get some history.
        try:
            repo = self._with_retry(
                lambda client: client.get_repo(f"{owner}/{repo_name}"),
                f"GET /repos/{owner}/{repo_name}"
            )
            total_stars = repo.stargazers_count
            
            history = []
            
            # If stars > 4000, it's too expensive to fetch all pages (40+ requests).
            # We will just take the current state as the starting point for "our" tracking.
            # OR we can try to get the "creation date" as 0 stars.
            
            history.append({
                "date": repo.created_at.strftime('%Y-%m-%d'),
                "count": 0
            })
            
            if total_stars < 2000:
                stargazers = self._with_retry(
                    lambda client: client.get_repo(f"{owner}/{repo_name}").get_stargazers_with_dates(),
                    f"GET /repos/{owner}/{repo_name}/stargazers"
                )
                # Aggregate by day
                star_dates = [s.starred_at.date() for s in stargazers]
                from collections import Counter
                counts = Counter(star_dates)
                sorted_dates = sorted(counts.keys())
                
                cum_stars = 0
                for date in sorted_dates:
                    cum_stars += counts[date]
                    history.append({
                        "date": date.strftime('%Y-%m-%d'),
                        "count": cum_stars
                    })
            else:
                # For large repos, just record today. 
                # Ideally we would use the 'Star History' simplified algorithm (sample pages)
                # But for now, let's keep it simple: Start tracking from today + creation date.
                history.append({
                    "date": today_str,
                    "count": total_stars
                })
                
            return history
            
        except Exception as e:
            print(f"Error fetching star history: {e}")
            return [{"date": today_str, "count": 0}] # Fallback


if __name__ == "__main__":
    gh_client = GitHubClient()
    # 测试获取仓库详情
    repo_details = gh_client.get_repo_details("anthropics", "skills")
    if repo_details:
        print(repo_details)
    else:
        print("Failed to get repo details")
    star_history = gh_client.get_star_history("anthropics", "skills")
    print(star_history)
