import re
import time
from collections import defaultdict
import concurrent.futures

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException

import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager
import spotipy
from spotipy.oauth2 import SpotifyOAuth

BASE_URL = "https://www.onepeloton.com/classes/cycling/"
CLASS_URL_PATTERN = re.compile(
    r"https://www\.onepeloton\.com/classes/cycling/\d+-min-[a-z0-9-]+-[a-z-]+-[a-z-]+-\w+"
)

def get_spotify_top_artists():
    print("Connecting to Spotify...")
    scope = "user-top-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
    results = sp.current_user_top_artists(limit=25, time_range='short_term')
    top_artists = [artist['name'].lower() for artist in results['items']]
    print("Top Artists:", top_artists)
    return top_artists

def match_classes_to_artists(class_playlists, top_artists):
    matched = defaultdict(list)
    for url, playlist in class_playlists.items():
        for title, artist in playlist:
            if any(fav in artist.lower() for fav in top_artists):
                matched[url].append((title, artist))
    return matched

def extract_playlist_from_public(driver, url):
    print(f"Opening class: {url}")
    driver.get(url)
    playlist = []
    try:
        view_more = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "playlist-accordion")))
        if view_more.get_attribute("aria-expanded") == "false":
            driver.execute_script("arguments[0].click();", view_more)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "song-title-0")))
    except:
        pass

    index = 0
    while True:
        try:
            title = driver.find_element(By.ID, f"song-title-{index}").text.strip()
            artist = driver.find_element(By.ID, f"song-artists-{index}").text.strip()
            playlist.append((title, artist))
            index += 1
        except:
            break

    return playlist

def extract_playlist_from_member(driver, href):
    driver.execute_script(f"window.open('{href}', '_blank');")
    driver.switch_to.window(driver.window_handles[1])
    playlist = []

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//li[@data-test-id='playlistSong']"))
        )
        songs = driver.find_elements(By.XPATH, "//li[@data-test-id='playlistSong']")
        for song in songs:
            title = song.find_element(By.XPATH, ".//strong").text
            artist = song.find_element(By.XPATH, ".//span").text
            playlist.append((title, artist))
    except:
        print("No visible playlist found")

    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    time.sleep(2)
    return playlist

def print_recommendations(matched):
    print("\nRecommended Classes Based on Your Spotify Artists:")
    for url, songs in sorted(matched.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"{url}")
        for title, artist in songs:
            print(f"   {title} — {artist}")
        print()

def fetch_playlist_pair(driver_path, url):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(driver_path), options=options)

    try:
        playlist = extract_playlist_from_public(driver, url)
    except Exception as e:
        print(f"Error with {url}: {e}")
        playlist = []
    finally:
        driver.quit()
    return url, playlist

def public_mode():
    print("Running in PUBLIC mode")
    top_artists = get_spotify_top_artists()

    valid_duration_filters = ["5-10mins", "15-20mins", "30-45mins", "60mins-up"]
    while True:
        print("Available class durations:")
        for i, duration in enumerate(valid_duration_filters):
            print(f"{i + 1}. {duration}")
        user_input = input("Enter the number corresponding to the desired class duration: ").strip()
        try:
            idx = int(user_input) - 1
            if 0 <= idx < len(valid_duration_filters):
                duration_filter = valid_duration_filters[idx]
                break
            else:
                print("Invalid number.")
        except ValueError:
            print("Please enter a number.")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(BASE_URL + duration_filter)

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
    except Exception as e:
        print(f"Timeout: {e}")
        driver.quit()
        return

    anchors = driver.find_elements(By.TAG_NAME, "a")
    links = set()
    for anchor in anchors:
        try:
            href = anchor.get_attribute("href")
            if href and CLASS_URL_PATTERN.match(href):
                links.add(href)
        except Exception:
            continue
    driver_path = driver.service.path
    driver.quit()

    # Process only the top 10 classes found
    links_list = list(links)[:10]
    print(f"Extracting playlists from {len(links_list)} classes in parallel...")
    class_playlists = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(fetch_playlist_pair, driver_path, url): url for url in links_list}
        for future in concurrent.futures.as_completed(future_to_url):
            url, playlist = future.result()
            class_playlists[url] = playlist

    matched = match_classes_to_artists(class_playlists, top_artists)
    print_recommendations(matched)

def member_mode():
    print("Running in MEMBER mode")
    top_artists = get_spotify_top_artists()

    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = uc.Chrome(version_main=136, options=options)

    driver.get("https://members.onepeloton.com/classes/cycling")
    input("Log in manually, then press ENTER to continue...")

    try:
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))).click()
    except:
        print("No cookie banner found")

    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/classes/cycling?modal=classDetailsModal')]"))
    )
    class_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/classes/cycling?modal=classDetailsModal')]")

    class_playlists = {}
    for i, class_link in enumerate(class_links[:10]):
        href = class_link.get_attribute("href")
        print(f"\nClass {i + 1} — Extracting playlist from {href}")
        class_playlists[href] = extract_playlist_from_member(driver, href)

    driver.quit()

    matched = match_classes_to_artists(class_playlists, top_artists)
    print_recommendations(matched)

def main():
    mode = input("Choose mode (public/member): ").strip().lower()
    if mode == "public":
        public_mode()
    elif mode == "member":
        member_mode()
    else:
        print("Invalid mode. Please type 'public' or 'member'.")

if __name__ == "__main__":
    main()