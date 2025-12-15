# redmine_wiki_mirror

## Overview

The `redmine_wiki_mirror` module mirrors Redmine wiki pages from a single project into a local directory. It performs a one-way sync where Redmine is the source of truth: pages are created or updated locally to match Redmine, and local files not present in Redmine can be removed when `delete_stale` is enabled.

The module is suitable for exporting project documentation from Redmine into a repository or documentation build pipeline.

---

## Requirements

* Python 3.6+
* Ansible (module runs under Ansible's Python)
* `fetch_url` available via `ansible.module_utils.urls` (bundled with Ansible)

---

## Behavior Summary

- Fetches the wiki index for a project via the Redmine REST API (`/projects/<project>/wiki/index.json`).
- Fetches each wiki page content (`/projects/<project>/wiki/<title>.json?include=content`) and writes files to `output_dir`.
- Filenames are derived from page titles by lowercasing and replacing spaces with underscores; a `filename_extension` is appended (default `md`).
- If `delete_stale` is true, files in `output_dir` that do not correspond to any current Redmine wiki page are removed.
- The module respects `check_mode`: file writes and deletions are skipped while `changed` is still reported.

---

## Options

| Parameter           | Required | Type  | Default | Description |
| ------------------- | -------- | ----- | ------- | ----------- |
| `redmine_url`       | yes      | str   | —       | Base URL of the Redmine instance (e.g. `https://redmine.example.com`). |
| `project`           | yes      | str   | —       | Redmine project identifier (name or id). |
| `api_key`           | yes      | str   | —       | Redmine API key for authentication. Marked `no_log` by the module. |
| `output_dir`        | yes      | str   | —       | Local directory to write mirrored wiki files. Directory will be created if necessary. |
| `delete_stale`      | no       | bool  | `true`  | When `true`, files in `output_dir` not present in Redmine are deleted. |
| `filename_extension`| no       | str   | `md`    | File extension to use for written files (without leading dot). |
| `debug`             | no       | bool  | `false` | Enable verbose debug logging; messages are returned in `debug_log`. |
| `rewrite_links`     | no       | bool  | `false` | Rewrite internal Redmine wiki links and wiki-style links to point at the mirrored filenames. |

---

## Example Playbook

```yaml
- hosts: localhost
  gather_facts: false
  tasks:
    - name: Mirror Redmine wiki into docs
      refol.general.redmine_wiki_mirror:
        redmine_url: "https://redmine.example.com"
        project: myproject
        api_key: "{{ lookup('env','REDMINE_API_KEY') }}"
        output_dir: "{{ playbook_dir }}/docs/redmine"
        delete_stale: true
        filename_extension: "md"
        debug: true
      register: redmine_mirror

    - name: Show mirror details
      debug:
        var: redmine_mirror
```

---

## Returned Values

| Key          | Type   | Description |
| ------------ | ------ | ----------- |
| `changed`    | bool   | Whether any file writes or deletions occurred (subject to `check_mode`). |
| `synced_pages`| list  | Paths of files created or updated during the run. |
| `deleted_pages`| list | Paths of files deleted when `delete_stale` is true. |
| `debug_log`  | list   | Debug messages collected when `debug=true`. Always returned. |

---

## Notes and Implementation Details

- Filenames: The module generates filenames via a simple normalization: spaces are replaced with underscores and the title is lowercased (`My Page` → `my_page.md`). This is implemented in the utility `_default_filename()`.
- HTTP: The module uses `fetch_url` (via `ansible.module_utils.urls.fetch_url`) and expects a JSON API from Redmine endpoints. Errors fetching or parsing JSON will cause the module to fail with helpful debug information when `debug` is enabled.
- Check mode: When Ansible runs in check mode, the module will report `changed` where it would have written or deleted files, but will not perform filesystem changes.
- Authentication: Provide a valid Redmine API key via `api_key`. The module sends it as `X-Redmine-API-Key` in request headers.

---

## Troubleshooting

- If pages are missing, confirm the `project` value and that the API key has permission to read the project's wiki.
- If JSON parsing fails, check the Redmine instance for non-standard responses or authentication issues; enabling `debug` will capture HTTP status and response body (when available).

## Link rewriting behavior

- When `rewrite_links` is enabled the module will rewrite internal Redmine wiki links to point at the mirrored filenames. This covers full Redmine wiki URLs (absolute and site-relative) and wiki-style links like `[[Title]]` or `[[Title|Label]]`.
- The project's main wiki page (title `wiki`) is mapped to `README.<filename_extension>`, so links targeting the main wiki will refer to the local README after mirroring.
