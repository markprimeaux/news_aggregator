#!/usr/bin/env python3
"""
Global News Aggregator
Fetches and displays news articles from RSS feeds around the world.

MIT License

Copyright (c) 2025 Mark Primeaux

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import feedparser
from datetime import datetime
from typing import List, Dict, Optional
import sys
import subprocess
import tempfile
import os
import curses
import textwrap
import requests
from bs4 import BeautifulSoup
from readability import Document

# Global news sources with their RSS feeds and categories
NEWS_SOURCES = {
    # US News Sources
    "NPR News": {"url": "https://feeds.npr.org/1001/rss.xml", "category": "US News"},
    "CBS News": {"url": "https://www.cbsnews.com/latest/rss/main", "category": "US News"},
    "NBC News": {"url": "https://feeds.nbcnews.com/nbcnews/public/news", "category": "US News"},
    "The New York Times": {"url": "https://rss.nytimes.com/services/xml/rss/nyt/US.xml", "category": "US News"},
    "PBS NewsHour": {"url": "https://www.pbs.org/newshour/feeds/rss/world", "category": "US News"},

    # General International News
    "BBC World": {"url": "http://feeds.bbci.co.uk/news/world/rss.xml", "category": "World News"},
    "Al Jazeera": {"url": "https://www.aljazeera.com/xml/rss/all.xml", "category": "World News"},
    "The Guardian World": {"url": "https://www.theguardian.com/world/rss", "category": "World News"},
    "Deutsche Welle": {"url": "https://rss.dw.com/xml/rss-en-all", "category": "World News"},
    "France 24": {"url": "https://www.france24.com/en/rss", "category": "World News"},
    "South China Morning Post": {"url": "https://www.scmp.com/rss/91/feed", "category": "World News"},
    "The Japan Times": {"url": "https://www.japantimes.co.jp/feed/", "category": "World News"},
    "Times of India": {"url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "category": "World News"},
    "ABC News Australia": {"url": "https://www.abc.net.au/news/feed/51120/rss.xml", "category": "World News"},

    # Political Science & National Security Sources
    "Council on Foreign Relations": {"url": "https://www.cfr.org/feed", "category": "Political Analysis"},
    "Foreign Policy Magazine": {"url": "https://foreignpolicy.com/feed/", "category": "Political Analysis"},
    "War on the Rocks": {"url": "https://warontherocks.com/feed/", "category": "National Security"},
    "The Diplomat": {"url": "https://thediplomat.com/feed/", "category": "Political Analysis"},
    "Lawfare": {"url": "https://www.lawfaremedia.org/feed", "category": "National Security"},
    "Center for Strategic & International Studies": {"url": "https://www.csis.org/analysis/feed", "category": "Political Analysis"},
    "Brookings Institution": {"url": "https://www.brookings.edu/feed/", "category": "Political Analysis"},
    "Defense One": {"url": "https://www.defenseone.com/rss/", "category": "National Security"},
    "The Atlantic": {"url": "https://www.theatlantic.com/feed/all", "category": "News & Analysis"},
    "The Atlantic - Politics": {"url": "https://www.theatlantic.com/feed/channel/politics/", "category": "Political Analysis"},

    # Premium/Magazine Sources
    "The New Yorker": {"url": "https://www.newyorker.com/feed/news", "category": "News & Analysis"},
    "ProPublica": {"url": "https://www.propublica.org/feeds/propublica/main", "category": "Investigative Journalism"},
    "The Economist": {"url": "https://www.economist.com/rss", "category": "News & Analysis"},

    # Tech/Science
    "Ars Technica": {"url": "https://feeds.arstechnica.com/arstechnica/index", "category": "Tech & Science"},
    "MIT Technology Review": {"url": "https://www.technologyreview.com/feed/", "category": "Tech & Science"},

    # Tech Security & IT Professional News
    "Krebs on Security": {"url": "https://krebsonsecurity.com/feed/", "category": "Tech Security"},
    "The Hacker News": {"url": "https://feeds.feedburner.com/TheHackersNews", "category": "Tech Security"},
    "Bleeping Computer": {"url": "https://www.bleepingcomputer.com/feed/", "category": "Tech Security"},
    "Dark Reading": {"url": "https://www.darkreading.com/rss_simple.asp", "category": "Tech Security"},
    "Security Week": {"url": "https://www.securityweek.com/feed/", "category": "Tech Security"},
    "Threatpost": {"url": "https://threatpost.com/feed/", "category": "Tech Security"},
    "Schneier on Security": {"url": "https://www.schneier.com/feed/atom/", "category": "Tech Security"},
    "SANS Internet Storm Center": {"url": "https://isc.sans.edu/rssfeed.xml", "category": "Tech Security"},
    "The Register": {"url": "https://www.theregister.com/headlines.atom", "category": "IT Professional"},
    "ZDNet Security": {"url": "https://www.zdnet.com/topic/security/rss.xml", "category": "IT Professional"},
    "CSO Online": {"url": "https://www.csoonline.com/feed/", "category": "IT Professional"},
    "InfoSecurity Magazine": {"url": "https://www.infosecurity-magazine.com/rss/news/", "category": "Tech Security"},
    "Naked Security": {"url": "https://nakedsecurity.sophos.com/feed/", "category": "Tech Security"},
    "TechCrunch Security": {"url": "https://techcrunch.com/category/security/feed/", "category": "Tech Security"},

    # Analysis
    "Vox": {"url": "https://www.vox.com/rss/index.xml", "category": "News & Analysis"},
}


def fetch_articles(feed_url: str, source_name: str, category: str, max_articles: int = 5) -> List[Dict]:
    """
    Fetch articles from an RSS feed.

    Args:
        feed_url: URL of the RSS feed
        source_name: Name of the news source
        category: Category of the news source
        max_articles: Maximum number of articles to fetch

    Returns:
        List of article dictionaries
    """
    try:
        feed = feedparser.parse(feed_url)
        articles = []

        for entry in feed.entries[:max_articles]:
            article = {
                'title': entry.get('title', 'No title'),
                'link': entry.get('link', ''),
                'published': entry.get('published', 'Unknown date'),
                'summary': entry.get('summary', entry.get('description', 'No summary available')),
                'source': source_name,
                'category': category
            }
            articles.append(article)

        return articles
    except Exception as e:
        print(f"Error fetching from {source_name}: {str(e)}", file=sys.stderr)
        return []


def clean_html(text: str) -> str:
    """Remove HTML tags from text."""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def format_articles_output(articles: List[Dict], show_summary: bool = False) -> str:
    """
    Format articles as a string for display.

    Args:
        articles: List of article dictionaries
        show_summary: Whether to include article summaries

    Returns:
        Formatted string of all articles
    """
    output = []
    output.append("\n" + "="*80)
    output.append("GLOBAL NEWS AGGREGATOR".center(80))
    output.append(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(80))
    output.append("="*80 + "\n")

    for idx, article in enumerate(articles, 1):
        output.append(f"\n[{idx}] {article['source']} - [{article['category']}]")
        output.append("-" * 80)
        output.append(f"📰 {article['title']}")
        output.append(f"🔗 {article['link']}")
        output.append(f"📅 {article['published']}")

        if show_summary and article['summary']:
            summary = clean_html(article['summary'])
            # Truncate long summaries
            if len(summary) > 300:
                summary = summary[:300] + "..."
            output.append(f"\n{summary}")

        output.append("-" * 80)

    output.append("\n" + "="*80)
    output.append(f"Total articles displayed: {len(articles)}".center(80))
    output.append("="*80 + "\n")

    return "\n".join(output)


def display_in_pager(content: str):
    """
    Display content in a pager (less/more).

    Args:
        content: Text content to display
    """
    # Try to use the user's preferred pager or fall back to less/more
    pager = os.environ.get('PAGER', 'less')

    # Check if less is available and use it with nice options
    pagers_to_try = [
        ['less', '-R', '-X', '-F'],  # -R for colors, -X no clear, -F quit if one screen
        ['less'],
        ['more'],
    ]

    for pager_cmd in pagers_to_try:
        try:
            # Create a temporary file with the content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            try:
                # Open the pager
                subprocess.run(pager_cmd + [tmp_path])
                return
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
        except (FileNotFoundError, subprocess.SubprocessError):
            continue

    # If no pager works, just print directly
    print(content)


def fetch_article_content(url: str) -> Optional[str]:
    """
    Fetch and extract the main content from an article URL.

    Args:
        url: URL of the article to fetch

    Returns:
        Extracted article text or None if failed
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Use readability to extract main content
        doc = Document(response.text)

        # Parse the HTML content
        soup = BeautifulSoup(doc.summary(), 'html.parser')

        # Extract text
        text = soup.get_text(separator='\n', strip=True)

        return text
    except Exception as e:
        return f"Error fetching article: {str(e)}"


def interactive_article_selector(stdscr, articles: List[Dict]) -> Optional[int]:
    """
    Display an interactive article selector with vim keybindings.

    Args:
        stdscr: Curses window object
        articles: List of article dictionaries

    Returns:
        Selected article index, None if quit, or -1 to refresh
    """
    curses.curs_set(0)  # Hide cursor
    current_row = 0
    top_row = 0  # For scrolling

    # Color setup
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Highlight
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Title
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Source

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Header
        header = "📰 NEWS AGGREGATOR - j/k: move, Enter: read, Shift+R: refresh, q: quit"
        stdscr.addstr(0, 0, header[:width-1], curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(1, 0, "=" * (width-1))

        # Calculate visible range
        visible_rows = height - 4  # Account for header and footer
        if current_row < top_row:
            top_row = current_row
        elif current_row >= top_row + visible_rows:
            top_row = current_row - visible_rows + 1

        # Display articles
        for idx in range(top_row, min(top_row + visible_rows, len(articles))):
            article = articles[idx]
            y_pos = idx - top_row + 2

            if y_pos >= height - 2:
                break

            # Prepare display text with category
            category_tag = f"[{article['category']}]"
            source_display = f"{article['source'][:20]}"
            # Calculate remaining width for title
            prefix_len = len(f"[{idx+1:2d}] {category_tag} {source_display} | ")
            title_width = width - prefix_len - 1
            display_text = f"[{idx+1:2d}] {category_tag} {source_display} | {article['title'][:title_width]}"

            if idx == current_row:
                stdscr.addstr(y_pos, 0, display_text[:width-1],
                            curses.color_pair(1) | curses.A_BOLD)
            else:
                stdscr.addstr(y_pos, 0, display_text[:width-1])

        # Footer
        footer = f"Article {current_row + 1}/{len(articles)}"
        if height > 3:
            stdscr.addstr(height-1, 0, footer[:width-1], curses.color_pair(2))

        stdscr.refresh()

        # Handle input
        key = stdscr.getch()

        # Vim keybindings
        if key in [ord('q'), ord('Q'), 27]:  # q, Q, or ESC
            return None
        elif key in [ord('R')]:  # Shift+R to refresh
            return -1
        elif key in [ord('j'), curses.KEY_DOWN]:
            current_row = min(current_row + 1, len(articles) - 1)
        elif key in [ord('k'), curses.KEY_UP]:
            current_row = max(current_row - 1, 0)
        elif key in [ord('g')]:
            # gg to go to top
            next_key = stdscr.getch()
            if next_key == ord('g'):
                current_row = 0
                top_row = 0
        elif key in [ord('G')]:
            # G to go to bottom
            current_row = len(articles) - 1
        elif key in [ord('d')]:
            # Ctrl+d - half page down
            current_row = min(current_row + visible_rows // 2, len(articles) - 1)
        elif key in [ord('u')]:
            # Ctrl+u - half page up
            current_row = max(current_row - visible_rows // 2, 0)
        elif key in [10, 13, curses.KEY_ENTER]:  # Enter key
            return current_row


def display_article_reader(article: Dict):
    """
    Fetch and display the full article content in a pager with beautiful formatting.

    Args:
        article: Article dictionary with title, link, source
    """
    print(f"\n🔄 Fetching article from {article['source']}...")
    print(f"📰 {article['title']}\n")

    content = fetch_article_content(article['link'])

    if not content:
        print("❌ Could not fetch article content.")
        return

    # Format the article with beautiful typography
    output = []
    width = 80

    # Top border with decorative elements
    output.append("")
    output.append("╔" + "═" * (width - 2) + "╗")

    # Title - wrapped and centered
    title_lines = textwrap.wrap(article['title'], width=width - 8)
    for title_line in title_lines:
        output.append("║ " + title_line.center(width - 4) + " ║")

    output.append("╚" + "═" * (width - 2) + "╝")
    output.append("")

    # Metadata section with nice formatting
    output.append("┌" + "─" * (width - 2) + "┐")
    output.append("│ " + "📰 SOURCE".ljust(width - 4) + " │")
    source_wrapped = textwrap.wrap(f"   {article['source']}", width=width - 4)
    for line in source_wrapped:
        output.append("│ " + line.ljust(width - 4) + " │")
    output.append("│" + " " * (width - 2) + "│")
    output.append("│ " + "📅 PUBLISHED".ljust(width - 4) + " │")
    output.append("│ " + f"   {article['published']}".ljust(width - 4) + " │")
    output.append("│" + " " * (width - 2) + "│")
    output.append("│ " + "🔗 LINK".ljust(width - 4) + " │")
    link_wrapped = textwrap.wrap(f"   {article['link']}", width=width - 4)
    for line in link_wrapped:
        output.append("│ " + line.ljust(width - 4) + " │")
    output.append("└" + "─" * (width - 2) + "┘")
    output.append("")
    output.append("")

    # Article body with nice spacing
    output.append("─" * width)
    output.append("")

    # Process content with paragraph detection
    paragraphs = content.split('\n\n')

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Check if it looks like a heading (short, no punctuation at end)
        if len(para) < 80 and not para.endswith(('.', '!', '?', '"', "'")):
            # Format as heading
            output.append("")
            output.append("▶ " + para.upper())
            output.append("")
        else:
            # Format as paragraph with proper indentation
            # First line indented, justified text
            lines = textwrap.wrap(para, width=width - 4)
            if lines:
                output.append("    " + lines[0])  # First line with indent
                for line in lines[1:]:
                    output.append("    " + line)
                output.append("")  # Blank line after paragraph

    # Footer
    output.append("")
    output.append("─" * width)
    output.append("")
    output.append("┌" + "─" * (width - 2) + "┐")
    output.append("│" + "END OF ARTICLE".center(width - 2) + "│")
    output.append("│" + "Press 'q' to return to article list".center(width - 2) + "│")
    output.append("└" + "─" * (width - 2) + "┘")
    output.append("")

    formatted_content = "\n".join(output)
    display_in_pager(formatted_content)


def get_available_categories() -> List[str]:
    """
    Get list of unique categories from news sources.

    Returns:
        Sorted list of unique categories
    """
    categories = set()
    for source_info in NEWS_SOURCES.values():
        categories.add(source_info['category'])
    return sorted(categories)


def interactive_main_menu(stdscr) -> Optional[str]:
    """
    Display the main menu with options to browse by category, individual sources, or exit.

    Args:
        stdscr: Curses window object

    Returns:
        Menu choice: "categories", "sources", or None for exit
    """
    curses.curs_set(0)  # Hide cursor
    current_row = 0

    menu_items = [
        ("Browse by Category", "categories", "View news organized by topic categories"),
        ("Browse Individual Sources", "sources", "Select specific news sources"),
        ("View All Sources", "all", "See articles from all available sources"),
        ("Exit", "exit", "Quit the application")
    ]

    # Color setup
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Highlight
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Title
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Menu items
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)    # Exit option

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Header
        header = "📰 GLOBAL NEWS AGGREGATOR"
        stdscr.addstr(0, (width - len(header)) // 2, header, curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(1, 0, "=" * (width-1))

        instructions = "j/k or ↑/↓: move | 1-4: quick select | Enter: confirm | q: quit"
        stdscr.addstr(2, (width - len(instructions)) // 2, instructions)
        stdscr.addstr(3, 0, "=" * (width-1))

        # Display menu options
        start_row = 6
        for idx, (label, value, description) in enumerate(menu_items):
            y_pos = start_row + (idx * 3)

            if y_pos >= height - 3:
                break

            # Number key shortcut
            number_key = idx + 1
            display_text = f"[{number_key}] {label}"

            # Choose color based on item
            item_color = curses.color_pair(4) if value == "exit" else curses.color_pair(3)

            if idx == current_row:
                stdscr.addstr(y_pos, (width - len(display_text)) // 2, display_text,
                            curses.color_pair(1) | curses.A_BOLD)
            else:
                stdscr.addstr(y_pos, (width - len(display_text)) // 2, display_text, item_color)

            # Show description
            if idx == current_row:
                stdscr.addstr(y_pos + 1, (width - len(description)) // 2, description,
                            curses.color_pair(2))

        # Footer
        footer = f"Option {current_row + 1}/{len(menu_items)}"
        if height > 3:
            stdscr.addstr(height-1, (width - len(footer)) // 2, footer, curses.color_pair(2))

        stdscr.refresh()

        # Handle input
        key = stdscr.getch()

        # Quit
        if key in [ord('q'), ord('Q'), 27]:  # q, Q, or ESC
            return None
        # Navigation
        elif key in [ord('j'), curses.KEY_DOWN]:
            current_row = min(current_row + 1, len(menu_items) - 1)
        elif key in [ord('k'), curses.KEY_UP]:
            current_row = max(current_row - 1, 0)
        # Number keys 1-4
        elif key in [ord(str(i)) for i in range(1, min(10, len(menu_items) + 1))]:
            number = int(chr(key))
            if 1 <= number <= len(menu_items):
                selected = menu_items[number - 1][1]
                return None if selected == "exit" else selected
        # Enter to select
        elif key in [10, 13, curses.KEY_ENTER]:  # Enter key
            selected = menu_items[current_row][1]
            return None if selected == "exit" else selected


def interactive_category_selector(stdscr, categories: List[str]) -> Optional[str]:
    """
    Display an interactive category selector with keyboard navigation.

    Args:
        stdscr: Curses window object
        categories: List of category names

    Returns:
        Selected category name or None if quit/back
    """
    curses.curs_set(0)  # Hide cursor
    current_row = 0

    menu_items = categories

    # Color setup
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Highlight
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Title
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Category

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Header
        header = "📰 SELECT NEWS CATEGORY"
        stdscr.addstr(0, (width - len(header)) // 2, header, curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(1, 0, "=" * (width-1))

        instructions = "j/k or ↑/↓: move | 1-9: quick select | Enter: confirm | q/ESC: back"
        stdscr.addstr(2, (width - len(instructions)) // 2, instructions)
        stdscr.addstr(3, 0, "=" * (width-1))

        # Display category options with source counts
        start_row = 5
        for idx, category in enumerate(menu_items):
            y_pos = start_row + idx

            if y_pos >= height - 2:
                break

            # Count sources in this category
            source_count = sum(1 for s in NEWS_SOURCES.values() if s['category'] == category)

            # Map number keys (1-9 for first 9 items)
            if idx < 9:
                number_key = idx + 1
                display_text = f"[{number_key}] {category} ({source_count} sources)"
            else:
                display_text = f"    {category} ({source_count} sources)"

            if idx == current_row:
                stdscr.addstr(y_pos, (width - len(display_text)) // 2, display_text,
                            curses.color_pair(1) | curses.A_BOLD)
            else:
                stdscr.addstr(y_pos, (width - len(display_text)) // 2, display_text,
                            curses.color_pair(3))

        # Footer
        footer = f"Category {current_row + 1}/{len(menu_items)}"
        if height > 3:
            stdscr.addstr(height-1, (width - len(footer)) // 2, footer, curses.color_pair(2))

        stdscr.refresh()

        # Handle input
        key = stdscr.getch()

        # Quit/Back
        if key in [ord('q'), ord('Q'), 27]:  # q, Q, or ESC
            return None
        # Navigation
        elif key in [ord('j'), curses.KEY_DOWN]:
            current_row = min(current_row + 1, len(menu_items) - 1)
        elif key in [ord('k'), curses.KEY_UP]:
            current_row = max(current_row - 1, 0)
        # Number keys 1-9
        elif key in [ord(str(i)) for i in range(1, min(10, len(menu_items) + 1))]:
            number = int(chr(key))
            if 1 <= number <= len(menu_items):
                return menu_items[number - 1]
        # Enter to select
        elif key in [10, 13, curses.KEY_ENTER]:  # Enter key
            return menu_items[current_row]


def interactive_source_selector(stdscr) -> Optional[List[str]]:
    """
    Display an interactive individual source selector with multi-select capability.

    Args:
        stdscr: Curses window object

    Returns:
        List of selected source names, or None if quit/back
    """
    curses.curs_set(0)  # Hide cursor
    current_row = 0
    top_row = 0
    selected_sources = set()

    # Get all sources sorted by name
    all_sources = sorted(NEWS_SOURCES.keys())

    # Color setup
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Highlight
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Title
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Source
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Selected
    curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Category tag

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Header
        header = "📰 SELECT NEWS SOURCES (Multi-select)"
        stdscr.addstr(0, (width - len(header)) // 2, header, curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(1, 0, "=" * (width-1))

        instructions = "j/k: move | Space: toggle | a: all | n: none | Enter: confirm | q/ESC: back"
        stdscr.addstr(2, (width - len(instructions)) // 2, instructions)

        selected_count = f"Selected: {len(selected_sources)}/{len(all_sources)}"
        stdscr.addstr(3, (width - len(selected_count)) // 2, selected_count, curses.color_pair(4))
        stdscr.addstr(4, 0, "=" * (width-1))

        # Calculate visible range
        visible_rows = height - 7
        if current_row < top_row:
            top_row = current_row
        elif current_row >= top_row + visible_rows:
            top_row = current_row - visible_rows + 1

        # Display source options
        start_row = 5
        for idx in range(top_row, min(top_row + visible_rows, len(all_sources))):
            source_name = all_sources[idx]
            category = NEWS_SOURCES[source_name]['category']
            y_pos = start_row + (idx - top_row)

            if y_pos >= height - 2:
                break

            # Checkbox and source name
            checkbox = "[✓]" if source_name in selected_sources else "[ ]"
            display_text = f"{checkbox} {source_name[:35]}"
            category_text = f"[{category}]"

            if idx == current_row:
                stdscr.addstr(y_pos, 2, display_text,
                            curses.color_pair(1) | curses.A_BOLD)
                # Show category for highlighted item
                cat_x = min(2 + len(display_text) + 2, width - len(category_text) - 2)
                stdscr.addstr(y_pos, cat_x, category_text, curses.color_pair(5))
            else:
                color = curses.color_pair(4) if source_name in selected_sources else curses.color_pair(3)
                stdscr.addstr(y_pos, 2, display_text, color)

        # Footer
        footer = f"Source {current_row + 1}/{len(all_sources)}"
        if height > 3:
            stdscr.addstr(height-1, (width - len(footer)) // 2, footer, curses.color_pair(2))

        stdscr.refresh()

        # Handle input
        key = stdscr.getch()

        # Quit/Back
        if key in [ord('q'), ord('Q'), 27]:  # q, Q, or ESC
            return None
        # Navigation
        elif key in [ord('j'), curses.KEY_DOWN]:
            current_row = min(current_row + 1, len(all_sources) - 1)
        elif key in [ord('k'), curses.KEY_UP]:
            current_row = max(current_row - 1, 0)
        elif key in [ord('g')]:
            # gg to go to top
            next_key = stdscr.getch()
            if next_key == ord('g'):
                current_row = 0
                top_row = 0
        elif key in [ord('G')]:
            # G to go to bottom
            current_row = len(all_sources) - 1
        # Toggle selection with space
        elif key == ord(' '):
            source_name = all_sources[current_row]
            if source_name in selected_sources:
                selected_sources.remove(source_name)
            else:
                selected_sources.add(source_name)
            # Move to next item
            current_row = min(current_row + 1, len(all_sources) - 1)
        # Select all
        elif key in [ord('a'), ord('A')]:
            selected_sources = set(all_sources)
        # Select none
        elif key in [ord('n'), ord('N')]:
            selected_sources.clear()
        # Enter to confirm
        elif key in [10, 13, curses.KEY_ENTER]:  # Enter key
            if selected_sources:
                return list(selected_sources)
            else:
                # Show error or just return None
                return None


def fetch_all_articles(articles_per_source: int = 3, category_filter: Optional[str] = None,
                       source_filter: Optional[List[str]] = None) -> List[Dict]:
    """
    Fetch articles from news sources, optionally filtered by category or specific sources.

    Args:
        articles_per_source: Number of articles to fetch from each source
        category_filter: Optional category to filter by (None = all sources)
        source_filter: Optional list of specific source names to fetch from

    Returns:
        List of all fetched articles
    """
    all_articles = []
    for source_name, source_info in NEWS_SOURCES.items():
        # Skip sources based on filters
        if source_filter and source_name not in source_filter:
            continue
        if category_filter and source_info['category'] != category_filter:
            continue

        print(f"Fetching from {source_name}...", end=" ")
        articles = fetch_articles(source_info['url'], source_name, source_info['category'], articles_per_source)
        all_articles.extend(articles)
        print(f"✓ ({len(articles)} articles)")
    return all_articles


def main():
    """Main function to aggregate and display news."""
    articles_per_source = 5  # Fetch 5 articles from each source

    # Main application loop
    while True:
        try:
            # Show main menu
            print("\n📰 GLOBAL NEWS AGGREGATOR\n")
            print("Press any key to open main menu...")
            input()

            menu_choice = curses.wrapper(interactive_main_menu)

            if menu_choice is None:
                # User chose to exit
                print("\n👋 Thanks for reading! Goodbye!\n")
                break

            # Handle menu choices
            selected_category = None
            selected_sources = None
            fetch_description = ""

            if menu_choice == "categories":
                # Browse by category
                categories = get_available_categories()
                selected_category = curses.wrapper(interactive_category_selector, categories)

                if selected_category is None:
                    # User went back to main menu
                    continue

                fetch_description = f"{selected_category}"

            elif menu_choice == "sources":
                # Browse individual sources
                selected_sources = curses.wrapper(interactive_source_selector)

                if selected_sources is None:
                    # User went back to main menu or selected nothing
                    continue

                fetch_description = f"{len(selected_sources)} selected source(s)"

            elif menu_choice == "all":
                # View all sources
                fetch_description = "all sources"

            # Fetch articles based on selection
            print(f"\n🌍 Fetching news from {fetch_description}...\n")
            all_articles = fetch_all_articles(
                articles_per_source,
                category_filter=selected_category,
                source_filter=selected_sources
            )

            if not all_articles:
                print("\n❌ No articles could be fetched. Please check your internet connection.")
                print("\nPress any key to return to main menu...")
                input()
                continue

            sources_count = len(set(article['source'] for article in all_articles))
            print(f"\n✅ Successfully fetched {len(all_articles)} articles from {sources_count} sources")
            print("\n📖 Opening interactive article selector...\n")
            print("Press any key to continue...")
            input()

            # Interactive article selection loop
            article_loop_active = True
            while article_loop_active:
                try:
                    # Use curses for interactive selection
                    selected_idx = curses.wrapper(interactive_article_selector, all_articles)

                    if selected_idx is None:
                        # User quit - return to main menu
                        article_loop_active = False
                        continue
                    elif selected_idx == -1:
                        # User wants to refresh
                        print("\n🔄 Refreshing feeds...\n")
                        all_articles = fetch_all_articles(
                            articles_per_source,
                            category_filter=selected_category,
                            source_filter=selected_sources
                        )

                        if not all_articles:
                            print("\n❌ No articles could be fetched. Please check your internet connection.")
                            print("Returning to previous article list...")
                        else:
                            sources_count = len(set(article['source'] for article in all_articles))
                            print(f"\n✅ Successfully refreshed {len(all_articles)} articles from {sources_count} sources")

                        print("\nPress any key to continue...")
                        input()
                        continue

                    # User selected an article
                    selected_article = all_articles[selected_idx]

                    # Display the article
                    display_article_reader(selected_article)

                    # Ask if they want to continue
                    print("\nPress Enter to return to article list, 'm' for main menu, or 'q' to quit: ", end="")
                    try:
                        user_input = input().strip().lower()
                        if user_input == 'q':
                            print("\n👋 Thanks for reading! Goodbye!\n")
                            return
                        elif user_input == 'm':
                            # Return to main menu
                            article_loop_active = False
                    except (EOFError, KeyboardInterrupt):
                        print("\n\n👋 Thanks for reading! Goodbye!\n")
                        return

                except KeyboardInterrupt:
                    # Return to main menu on Ctrl+C
                    article_loop_active = False

        except KeyboardInterrupt:
            print("\n\n👋 Thanks for reading! Goodbye!\n")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 News aggregation interrupted. Goodbye!")
        sys.exit(0)
