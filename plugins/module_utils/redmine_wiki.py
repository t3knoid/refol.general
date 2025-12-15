# plugins/module_utils/redmine_wiki.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple
import re
from urllib.parse import unquote

from ansible.module_utils.urls import fetch_url
from urllib.parse import quote


class RedmineWikiMirrorError(Exception):
    pass


def _debug(debug_enabled: bool, log: List[str], message: str):
    if debug_enabled:
        log.append(message)


def _get_json(module, url: str, headers: Dict[str, str], debug_enabled: bool, log: List[str]) -> Dict:
    _debug(debug_enabled, log, f"Fetching URL: {url}")

    resp, info = fetch_url(module, url, headers=headers)
    status = info.get("status", 0)

    _debug(debug_enabled, log, f"HTTP status: {status}")

    if status != 200:
        body = ""
        if resp is not None:
            try:
                body = resp.read().decode("utf-8", errors="replace")
            except Exception:
                body = "<unable to decode response body>"

        module.fail_json(
            msg=f"Failed to fetch URL '{url}' (status={status})",
            response_body=body,
            response_info=info,
            debug_log=log,
        )

    try:
        raw = resp.read()
        return json.loads(raw)
    except Exception as e:
        module.fail_json(
            msg=f"Failed to parse JSON from '{url}': {e}",
            debug_log=log,
        )


def _default_filename(title: str, extension: str = "md") -> str:
    safe = title.replace(" ", "_").lower()
    return f"{safe}.{extension}"


def _filename_for_title(title: str, extension: str = "md") -> str:
    """Return the filename to write for a given wiki title.

    Special-case the main wiki page (title 'wiki') to map to README.<ext>
    so repositories that consume the mirrored pages (e.g., GitHub) get
    a README as the project landing page.
    """
    if title and title.strip().lower() == "wiki":
        return f"README.{extension}"
    return _default_filename(title, extension)


def _rewrite_content(content: str, project: str, base: str, mapping: Dict[str, str]) -> str:
    """Rewrite known Redmine wiki links and wiki-style links to local filenames.

    - Rewrites absolute or relative Redmine wiki URLs to the mapped filename.
    - Rewrites wiki-style links [[Page]] or [[Page|Label]] to Markdown links.
    """

    # Replace full or site-relative Redmine wiki links
    # e.g. https://host/projects/<project>/wiki/<title>
    pattern_full = re.compile(r'https?://[^\s)\'"\]]+/projects/' + re.escape(project) + r'/wiki/([^\)\s\'"\]]+)')

    def _replace_full(m):
        enc = m.group(1)
        title = unquote(enc)
        fname = mapping.get(title) or mapping.get(enc) or _default_filename(title)
        return fname

    content = pattern_full.sub(lambda m: _replace_full(m), content)

    # Replace site-relative links: /projects/<project>/wiki/<title>
    pattern_rel = re.compile(r'/projects/' + re.escape(project) + r'/wiki/([^\)\s\'"\]]+)')

    content = pattern_rel.sub(lambda m: mapping.get(unquote(m.group(1))) or mapping.get(m.group(1)) or _default_filename(unquote(m.group(1))), content)

    # Rewrite wiki-style links [[Title]] or [[Title|Label]]
    wiki_link_re = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")

    def _wiki_link_replace(m):
        title = m.group(1).strip()
        label = m.group(2) or title
        fname = mapping.get(title) or mapping.get(quote(title, safe='')) or _default_filename(title)
        return f"[{label}]({fname})"

    # We need quote here for lookup; import inside to avoid unused if function not used
    from urllib.parse import quote

    content = wiki_link_re.sub(_wiki_link_replace, content)

    return content


def mirror_redmine_wiki(
    module,
    *,
    redmine_url: str,
    project: str,
    api_key: str,
    output_dir: str,
    delete_stale: bool = True,
    filename_extension: str = "md",
    debug_enabled: bool = False,
    rewrite_links: bool = False,
) -> Tuple[bool, List[str], List[str], List[str]]:
    """
    Returns: (changed, synced_pages, deleted_pages, debug_log)
    """
    log: List[str] = []

    headers = {"X-Redmine-API-Key": api_key}
    base = redmine_url.rstrip("/")

    index_url = f"{base}/projects/{project}/wiki/index.json"
    index = _get_json(module, index_url, headers, debug_enabled, log).get("wiki_pages", [])

    # Build title -> filename mapping for all pages up-front so links can be rewritten.
    title_to_filename: Dict[str, str] = {}
    for entry in index:
        t = entry.get("title")
        if not t:
            continue
        title_to_filename[t] = _filename_for_title(t, extension=filename_extension)

    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    _debug(debug_enabled, log, f"Output directory: {outdir}")

    changed = False
    seen_filenames = set()
    synced_pages: List[str] = []
    deleted_pages: List[str] = []

    # Mirror wiki pages
    for entry in index:
        title = entry.get("title")
        if not title:
            _debug(debug_enabled, log, "Skipping entry with no title")
            continue

        filename = _filename_for_title(title, extension=filename_extension)
        seen_filenames.add(filename)

        _debug(debug_enabled, log, f"Processing page '{title}' → {filename}")

        encoded_title = quote(title, safe="")
        page_url = f"{base}/projects/{project}/wiki/{encoded_title}.json?include=content"
        page = _get_json(module, page_url, headers, debug_enabled, log).get("wiki_page", {})
        content = page.get("text", "")

        if rewrite_links:
            try:
                content = _rewrite_content(content, project, base, title_to_filename)
            except Exception as e:
                _debug(debug_enabled, log, f"Link rewrite failed for '{title}': {e}")

        fpath = outdir / filename

        old_content = ""
        if fpath.exists():
            try:
                old_content = fpath.read_text(encoding="utf-8")
            except Exception:
                old_content = None

        if old_content != content:
            _debug(debug_enabled, log, f"Writing updated content to {fpath}")
            if not module.check_mode:
                fpath.write_text(content, encoding="utf-8")
            changed = True
            synced_pages.append(str(fpath))
        else:
            _debug(debug_enabled, log, f"No change for {fpath}")

    # Delete stale files
    if delete_stale:
        for f in outdir.glob(f"*.{filename_extension}"):
            if f.name not in seen_filenames:
                _debug(debug_enabled, log, f"Deleting stale file {f}")
                if not module.check_mode:
                    f.unlink()
                changed = True
                deleted_pages.append(str(f))

    return changed, synced_pages, deleted_pages, log
