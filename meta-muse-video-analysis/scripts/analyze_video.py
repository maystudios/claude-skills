#!/usr/bin/env python3
"""Analyze a local video with Meta Muse Spark 1.2 Contributor.

The script intentionally uses only Python's standard library so the skill works
in fresh Codex and Claude Code environments without installing dependencies.
"""

from __future__ import annotations

import argparse
import http.client
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any


API_BASE = "https://api.meta.ai/v1"
MODEL = "muse-spark-1.2-contributor"
API_KEY_ENV = "META_MUSE_KEY"
DEFAULT_TIMEOUT_SECONDS = 3600
UPLOAD_CHUNK_SIZE = 1024 * 1024
SUPPORTED_VIDEO_EXTENSIONS = {
    ".avi",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".webm",
    ".wmv",
}


class MetaApiError(RuntimeError):
    """A sanitized Meta API failure."""


def _decode_json(payload: bytes) -> dict[str, Any]:
    if not payload:
        return {}
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        snippet = payload[:500].decode("utf-8", errors="replace")
        raise MetaApiError(f"Meta returned a non-JSON response: {snippet}") from exc
    if not isinstance(value, dict):
        raise MetaApiError("Meta returned an unexpected JSON response.")
    return value


def _error_message(status: int, payload: bytes) -> str:
    detail = payload[:2000].decode("utf-8", errors="replace").strip()
    try:
        parsed = json.loads(detail)
        if isinstance(parsed, dict):
            error = parsed.get("error")
            if isinstance(error, dict):
                detail = str(error.get("message") or error.get("code") or error)
            elif error:
                detail = str(error)
            elif parsed.get("message"):
                detail = str(parsed["message"])
    except json.JSONDecodeError:
        pass
    suffix = f": {detail}" if detail else ""
    return f"Meta API request failed with HTTP {status}{suffix}"


def _json_request(
    method: str,
    path: str,
    api_key: str,
    *,
    body: dict[str, Any] | None = None,
    timeout: int,
) -> dict[str, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        f"{API_BASE}{path}", data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return _decode_json(response.read())
    except urllib.error.HTTPError as exc:
        raise MetaApiError(_error_message(exc.code, exc.read())) from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise MetaApiError(f"Could not reach the Meta API: {reason}") from exc
    except TimeoutError as exc:
        raise MetaApiError(
            f"Meta API request timed out after {timeout} seconds."
        ) from exc


def _upload_file(video: Path, api_key: str, timeout: int) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(API_BASE)
    if parsed.scheme != "https" or not parsed.hostname:
        raise MetaApiError("The configured Meta API URL is invalid.")

    boundary = f"----meta-muse-{uuid.uuid4().hex}"
    content_type = mimetypes.guess_type(video.name)[0] or "application/octet-stream"
    safe_name = video.name.replace('"', "_")
    prefix = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="purpose"\r\n\r\n'
        "user_data\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{safe_name}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8")
    suffix = f"\r\n--{boundary}--\r\n".encode("ascii")
    content_length = len(prefix) + video.stat().st_size + len(suffix)

    connection = http.client.HTTPSConnection(
        parsed.hostname, parsed.port or 443, timeout=timeout
    )
    try:
        connection.putrequest("POST", f"{parsed.path}/files")
        connection.putheader("Authorization", f"Bearer {api_key}")
        connection.putheader("Accept", "application/json")
        connection.putheader("Content-Type", f"multipart/form-data; boundary={boundary}")
        connection.putheader("Content-Length", str(content_length))
        connection.endheaders()
        connection.send(prefix)

        sent = 0
        size = video.stat().st_size
        next_progress = 10
        with video.open("rb") as source:
            while chunk := source.read(UPLOAD_CHUNK_SIZE):
                connection.send(chunk)
                sent += len(chunk)
                if size and sent * 100 >= size * next_progress:
                    print(
                        f"Upload: {min(100, sent * 100 // size)}%",
                        file=sys.stderr,
                        flush=True,
                    )
                    next_progress += 10

        connection.send(suffix)
        response = connection.getresponse()
        payload = response.read()
        if not 200 <= response.status < 300:
            raise MetaApiError(_error_message(response.status, payload))
        return _decode_json(payload)
    except (OSError, http.client.HTTPException) as exc:
        if isinstance(exc, MetaApiError):
            raise
        raise MetaApiError(f"Video upload failed: {exc}") from exc
    finally:
        connection.close()


def _extract_output_text(response: dict[str, Any]) -> str:
    direct = response.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    fragments: list[str] = []
    output = response.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    fragments.append(text.strip())

    if fragments:
        return "\n\n".join(fragments)
    raise MetaApiError("Meta returned no textual analysis in the response.")


def _ensure_model_available(api_key: str, timeout: int) -> None:
    catalog = _json_request("GET", "/models", api_key, timeout=timeout)
    rows = catalog.get("data")
    available_ids: set[str] = set()
    if isinstance(rows, list):
        available_ids = {
            row["id"]
            for row in rows
            if isinstance(row, dict) and isinstance(row.get("id"), str)
        }
    if MODEL in available_ids:
        return

    muse_ids = sorted(
        model_id
        for model_id in available_ids
        if isinstance(model_id, str) and ("muse" in model_id or "spark" in model_id)
    )
    visible = ", ".join(muse_ids) if muse_ids else "none"
    raise MetaApiError(
        f"Model '{MODEL}' is not available for this API key. "
        f"Visible Muse/Spark models: {visible}. Enable Contributor access in the "
        "Meta developer dashboard or use an eligible key. No video was uploaded, "
        "and the tool will not fall back to a different model."
    )


def analyze_video(
    video: Path,
    prompt: str,
    api_key: str,
    *,
    timeout: int,
    keep_upload: bool,
) -> tuple[str, dict[str, Any], str, bool]:
    print(f"Checking access to {MODEL}...", file=sys.stderr, flush=True)
    _ensure_model_available(api_key, timeout)
    print(
        f"Uploading {video.name} ({video.stat().st_size / (1024 * 1024):.1f} MiB)...",
        file=sys.stderr,
        flush=True,
    )
    upload = _upload_file(video, api_key, timeout)
    file_id = upload.get("id")
    if not isinstance(file_id, str) or not file_id:
        raise MetaApiError("Meta's Files API returned no file id.")

    deleted = False
    try:
        print(f"Analyzing with {MODEL}...", file=sys.stderr, flush=True)
        response = _json_request(
            "POST",
            "/responses",
            api_key,
            body={
                "model": MODEL,
                "input": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_file", "file_id": file_id},
                            {"type": "input_text", "text": prompt},
                        ],
                    }
                ],
            },
            timeout=timeout,
        )
        analysis = _extract_output_text(response)
    finally:
        if not keep_upload:
            try:
                _json_request(
                    "DELETE", f"/files/{urllib.parse.quote(file_id)}", api_key, timeout=timeout
                )
                deleted = True
                print("Remote upload deleted.", file=sys.stderr, flush=True)
            except MetaApiError as exc:
                print(
                    f"Warning: remote upload could not be deleted: {exc}",
                    file=sys.stderr,
                    flush=True,
                )
    return analysis, response, file_id, deleted


def _resolve_prompt(args: argparse.Namespace) -> str:
    if args.prompt is not None:
        prompt = args.prompt
    elif args.prompt_file is not None:
        try:
            prompt = args.prompt_file.read_text(encoding="utf-8")
        except OSError as exc:
            raise MetaApiError(f"Could not read prompt file: {exc}") from exc
    elif not sys.stdin.isatty():
        prompt = sys.stdin.read()
    else:
        prompt = input("Analysis prompt: ")

    if not prompt.strip():
        raise MetaApiError("The analysis prompt must not be empty.")
    return prompt.strip()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            f"Analyze a local video with the fixed model {MODEL}. "
            f"The API key is read from {API_KEY_ENV}."
        )
    )
    parser.add_argument("video", type=Path, help="Path to the local video file")
    prompt_group = parser.add_mutually_exclusive_group()
    prompt_group.add_argument("--prompt", help="Free-form analysis prompt")
    prompt_group.add_argument(
        "--prompt-file", type=Path, help="UTF-8 file containing the analysis prompt"
    )
    parser.add_argument("--output", type=Path, help="Write the result to this UTF-8 file")
    parser.add_argument(
        "--json", action="store_true", help="Emit a machine-readable result envelope"
    )
    parser.add_argument(
        "--keep-upload",
        action="store_true",
        help="Do not delete the uploaded video from Meta after analysis",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Per-request timeout in seconds (default: {DEFAULT_TIMEOUT_SECONDS})",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    video = args.video.expanduser().resolve()
    if not video.is_file():
        print(f"Error: video file not found: {video}", file=sys.stderr)
        return 2
    if video.suffix.lower() not in SUPPORTED_VIDEO_EXTENSIONS:
        print(
            f"Error: unsupported video extension '{video.suffix or '(none)'}'.",
            file=sys.stderr,
        )
        return 2
    if args.timeout <= 0:
        print("Error: --timeout must be greater than zero.", file=sys.stderr)
        return 2

    api_key = os.environ.get(API_KEY_ENV, "").strip()
    if not api_key:
        print(
            f"Error: Windows environment variable {API_KEY_ENV} is not set.",
            file=sys.stderr,
        )
        return 2

    try:
        prompt = _resolve_prompt(args)
        analysis, raw_response, file_id, deleted = analyze_video(
            video,
            prompt,
            api_key,
            timeout=args.timeout,
            keep_upload=args.keep_upload,
        )
    except (MetaApiError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        rendered = json.dumps(
            {
                "model": MODEL,
                "video": str(video),
                "prompt": prompt,
                "analysis": analysis,
                "remote_file_id": file_id,
                "remote_file_deleted": deleted,
                "usage": raw_response.get("usage"),
                "response_id": raw_response.get("id"),
            },
            ensure_ascii=False,
            indent=2,
        )
    else:
        rendered = analysis

    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Saved analysis to {output}", file=sys.stderr)
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
