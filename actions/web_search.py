import requests
import re
from urllib.parse import unquote
from html import unescape
from lococode.actions.base import BaseTool


class WebSearchTool(BaseTool):
    """Searches the web via DuckDuckGo and adds results to context."""

    def __init__(self):
        super().__init__()
        self.name = "web_search"
        self.description = "Search the web and add results to context. Usage: /search <query>"
        self.pattern = r"/search\s+(.+)"
        self.is_slash = True
        self.intent = "web_search"
        self.arg_description = "search query"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _strip_html(text):
        """Remove HTML tags and decode entities."""
        text = re.sub(r"<[^>]+>", "", text)
        return unescape(text).strip()

    @staticmethod
    def _extract_results(html, max_results=6):
        """
        Parse DuckDuckGo HTML-lite results.
        Each result block lives inside a table with class 'result-link' links
        and 'result-snippet' spans.
        """
        results = []

        # DuckDuckGo lite wraps each result in a <tr> block.
        # Links look like: <a rel="nofollow" href="..." class="result-link">Title</a>
        # Snippets are in <td class="result-snippet">...</td>
        # href comes before class in DDG lite HTML, so match the full
        # anchor tag with class='result-link' and extract href separately.
        link_pattern = re.compile(
            r'<a[^>]*class=["\']result-link["\'][^>]*>(.*?)</a>',
            re.DOTALL,
        )
        href_pattern = re.compile(r'href=["\']([^"\']*)["\']')
        snippet_pattern = re.compile(
            r'<td[^>]*class=["\']result-snippet["\'][^>]*>(.*?)</td>',
            re.DOTALL,
        )

        # Find all full <a> tags that have result-link class
        link_tags = list(re.finditer(
            r'<a[^>]*class=["\']result-link["\'][^>]*>.*?</a>',
            html, re.DOTALL,
        ))
        snippets = snippet_pattern.findall(html)

        for i, tag_match in enumerate(link_tags):
            if len(results) >= max_results:
                break
            tag = tag_match.group(0)
            title = WebSearchTool._strip_html(tag)
            # Skip sponsored ads and "more info" links
            if not title or title.lower() == "more info":
                continue
            # Check if this tag is inside a sponsored row
            preceding = html[max(0, tag_match.start() - 200):tag_match.start()]
            if "result-sponsored" in preceding:
                continue
            href_m = href_pattern.search(tag)
            url = href_m.group(1) if href_m else ""

            # Handle DuckDuckGo redirects (e.g. //duckduckgo.com/l/?uddg=...)
            if "uddg=" in url:
                try:
                    # simplistic extraction used to avoid full urlparse dep if desired, 
                    # but unquote is needed.
                    # format usually: ...?uddg=URL&rut=...
                    start = url.find("uddg=") + 5
                    end = url.find("&", start)
                    if end == -1:
                        raw_url = url[start:]
                    else:
                        raw_url = url[start:end]
                    url = unquote(raw_url)
                except Exception:
                    pass # Fallback to original if parsing fails

            snippet = WebSearchTool._strip_html(snippets[i]) if i < len(snippets) else ""
            results.append({"title": title, "url": url, "snippet": snippet})

        return results

    # ── main execute ─────────────────────────────────────────────────────

    def execute(self, match, context):
        query = match.group(1).strip()
        if not query:
            print("\033[31mError: Please provide a search query.\033[0m")
            return True

        print(f"\033[92mSearching the web for: \033[1m{query}\033[0m")

        try:
            resp = requests.get(
                "https://lite.duckduckgo.com/lite/",
                params={"q": query},
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                },
                timeout=10,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"\033[31mSearch failed: {e}\033[0m")
            return True

        results = self._extract_results(resp.text)

    # ── main execute ─────────────────────────────────────────────────────

    def execute(self, match, context):
        query = match.group(1).strip()
        if not query:
            print("\033[31mError: Please provide a search query.\033[0m")
            return True

        print(f"\033[92mSearching the web for: \033[1m{query}\033[0m")

        try:
            resp = requests.get(
                "https://lite.duckduckgo.com/lite/",
                params={"q": query},
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                },
                timeout=10,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"\033[31mSearch failed: {e}\033[0m")
            return True

        results = self._extract_results(resp.text)

        if not results:
            print("\033[33mNo results found.\033[0m")
            return True

        # Build a concise text block for the user to see
        display_block = f"── Web Search Results for \"{query}\" ──\n"
        prompt_block = ""
        for i, r in enumerate(results, 1):
            entry = f"[{i}] {r['title']}\n    {r['snippet']}\n"
            display_block += f"\n[{i}] {r['title']}\n    {r['url']}\n    {r['snippet']}\n"
            prompt_block += entry

        print(f"\033[36m{display_block}\033[0m")

        # Ask the model to pick the best result
        print(f"\033[90mAnalyzing results to pick the best one...\033[0m")
        
        best_idx = 0
        if 'stream_response' in context and 'model_id' in context:
            selection_prompt = (
                f"Here are search results for the query: \"{query}\"\n\n"
                f"{prompt_block}\n\n"
                "Identify the single most relevant result. Respond with ONLY the index number (e.g., 1)."
            )
            
            messages = [{"role": "user", "content": selection_prompt}]
            # Call the model via the function stored in context
            response = context['stream_response'](context['model_id'], messages, silent=True)
            
            if response:
                # Extract the first number found
                match = re.search(r'\d+', response)
                if match:
                    idx = int(match.group())
                    if 1 <= idx <= len(results):
                        best_idx = idx - 1
        
        best_result = results[best_idx]
        print(f"\033[92mSelected result [{best_idx+1}]: {best_result['title']}\033[0m")

        # Fetch the full page content
        url = best_result['url']
        page_content = ""
        
        if url:
            print(f"\033[90mFetching content from {url}...\033[0m")
            try:
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                }
                # Use a slightly longer timeout for page loads
                page_resp = requests.get(url, headers=headers, timeout=15)
                page_resp.raise_for_status()
                
                raw_html = page_resp.text
                
                # Remove scripts and styles first
                raw_html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw_html, flags=re.DOTALL | re.IGNORECASE)
                
                # Use the existing strip_html method
                page_content = self._strip_html(raw_html)
                
                # Collapse excessive whitespace
                page_content = re.sub(r'\s+', ' ', page_content).strip()
                
                # Limit content length to avoid overflowing context excessively
                max_len = 8000
                if len(page_content) > max_len:
                     page_content = page_content[:max_len] + "... [truncated]"
                     
            except Exception as e:
                print(f"\033[31mFailed to fetch page content: {e}\033[0m")
                page_content = f"Error fetching content: {e}. Falling back to snippet: {best_result['snippet']}"
        else:
            page_content = best_result['snippet']

        # Format the included context
        final_context = (
            f"── Selected Search Result for \"{query}\" ──\n"
            f"Title: {best_result['title']}\n"
            f"Source: {url}\n"
            f"Full Page Content: {page_content}\n"
        )

        display_limit = 1000
        preview = page_content[:display_limit] + "..." if len(page_content) > display_limit else page_content

        print(f"\n\033[93m--- Page Content Preview ---\033[0m")
        print(f"{preview}")
        print(f"\033[93m----------------------------\033[0m")
        print(f"\033[90m(Total length: {len(page_content)} chars)\033[0m")

        confirm = input("\n\033[1;37mInclude this content in the context? (y/n): \033[0m").strip().lower()
        
        if confirm == 'y':
            # Store ONLY the best result in context
            search_history = context.setdefault("search_results", [])
            search_history.append(final_context)

            print(
                "\033[92mBest result saved to context. "
                "It will be included in the next edit prompt.\033[0m"
            )
        else:
            print("\033[33mContent discarded.\033[0m")
        
        return True
