from __future__ import annotations

from pathlib import Path
import logging
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.constants import ErrorCode
from app.core.config import get_settings
from app.core.exceptions import NoVideoFoundError, XClientError


logger = logging.getLogger(__name__)


class XClient:
    TWEET_FIELDS = [
        "author_id",
        "attachments",
        "conversation_id",
        "created_at",
        "entities",
        "referenced_tweets",
    ]
    MEDIA_FIELDS = [
        "type",
        "url",
        "preview_image_url",
        "variants",
        "duration_ms",
        "width",
        "height",
    ]
    EXPANSIONS = [
        "attachments.media_keys",
        "referenced_tweets.id",
        "referenced_tweets.id.attachments.media_keys",
    ]

    def __init__(self) -> None:
        try:
            import tweepy
        except ModuleNotFoundError as exc:
            raise RuntimeError("tweepy is required to use XClient") from exc

        self.settings = get_settings()
        self._cached_bot_user_id = self.settings.x_bot_user_id or None
        self.last_mentions_meta: dict[str, Any] | None = None
        auth = tweepy.OAuth1UserHandler(
            self.settings.x_api_key,
            self.settings.x_api_secret,
            self.settings.x_access_token,
            self.settings.x_access_token_secret,
        )
        self.api = tweepy.API(auth)
        self.client = tweepy.Client(
            bearer_token=self.settings.x_bearer_token,
            consumer_key=self.settings.x_api_key,
            consumer_secret=self.settings.x_api_secret,
            access_token=self.settings.x_access_token,
            access_token_secret=self.settings.x_access_token_secret,
            wait_on_rate_limit=True,
        )

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    def fetch_recent_mentions(self, limit: int, since_id: str | None = None) -> list[dict[str, Any]]:
        bot_user_id = self.get_bot_user_id()
        logger.info(
            "polling X mentions bot_user_id=%s limit=%s since_id=%s",
            bot_user_id,
            min(limit, 100),
            since_id or "-",
        )
        request_kwargs: dict[str, Any] = {
            "id": bot_user_id,
            "max_results": min(limit, 100),
            "expansions": self.EXPANSIONS,
            "tweet_fields": self.TWEET_FIELDS,
            "media_fields": self.MEDIA_FIELDS,
        }
        if since_id:
            request_kwargs["since_id"] = since_id
        response = self.client.get_users_mentions(**request_kwargs)
        self.last_mentions_meta = getattr(response, "meta", None)
        logger.info("X mentions response meta=%s", self.last_mentions_meta)
        includes = self._normalize_includes(response.includes)
        tweets = response.data or []
        results: list[dict[str, Any]] = []
        for tweet in tweets:
            tweet_payload = tweet.data
            if tweet_payload.get("author_id") == bot_user_id:
                continue
            source = self._find_video_source(tweet_payload, includes)
            results.append(
                {
                    **tweet_payload,
                    "video_tweet_id": source["tweet_id"] if source else None,
                    "video_url": source["video_url"] if source else None,
                }
            )
        results = self._filter_since_id(results, since_id)
        results.sort(key=lambda item: int(item["id"]))
        logger.info(
            "fetched mentions count=%s ids=%s",
            len(results),
            [str(item["id"]) for item in results],
        )
        return results


    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    def search_recent_mentions(self, limit: int, since_id: str | None = None) -> list[dict[str, Any]]:
        bot_user_id = self.get_bot_user_id()
        username = self.settings.x_bot_username.lstrip("@").strip()
        if not username:
            raise XClientError(
                "X_BOT_USERNAME must be provided for recent search mention fallback.",
                code=ErrorCode.INTERNAL_ERROR,
                retryable=False,
            )
        query = f"@{username} -is:retweet"
        logger.info(
            "searching recent mentions query=%s limit=%s since_id=%s",
            query,
            min(limit, 100),
            since_id or "-",
        )
        request_kwargs: dict[str, Any] = {
            "query": query,
            "max_results": min(limit, 100),
            "sort_order": "recency",
            "expansions": self.EXPANSIONS,
            "tweet_fields": self.TWEET_FIELDS,
            "media_fields": self.MEDIA_FIELDS,
        }
        if since_id:
            request_kwargs["since_id"] = since_id
        response = self.client.search_recent_tweets(**request_kwargs)
        self.last_mentions_meta = getattr(response, "meta", None)
        logger.info("X recent search response meta=%s", self.last_mentions_meta)
        includes = self._normalize_includes(response.includes)
        tweets = response.data or []
        results: list[dict[str, Any]] = []
        for tweet in tweets:
            tweet_payload = tweet.data
            if tweet_payload.get("author_id") == bot_user_id:
                continue
            if not self._tweet_mentions_bot(tweet_payload, bot_user_id, username):
                continue
            source = self._find_video_source(tweet_payload, includes)
            results.append(
                {
                    **tweet_payload,
                    "video_tweet_id": source["tweet_id"] if source else None,
                    "video_url": source["video_url"] if source else None,
                }
            )
        results = self._filter_since_id(results, since_id)
        results.sort(key=lambda item: int(item["id"]))
        logger.info(
            "searched mentions count=%s ids=%s",
            len(results),
            [str(item["id"]) for item in results],
        )
        return results

    def _normalize_v1_status(self, status: Any) -> dict[str, Any] | None:
        payload = getattr(status, "_json", None) or {}
        status_id = payload.get("id_str") or str(payload.get("id")) if payload.get("id") else None
        if not status_id:
            return None
        author = payload.get("user") or {}
        author_id = author.get("id_str") or (str(author.get("id")) if author.get("id") else None)
        full_text = payload.get("full_text") or payload.get("text") or ""
        bot_user_id = self.get_bot_user_id()
        username = self.settings.x_bot_username.lstrip("@").strip()
        if author_id == bot_user_id:
            return None
        if not self._tweet_mentions_bot(
            {
                "text": full_text,
                "entities": {"mentions": self._normalize_v1_mentions(payload)},
            },
            bot_user_id,
            username,
        ):
            return None

        video_url = self._extract_video_url_from_v1_status(payload)
        quoted_id = payload.get("quoted_status_id_str")
        reply_id = payload.get("in_reply_to_status_id_str")
        video_tweet_id = status_id if video_url else quoted_id or reply_id
        return {
            "id": status_id,
            "author_id": author_id,
            "conversation_id": reply_id or quoted_id or status_id,
            "referenced_tweets": ([{"type": "quoted", "id": quoted_id}] if quoted_id else []) + ([{"type": "replied_to", "id": reply_id}] if reply_id else []),
            "entities": {"mentions": self._normalize_v1_mentions(payload)},
            "video_tweet_id": video_tweet_id,
            "video_url": video_url,
            "text": full_text,
        }

    def _normalize_v1_mentions(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        mentions = ((payload.get("entities") or {}).get("user_mentions") or [])
        normalized: list[dict[str, Any]] = []
        for mention in mentions:
            mention_id = mention.get("id_str") or (str(mention.get("id")) if mention.get("id") else None)
            normalized.append({"id": mention_id, "username": mention.get("screen_name")})
        return normalized

    def _extract_video_url_from_v1_status(self, payload: dict[str, Any]) -> str | None:
        media_items = ((payload.get("extended_entities") or {}).get("media") or [])
        for media in media_items:
            if media.get("type") not in {"video", "animated_gif"}:
                continue
            variants = ((media.get("video_info") or {}).get("variants") or [])
            best = self._pick_best_variant(variants)
            if best:
                return best
            if media.get("media_url_https"):
                return str(media["media_url_https"])
        return None

    def _filter_since_id(self, tweets: list[dict[str, Any]], since_id: str | None) -> list[dict[str, Any]]:
        if not since_id:
            return tweets
        filtered = [tweet for tweet in tweets if int(str(tweet["id"])) > int(since_id)]
        if len(filtered) != len(tweets):
            logger.info(
                "filtered stale mentions since_id=%s before=%s after=%s removed_ids=%s",
                since_id,
                len(tweets),
                len(filtered),
                [str(tweet["id"]) for tweet in tweets if int(str(tweet["id"])) <= int(since_id)],
            )
        return filtered

    def _tweet_mentions_bot(self, tweet: dict[str, Any], bot_user_id: str, username: str) -> bool:
        mentions = ((tweet.get("entities") or {}).get("mentions") or [])
        for mention in mentions:
            if str(mention.get("id")) == str(bot_user_id):
                return True
            if str(mention.get("username", "")).lower() == username.lower():
                return True
        return f"@{username.lower()}" in str(tweet.get("text", "")).lower()


    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    def search_recent_mentions_v1(self, limit: int, since_id: str | None = None) -> list[dict[str, Any]]:
        username = self.settings.x_bot_username.lstrip("@").strip()
        if not username:
            raise XClientError(
                "X_BOT_USERNAME must be provided for v1 search mention fallback.",
                code=ErrorCode.INTERNAL_ERROR,
                retryable=False,
            )
        query = f"@{username} -filter:retweets"
        logger.info(
            "searching v1 mentions query=%s limit=%s since_id=%s",
            query,
            min(limit, 100),
            since_id or "-",
        )
        statuses = self.api.search_tweets(
            q=query,
            count=min(limit, 100),
            result_type="recent",
            tweet_mode="extended",
        )
        self.last_mentions_meta = {"result_count": len(statuses), "source": "v1_search"}
        results = [self._normalize_v1_status(status) for status in statuses]
        results = [item for item in results if item is not None]
        results = self._filter_since_id(results, since_id)
        results.sort(key=lambda item: int(item["id"]))
        logger.info(
            "searched v1 mentions count=%s ids=%s",
            len(results),
            [str(item["id"]) for item in results],
        )
        return results

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    def fetch_tweet_details(self, tweet_id: str) -> dict[str, Any]:
        response = self.client.get_tweet(
            id=tweet_id,
            expansions=self.EXPANSIONS,
            tweet_fields=self.TWEET_FIELDS,
            media_fields=self.MEDIA_FIELDS,
        )
        if response.data is None:
            raise NoVideoFoundError(f"Tweet {tweet_id} not found.")
        includes = self._normalize_includes(response.includes)
        return self._enrich_tweet(response.data.data, includes)

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    def get_bot_user_id(self) -> str:
        if self._cached_bot_user_id:
            return self._cached_bot_user_id
        username = self.settings.x_bot_username.lstrip("@").strip()
        if not username:
            raise XClientError(
                "X_BOT_USER_ID or X_BOT_USERNAME must be provided.",
                code=ErrorCode.INTERNAL_ERROR,
                retryable=False,
            )
        response = self.client.get_user(username=username)
        if response.data is None or not response.data.data.get("id"):
            raise XClientError(
                f"Failed to resolve X bot user id from username: {username}",
                code=ErrorCode.INTERNAL_ERROR,
                retryable=True,
            )
        self._cached_bot_user_id = str(response.data.data["id"])
        return self._cached_bot_user_id

    def resolve_video_source(self, mention_tweet_id: str, provided_video_tweet_id: str | None = None) -> dict[str, Any]:
        mention = self.fetch_tweet_details(mention_tweet_id)
        if provided_video_tweet_id:
            tweet = self.fetch_tweet_details(provided_video_tweet_id)
            video_url = self._extract_video_url(tweet)
            if not video_url:
                raise NoVideoFoundError(f"Tweet {provided_video_tweet_id} has no video media.")
            return {**tweet, "resolved_video_tweet_id": provided_video_tweet_id, "video_url": video_url}

        source = self._find_video_source(mention, mention.get("includes", {}))
        if not source:
            source = self._find_conversation_video_source(mention)
        if not source:
            logger.info(
                "no video source found mention_tweet_id=%s conversation_id=%s referenced_tweets=%s attachments=%s",
                mention.get("id"),
                mention.get("conversation_id"),
                mention.get("referenced_tweets"),
                mention.get("attachments"),
            )
            raise NoVideoFoundError("No video found in mention, reply parent, quoted tweet, or conversation root tweet.")

        if source["tweet_id"] == str(mention["id"]):
            return {**mention, "resolved_video_tweet_id": source["tweet_id"], "video_url": source["video_url"]}

        referenced = mention.get("includes", {}).get("tweets", {}).get(source["tweet_id"])
        if referenced is None:
            tweet = self.fetch_tweet_details(source["tweet_id"])
            return {**tweet, "resolved_video_tweet_id": source["tweet_id"], "video_url": source["video_url"]}
        return {**referenced, "resolved_video_tweet_id": source["tweet_id"], "video_url": source["video_url"]}

    def _normalize_includes(self, includes: Any) -> dict[str, dict[str, dict[str, Any]]]:
        normalized = {"tweets": {}, "media": {}}
        if not includes:
            return normalized
        raw = includes if isinstance(includes, dict) else dict(includes)
        for tweet in raw.get("tweets", []) or []:
            payload = tweet.data if hasattr(tweet, "data") else tweet
            normalized["tweets"][str(payload["id"])] = payload
        for media in raw.get("media", []) or []:
            payload = media.data if hasattr(media, "data") else media
            media_key = payload.get("media_key")
            if media_key:
                normalized["media"][media_key] = payload
        return normalized

    def _enrich_tweet(self, tweet: dict[str, Any], includes: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
        return {**tweet, "includes": includes}

    def _find_video_source(self, tweet: dict[str, Any], includes: dict[str, dict[str, dict[str, Any]]]) -> dict[str, str] | None:
        current_video = self._extract_video_url(tweet, includes)
        if current_video:
            return {"tweet_id": str(tweet["id"]), "video_url": current_video}

        for ref in tweet.get("referenced_tweets") or []:
            ref_type = ref.get("type")
            if ref_type not in {"replied_to", "quoted"}:
                continue
            referenced = includes.get("tweets", {}).get(str(ref["id"]))
            if not referenced:
                continue
            video_url = self._extract_video_url(referenced, includes)
            if video_url:
                return {"tweet_id": str(ref["id"]), "video_url": video_url}
        return None

    def _find_conversation_video_source(self, mention: dict[str, Any]) -> dict[str, str] | None:
        conversation_id = mention.get("conversation_id")
        mention_id = mention.get("id")
        if not conversation_id or str(conversation_id) == str(mention_id):
            return None
        try:
            root = self.fetch_tweet_details(str(conversation_id))
        except Exception as exc:
            logger.info(
                "failed to fetch conversation root mention_tweet_id=%s conversation_id=%s error=%s",
                mention_id,
                conversation_id,
                exc,
            )
            return None
        source = self._find_video_source(root, root.get("includes", {}))
        if source:
            logger.info(
                "found video from conversation root reference mention_tweet_id=%s conversation_id=%s video_tweet_id=%s",
                mention_id,
                conversation_id,
                source["tweet_id"],
            )
            return source
        video_url = self._extract_video_url(root, root.get("includes", {}))
        if video_url:
            logger.info(
                "found video from conversation root mention_tweet_id=%s conversation_id=%s",
                mention_id,
                conversation_id,
            )
            return {"tweet_id": str(conversation_id), "video_url": video_url}
        logger.info(
            "conversation root has no video mention_tweet_id=%s conversation_id=%s attachments=%s",
            mention_id,
            conversation_id,
            root.get("attachments"),
        )
        return None

    def _extract_video_url(self, tweet: dict[str, Any], includes: dict[str, dict[str, dict[str, Any]]] | None = None) -> str | None:
        includes = includes or tweet.get("includes", {})
        media_keys = ((tweet.get("attachments") or {}).get("media_keys") or [])
        medias = [includes.get("media", {}).get(media_key) for media_key in media_keys]
        medias = [media for media in medias if media]
        for media in medias:
            media_type = media.get("type")
            if media_type not in {"video", "animated_gif"}:
                continue
            variants = media.get("variants") or []
            best = self._pick_best_variant(variants)
            if best:
                return best
            if media.get("url"):
                return str(media["url"])
        return None

    def _pick_best_variant(self, variants: list[dict[str, Any]]) -> str | None:
        mp4_variants = [
            variant
            for variant in variants
            if variant.get("content_type") == "video/mp4" and variant.get("url")
        ]
        if not mp4_variants:
            return None
        best = max(mp4_variants, key=lambda item: int(item.get("bit_rate", 0)))
        return str(best["url"])

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    def upload_video(self, video_path: Path) -> str:
        try:
            media = self.api.media_upload(filename=str(video_path), media_category="tweet_video", chunked=True)
            return str(media.media_id)
        except Exception as exc:
            raise XClientError(f"Failed to upload media: {exc}", code=ErrorCode.X_MEDIA_UPLOAD_FAILED) from exc

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    def reply_with_media(self, mention_tweet_id: str, text: str, media_id: str) -> str:
        try:
            response = self.client.create_tweet(text=text, in_reply_to_tweet_id=mention_tweet_id, media_ids=[media_id])
            return str(response.data["id"])
        except Exception as exc:
            raise XClientError(f"Failed to create reply tweet: {exc}", code=ErrorCode.X_REPLY_FAILED) from exc
