import httpx
from bs4 import BeautifulSoup
import logging
from typing import List, Dict
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

UNIVERSITY_SITES = {
    "🏛 Oliy ta'lim (Edu.uz)": "https://edu.uz/uz/news/index",
    "📰 Kun.uz Ta'lim": "https://kun.uz/news/category/talim",
    "🎓 TATU": "https://tuit.uz/all-news",
    "⚙️ TDTU": "https://tdtu.uz/category/yangiliklar/",
    "💻 Inha": "https://inha.uz/news/",
    "🇺🇿 O'zMU": "https://nuu.uz/uz/yangiliklar/",
}

async def fetch_news(uni_name: str) -> List[Dict[str, str]]:
    url = UNIVERSITY_SITES.get(uni_name)
    if not url:
        return []

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, verify=False) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            }
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                logger.error(f"Failed to fetch news from {url}: {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            potential_items = []

            # 1. Specific reliable logic for Edu.uz
            if "Edu.uz" in uni_name:
                items = soup.select('.news_card') or soup.select('.news-item')
                for it in items[:5]:
                    link = it.find('a')
                    title = it.find(class_='news_card_title') or it.find(['h3', 'h4'])
                    if link and title:
                        potential_items.append({
                            "title": title.get_text(strip=True),
                            "link": urljoin(url, link['href'])
                        })

            # 2. Specific for Kun.uz
            elif "Kun.uz" in uni_name:
                items = soup.select('.news-card, .daily-block .news')
                for it in items[:5]:
                    link = it.find('a', class_='news__title') or it.find('a')
                    if link and len(link.get_text(strip=True)) > 20:
                        potential_items.append({
                            "title": link.get_text(strip=True),
                            "link": urljoin("https://kun.uz", link['href'])
                        })

            # 3. Smart Generic Scraper for others
            if not potential_items:
                # Find all links that contain more than 30 characters of text (likely headlines)
                # and are not standard navigation links
                links = soup.find_all('a')
                seen_links = set()
                
                for link in links:
                    text = link.get_text(strip=True)
                    href = link.get('href')
                    
                    if not href or href in seen_links or len(text) < 30:
                        continue
                    
                    # Skip common non-news links
                    if any(x in href.lower() for x in ['facebook', 'telegram', 'twitter', 'instagram', 'youtube', 'contact', 'about']):
                        continue
                        
                    full_url = urljoin(url, href)
                    potential_items.append({
                        "title": text,
                        "link": full_url
                    })
                    seen_links.add(href)
                    
                    if len(potential_items) >= 5:
                        break

            return potential_items[:5]

    except Exception as e:
        logger.error(f"Error scraping news for {uni_name}: {e}")
        return []
