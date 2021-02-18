from __future__ import annotations
from datetime import datetime, timedelta, timezone
from distutils.util import strtobool
from dotenv import dotenv_values
from loguru import logger

import fire
import iso8601
import loguru
import re
import requests
import sys
import tweepy


NUMBER = "number"
NUMBER_MAX_DAYS = 5
NUMBER_MAX_HOURS = 24 * NUMBER_MAX_DAYS
NUMBER_MAX_MINUTES = 60 * NUMBER_MAX_HOURS
NUMBER_MAX_SECONDS = 60 * NUMBER_MAX_MINUTES

UNIT = "unit"
UNIT_DAYS = "d"
UNIT_HOURS = "h"
UNIT_MINUTES = "m"
UNIT_SECONDS = "s"

DEBUG = "DEBUG"

config = {
    **dotenv_values(".env"),  # load shared development variables
    **dotenv_values(".env.secret"),  # load sensitive variables
}


def loguru_format(record: loguru.Record):
    format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | \
<level>{level: <8}</level> | \
<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}\n{exception}</level>"

    if record["extra"].get("sensitive") and not bool(
        strtobool(config.get(DEBUG) or "FALSE")
    ):
        omit_fields = []
        for field in record["extra"]:
            if field == "sensitive":
                continue
            else:
                omit_fields.append(record["extra"][field])

        record["message"] = re.sub(
            "|".join(re.escape(omit_field) for omit_field in omit_fields),
            "***redacted***",
            record["message"],
        )

    return format


logger.configure(
    handlers=[
        dict(
            sink=sys.stdout,
            diagnose=True
            if bool(strtobool(config.get(DEBUG) or "FALSE"))
            else False,
            format=loguru_format,
        ),
    ],
)


@logger.catch
def main(
    consumer_key: str,
    consumer_secret: str,
    access_token: str,
    access_token_secret: str,
    bearer_token: str,
    hashtags: frozenset[str] = frozenset(
        [
            "binit",
            "binthis",
            "bintweet",
            "junktweet",
            "rmit",
            "rmthis",
            "rmme",
            "rmtweet",
        ]
    ),
) -> None:
    """[Remove (bin) tweet after specified time from certain hashtag.
    Any tweets with specified hashtag beyond 5 days will be removed.]

    Args:
        consumer_key (str):
            Twitter API (consumer) key. Get from https://developer.twitter.com/en/portal/projects.
        consumer_secret (str):
            Twitter API (consumer) secret key. Get from https://developer.twitter.com/en/portal/projects.
        access_token (str):
            Twitter access token key. Get from https://developer.twitter.com/en/portal/projects.
        access_token_secret (str):
            Twitter access token secret key.
            Get from https://developer.twitter.com/en/portal/projects.
        bearer_token (str):
            Twitter bearer token.
            Get from https://developer.twitter.com/en/portal/projects.
        hashtags (frozenset[str]):
            A set of distinct hashtag that will be used to
            indicate which tweets to be removed (bin).
    """

    utcnow = datetime.now(timezone.utc)
    logger.info(f"bintweet starting...")
    logger.info(f"authenticating...")
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    me = api.me()

    logger.info(f"authentication is successful.")
    logger.bind(sensitive=True).info(
        "screen name: {screen_name}",
        screen_name=me.screen_name,
        name=me.name,
    )

    regex = re.compile(
        fr"#after(?P<{NUMBER}>\d)(?P<{UNIT}>[{UNIT_DAYS}{UNIT_HOURS}{UNIT_MINUTES}{UNIT_SECONDS}])"
    )

    for hashtag in hashtags:
        logger.info(f"hashtag: {hashtag}")

        query = f"query={hashtag} (from:{me.screen_name})"
        tweet_fields = "tweet.fields=text,created_at"
        max_results = "max_results=100"

        url = f"https://api.twitter.com/2/tweets/search/recent?{query}&{tweet_fields}&{max_results}"
        headers = {"Authorization": "Bearer {}".format(bearer_token)}
        response = requests.request("GET", url, headers=headers).json()

        for tweet in response.get("data") or []:
            result = regex.search(tweet["text"])
            logger.info(tweet["id"])

            if result:
                number = int(result.groupdict()[NUMBER])
                unit = result.groupdict()[UNIT]

                if unit == UNIT_HOURS:
                    if number > NUMBER_MAX_HOURS:
                        number = NUMBER_MAX_HOURS

                    removeDateTime = iso8601.parse_date(
                        tweet["created_at"]
                    ) + timedelta(hours=number)

                    if utcnow > removeDateTime:
                        logger.info(f"remove tweet {tweet['id']}")
                        api.destroy_status(tweet["id"])

                    continue
                elif unit == UNIT_DAYS:
                    if number > NUMBER_MAX_DAYS:
                        number = NUMBER_MAX_DAYS

                    removeDateTime = iso8601.parse_date(
                        tweet["created_at"]
                    ) + timedelta(days=number)

                    if utcnow > removeDateTime:
                        logger.info(f"remove tweet {tweet['id']}")
                        api.destroy_status(tweet["id"])

                    continue
                elif unit == UNIT_MINUTES:
                    if number > NUMBER_MAX_MINUTES:
                        number = NUMBER_MAX_MINUTES

                    removeDateTime = iso8601.parse_date(
                        tweet["created_at"]
                    ) + timedelta(minutes=number)

                    if utcnow > removeDateTime:
                        logger.info(f"remove tweet {tweet['id']}")
                        api.destroy_status(tweet["id"])

                    continue
                elif unit == UNIT_SECONDS:
                    if number > NUMBER_MAX_SECONDS:
                        number = NUMBER_MAX_SECONDS

                    removeDateTime = iso8601.parse_date(
                        tweet["created_at"]
                    ) + timedelta(seconds=number)

                    if utcnow > removeDateTime:
                        logger.info(f"remove tweet {tweet['id']}")
                        api.destroy_status(tweet["id"])

                    continue

            # TODO check if tweets is older than 5 days
            removeDateTime = iso8601.parse_date(
                tweet["created_at"]
            ) + timedelta(days=NUMBER_MAX_DAYS)

            if utcnow > removeDateTime:
                logger.info(f"remove tweet {tweet['id']}")
                api.destroy_status(tweet["id"])


if __name__ == "__main__":
    fire.Fire(main)
