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

# Global news sources with their RSS feeds
NEWS_SOURCES = {
    # US News Sources
    "NPR News": "https://feeds.npr.org/1001/rss.xml",
    "CBS News": "https://www.cbsnews.com/latest/rss/main",
    "NBC News": "https://feeds.nbcnews.com/nbcnews/public/news",
    "The New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
    "PBS NewsHour": "https://www.pbs.org/newshour/feeds/rss/world",

    # General International News
    "BBC World": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "The Guardian World": "https://www.theguardian.com/world/rss",
    "Deutsche Welle": "https://rss.dw.com/xml/rss-en-all",
    "France 24": "https://www.france24.com/en/rss",
    "South China Morning Post": "https://www.scmp.com/rss/91/feed",
    "The Japan Times": "https://www.japantimes.co.jp/feed/",
    "Times of India": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "ABC News Australia": "https://www.abc.net.au/news/feed/51120/rss.xml",

    # Political Science & National Security Sources
    "Council on Foreign Relations": "https://www.cfr.org/feed",
    "Foreign Policy Magazine": "https://foreignpolicy.com/feed/",
    "War on the Rocks": "https://warontherocks.com/feed/",
    "The Diplomat": "https://thediplomat.com/feed/",
    "Lawfare": "https://www.lawfaremedia.org/feed",
    "Center for Strategic & International Studies": "https://www.csis.org/analysis/feed",
    "Brookings Institution": "https://www.brookings.edu/feed/",
    "Defense One": "https://www.defenseone.com/rss/",
    "The Atlantic": "https://www.theatlantic.com/feed/all",
    "The Atlantic - Politics": "https://www.theatlantic.com/feed/channel/politics/",

    # Premium/Magazine Sources
    "The New Yorker": "https://www.newyorker.com/feed/news",
    "ProPublica": "https://www.propublica.org/feeds/propublica/main",
    "The Economist": "https://www.economist.com/rss",

    # Tech/Science
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
    "MIT Technology Review": "https://www.technologyreview.com/feed/",

    # Analysis
    "Vox": "https://www.vox.com/rss/index.xml",
}


def fetch_articles(feed_url: str, source_name: str, max_articles: int = 5) -> List[Dict]:
    """
    Fetch articles from an RSS feed.

    Args:
        feed_url: URL of the RSS feed
        source_name: Name of the news source
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
                'source': source_name
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
        output.append(f"\n[{idx}] {article['source']}")
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

            # Prepare display text
            display_text = f"[{idx+1:2d}] {article['source'][:25]:25s} | {article['title'][:width-40]}"

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


def fetch_all_articles(articles_per_source: int = 3) -> List[Dict]:
    """
    Fetch articles from all news sources.

    Args:
        articles_per_source: Number of articles to fetch from each source

    Returns:
        List of all fetched articles
    """
    all_articles = []
    for source_name, feed_url in NEWS_SOURCES.items():
        print(f"Fetching from {source_name}...", end=" ")
        articles = fetch_articles(feed_url, source_name, articles_per_source)
        all_articles.extend(articles)
        print(f"✓ ({len(articles)} articles)")
    return all_articles


def main():
    """Main function to aggregate and display news."""
    print("\n🌍 Fetching news from around the world...\n")

    articles_per_source = 5  # Fetch 5 articles from each source
    all_articles = fetch_all_articles(articles_per_source)

    if not all_articles:
        print("\n❌ No articles could be fetched. Please check your internet connection.")
        sys.exit(1)

    print(f"\n✅ Successfully fetched {len(all_articles)} articles from {len(NEWS_SOURCES)} sources")
    print("\n📖 Opening interactive article selector...\n")
    print("Press any key to continue...")
    input()

    # Interactive article selection loop
    while True:
        try:
            # Use curses for interactive selection
            selected_idx = curses.wrapper(interactive_article_selector, all_articles)

            if selected_idx is None:
                # User quit
                print("\n👋 Thanks for reading! Goodbye!\n")
                break
            elif selected_idx == -1:
                # User wants to refresh
                print("\n🔄 Refreshing feeds...\n")
                all_articles = fetch_all_articles(articles_per_source)

                if not all_articles:
                    print("\n❌ No articles could be fetched. Please check your internet connection.")
                    print("Returning to previous article list...")
                else:
                    print(f"\n✅ Successfully refreshed {len(all_articles)} articles from {len(NEWS_SOURCES)} sources")

                print("\nPress any key to continue...")
                input()
                continue

            # User selected an article
            selected_article = all_articles[selected_idx]

            # Display the article
            display_article_reader(selected_article)

            # Ask if they want to continue
            print("\nPress Enter to return to article list, or 'q' to quit: ", end="")
            try:
                user_input = input().strip().lower()
                if user_input == 'q':
                    print("\n👋 Thanks for reading! Goodbye!\n")
                    break
            except (EOFError, KeyboardInterrupt):
                print("\n\n👋 Thanks for reading! Goodbye!\n")
                break

        except KeyboardInterrupt:
            print("\n\n👋 Thanks for reading! Goodbye!\n")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 News aggregation interrupted. Goodbye!")
        sys.exit(0)
