# main.py
import sys
from api.index import fetch_and_parse_content


def main():
    url = "https://www.dailymail.co.uk/sport/football/article-13150261/Liverpool-send-representatives-watch-Ruben-Amorim-Sporting-Jurgen-Klopp-Bayer-Leverkusen-Xabi-Alonso.html"
    html_content = fetch_and_parse_content(url)
    print(html_content)


if __name__ == "__main__":
    main()
