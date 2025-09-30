# Movie and TV Show Downloader

This script is a command-line tool for finding and downloading movies and TV shows. It searches for content on The Movie Database (TMDB) and then retrieves the video file from streaming sources.

## How It Works

The script first takes a search query from the command line to find the desired movie or TV show on TMDB. Once the correct item is found, it uses a headless browser to visit a streaming website and capture the video stream playlist (`.m3u8` file). Finally, it downloads all the video segments in parallel and stitches them together into a single video file.

## Features

-   Search for movies and TV shows from the command line.
-   Automatically selects the top search result.
-   For TV shows, you can specify the season and episode number.
-   Choose the desired video quality (e.g., 720p, 1080p).
-   Parallel segment downloading for faster speeds.
-   Displays a progress bar for the download.

## Prerequisites

Before you begin, ensure you have the following installed:
-   Python 3.6+
-   Brave Browser (the script is configured to use it by default)
-   The required Python libraries

## Installation

1.  Clone this repository or download the `main.py` script.
2.  Install the necessary Python packages using pip:

    ```shell
    pip install requests beautifulsoup4 selenium
    ```

## Usage

You can run the script from your terminal. The basic syntax is:

```shell
python main.py <title> [options]
```

**Options:**
-   `-sXXeYY`: Specify the season and episode for a TV show (e.g., `-s01e02`).
-   `-<quality>`: Specify the video quality. Options can include `1080p`, `720p`, `360p`. Defaults to `720p` if not provided.

### Examples

**To download a movie:**

```shell
python main.py "The Matrix" -1080p
```

This will search for "The Matrix", find the highest quality stream up to 1080p, and download it as `The Matrix.mp4` in a folder named `The Matrix`.

**To download a TV show episode:**

```shell
python main.py "Breaking Bad" -s02e05
```

This will search for "Breaking Bad" and download the fifth episode of the second season with the default 720p quality. The file will be saved as `Breaking Bad_S02E05.mp4` in a folder named `Breaking Bad`.

## Disclaimer

This script is intended for educational purposes only. The content downloaded may be copyrighted. Please respect the copyright laws in your country and use this tool responsibly. The developers of this script are not responsible for its misuse.
