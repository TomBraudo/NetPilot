from __future__ import annotations

import os
import re
import tempfile
from typing import List, Optional, Tuple

from .common import logger, router_connection_manager, _execute, CATEGORY_DIR


def _ensure_category_dir() -> Tuple[bool, Optional[str]]:
    out, err = _execute(f"mkdir -p {CATEGORY_DIR} 2>/dev/null || true && echo ok")
    if err or (out or '').strip() != 'ok':
        return False, err or "Failed to ensure category directory"
    return True, None


def _sanitize_category_name(category: str) -> Tuple[Optional[str], Optional[str]]:
    if not isinstance(category, str):
        return None, "Invalid category name type"
    cleaned = category.strip().lower()
    if not cleaned:
        return None, "Empty category name"
    if not re.match(r"^[a-z0-9._-]+$", cleaned):
        return None, "Category must match [a-z0-9._-]+"
    return cleaned, None


def _category_file_path(category: str) -> Tuple[Optional[str], Optional[str]]:
    cleaned, err = _sanitize_category_name(category)
    if err:
        return None, err
    return f"{CATEGORY_DIR}/{cleaned}.txt", None


def _clean_domain_line(raw_line: str) -> Optional[str]:
    if raw_line is None:
        return None
    # Strip comments and whitespace
    line = raw_line.split('#', 1)[0].strip().lower()
    if not line:
        return None
    # Drop ABP prefixes/suffixes if provided; store plain domain token
    if line.startswith('||'):
        line = line[2:]
    if line.endswith('^'):
        line = line[:-1]
    if not re.match(r"^[a-z0-9.-]+$", line):
        return None
    if re.match(r"^\d+\.\d+\.\d+\.\d+$", line):
        return None
    return line


def list_categories() -> Tuple[Optional[List[str]], Optional[str]]:
    try:
        ok, err = _ensure_category_dir()
        if not ok:
            return None, err
        out, err = _execute(f"ls -1 {CATEGORY_DIR} 2>/dev/null | sed -n 's/\\.txt$//p' | cat")
        if err:
            logger.warning(f"list_categories: ls error: {err}")
        names: List[str] = []
        for line in (out or '').splitlines():
            t = line.strip()
            if t:
                names.append(t)
        return sorted(list({n for n in names})), None
    except Exception as e:
        logger.error(f"list_categories failed: {e}", exc_info=True)
        return None, str(e)


def get_category_domains(category: str) -> Tuple[Optional[List[str]], Optional[str]]:
    try:
        path, err = _category_file_path(category)
        if err:
            return None, err
        out, err = _execute(f"cat {path} 2>/dev/null | cat")
        if err and 'No such file' in (err or ''):
            return [], None
        if err and not out:
            return None, err
        domains: List[str] = []
        for raw in (out or '').splitlines():
            dom = _clean_domain_line(raw)
            if dom:
                domains.append(dom)
        # Dedup preserve order
        seen = set()
        uniq: List[str] = []
        for d in domains:
            if d not in seen:
                seen.add(d)
                uniq.append(d)
        return uniq, None
    except Exception as e:
        logger.error(f"get_category_domains failed for {category}: {e}", exc_info=True)
        return None, str(e)


def set_category_domains(category: str, domains_or_text, mode: str = "replace") -> Tuple[Optional[dict], Optional[str]]:
    try:
        if mode not in ("replace",):
            return None, "Unsupported mode"
        path, err = _category_file_path(category)
        if err:
            return None, err

        if isinstance(domains_or_text, str):
            raw_text = domains_or_text
        elif isinstance(domains_or_text, list):
            cleaned_lines: List[str] = []
            for item in domains_or_text:
                if not isinstance(item, str):
                    continue
                dom = _clean_domain_line(item)
                if dom:
                    cleaned_lines.append(dom)
            raw_text = "\n".join(cleaned_lines) + "\n"
        else:
            return None, "domains_or_text must be string or list"

        ok, err = _ensure_category_dir()
        if not ok:
            return None, err

        with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8', newline='\n') as tf:
            tf.write(raw_text)
            tf.flush()
            local_path = tf.name
        try:
            success, copy_err = router_connection_manager.copy_file(
                local_path=local_path,
                remote_path=path,
                make_executable=False,
                normalize_crlf=True,
            )
        finally:
            try:
                os.unlink(local_path)
            except Exception:
                pass

        if not success:
            return None, copy_err or "Failed to copy category file to router"

        return {"category": category, "bytes": len(raw_text.encode('utf-8'))}, None
    except Exception as e:
        logger.error(f"set_category_domains failed for {category}: {e}", exc_info=True)
        return None, str(e)


def create_category(category: str, domains_or_text) -> Tuple[Optional[dict], Optional[str]]:
    """Create a new category file; error if exists. Content is normalized like set_category_domains."""
    try:
        path, err = _category_file_path(category)
        if err:
            return None, err
        # Check existence on router
        out, _ = _execute(f"[ -e {path} ] && echo yes || echo no")
        if (out or '').strip() == 'yes':
            return None, "category already exists"
        # Reuse set_category_domains for writing
        res, serr = set_category_domains(category, domains_or_text, mode="replace")
        if serr:
            return None, serr
        return res, None
    except Exception as e:
        logger.error(f"create_category failed for {category}: {e}", exc_info=True)
        return None, str(e)


