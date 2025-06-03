# Spotify to Peloton Class Matcher

This Python script connects to your Spotify account to retrieve your top artists and then scrapes Peloton cycling classes to find classes that feature songs by those artists.

## Features

-   Retrieve your top artists from Spotify.
-   Scrape Peloton public or member site for cycling class playlists.
-   Match classes with songs by your top artists.
-   Recommend classes based on the number of matched songs by your favorite artists.

## Prerequisites

-   Python 3.6 or higher
-   A Spotify account
-   A Peloton account (optional, for member mode)
-   Google Chrome browser installed

## Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd spotify-to-peloton
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Spotify API credentials:**

    -   Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
    -   Log in and create a new application.
    -   Note down your `Client ID` and `Client Secret`.
    -   Edit the application settings and add `http://localhost:8888/callback` as a Redirect URI.
    -   Create a `.env` file in the project root directory with the following content:

        ```env
        SPOTIPY_CLIENT_ID='YOUR_CLIENT_ID'
        SPOTIPY_CLIENT_SECRET='YOUR_CLIENT_SECRET'
        SPOTIPY_REDIRECT_URI='http://127.0.0.1:8888/callback'
        ```
        Replace `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` with your actual Spotify API credentials.

## Usage

1.  **Run the script:**

    ```bash
    python spotify_peloton_combined.py
    ```

2.  **Choose a mode:**

    The script will prompt you to choose between `public` and `member` mode.

    -   **Public Mode:** Scrapes publicly available class information. You will be asked to select a class duration filter.
    -   **Member Mode:** Requires manual login to the Peloton member site through the opened browser window. It can access more detailed information, potentially including playlists for classes not publicly listed.

3.  **Follow the prompts:**

    -   For Spotify authentication, a browser window will open. Log in and authorize the application.
    -   In member mode, a browser window will open for Peloton login. Log in manually and then press ENTER in the terminal to continue.

The script will then extract class playlists, match them against your top Spotify artists, and print recommendations.
