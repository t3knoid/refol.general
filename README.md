# refol.general

`refol.general` is an Ansible Collection containing general-purpose modules, including `consolidate_variable`, which consolidates list-type variables from multiple inventories and renders Jinja2 expressions recursively.

This collection is ideal for environments with multiple inventories under a single root directory.

---

## Building

Build the collection from source:

```bash
ansible-galaxy collection build ../refol.general
```

This creates a `refol-general-0.0.1.tar.gz` file.

---

## Installation

Install the collection from a local build or Galaxy:

```bash
# From local build
ansible-galaxy collection install ./refol-general-0.0.1.tar.gz

# From Galaxy (if published)
ansible-galaxy collection install refol.general
```

When running playbooks that reference the collection's modules without setting `ANSIBLE_LIBRARY` or
`ANSIBLE_MODULE_UTILS` environment variables, ensure your `ansible.cfg` includes the collection's
plugin paths. Add the following to the `[defaults]` section of `ansible.cfg` if you install the
collection into the default user collection path (`~/.ansible/collections`):

```ini
# (pathspec) Colon-separated paths in which Ansible will search for Modules.
library=~/.ansible/collections/ansible_collections/refol/general/plugins/modules:

# (pathspec) Colon-separated paths in which Ansible will search for Module utils files, which are shared by modules.
module_utils=~/.ansible/collections/ansible_collections/refol/general/plugins/module_utils
```

If you're developing in-tree (running modules from the repository), you can alternatively set the
environment variables for the run instead of modifying `ansible.cfg`:

```bash
export ANSIBLE_LIBRARY=./plugins/modules
export ANSIBLE_MODULE_UTILS=./plugins/module_utils
```

## Verify the installation

Run the following to show that the collection has been installed.

```bash
ansible-galaxy collection list refol.general
```

---

## Module: consolidate_variable

### Overview

The `consolidate_variable` module consolidates a list-type variable (e.g., `rproxy_setup_sites`) from **all sub-inventories** under a multi-inventory root and recursively renders Jinja2 expressions using merged role and inventory variables.

---

### Requirements

* Python 3.6+
* Ansible 2.12+
* `jinja2` Python package

---

### Inventory Layout

The module requires a **multi-inventory root**, where each subdirectory represents a separate inventory:

```
inventory/
├── test/
│   ├── group_vars/
│   └── host_vars/
└── prod/
    ├── group_vars/
    └── host_vars/
```

* Single-inventory roots are **not supported**.
* Only `.yml` and `.yaml` files are considered.

---

### Module Options

| Parameter       | Required | Type | Description                                                                                           |
| --------------- | -------- | ---- | ----------------------------------------------------------------------------------------------------- |
| `inventory_dir` | yes      | str  | Base directory containing multiple inventory folders. Must contain subdirectories for each inventory. |
| `roles_dir`     | no       | str  | Directory containing roles. Default is `roles`.                                                       |
| `target_var`    | yes      | str  | Name of the variable to consolidate. Must be a list-type variable.                                    |
| `debug`         | no       | bool | Enable debug output. Default `false`.                                                                 |
| `rewrite_links` | no | bool | Rewrite Redmine wiki links and wiki-style links to local filenames. Default `false`. |

---

### Usage Hint

Use `ansible.cfg` defaults to set inventory and roles paths:

```yaml
vars:
  inventory_dir_root: "{{ lookup('ansible.builtin.config','DEFAULT_HOST_LIST')[0] }}"
  roles_dir_root: "{{ lookup('ansible.builtin.config','DEFAULT_ROLES_PATH')[0] }}"
```

---

### Example Playbook

```yaml
- hosts: localhost
  gather_facts: false
  vars:
    inventory_dir_root: "{{ lookup('ansible.builtin.config','DEFAULT_HOST_LIST')[0] }}"
    roles_dir_root: "{{ lookup('ansible.builtin.config','DEFAULT_ROLES_PATH')[0] }}"
  tasks:
    - name: Consolidate rproxy_setup_sites
      refol.general.consolidate_variable:
        inventory_dir: "{{ inventory_dir_root }}"
        roles_dir: "{{ roles_dir_root }}"
        target_var: rproxy_setup_sites
        debug: true
      register: result

    - name: Show consolidated result
      debug:
        var: result
```

### Testing 

Run the following smoke test to validate the consolidate_variable module.

```bash
ansible-playbook  ./tests/test_consolidate_variable.yml
```

---

### Return Values

| Key         | Type | Description                                                  |
| ----------- | ---- | ------------------------------------------------------------ |
| `result`    | list | Fully consolidated and rendered list of the target variable. |
| `debug_log` | list | Optional debug trace output if `debug=true`.                 |

---

### Notes

* Only supports **multi-inventory roots**. Single-inventory folders will not be processed.
* Recursively renders Jinja2 expressions using merged inventory and role variables.
* Ideal for consolidating list-type variables such as `rproxy_setup_sites` across multiple inventories.

---

## Module: redmine_wiki_mirror

### Overview

The `redmine_wiki_mirror` module mirrors Redmine wiki pages for a project into a local directory. It is intended for exporting project wiki content from Redmine into a repository or documentation build pipeline. The module treats Redmine as the source of truth and will create, update, or (optionally) delete local files to match the wiki state.

---

### Requirements

* Python 3.6+
* Ansible (module runs under Ansible's Python runtime and uses `ansible.module_utils.urls.fetch_url`)

---

### Module Options

| Parameter           | Required | Type  | Description                                                  |
| ------------------- | -------- | ----- | ------------------------------------------------------------ |
| `redmine_url`       | yes      | str   | Base URL of the Redmine instance (e.g. `https://redmine.example.com`) |
| `project`           | yes      | str   | Redmine project identifier (name or id)                      |
| `api_key`           | yes      | str   | Redmine API key for authentication (marked `no_log` by the module) |
| `output_dir`        | yes      | str   | Local directory to write mirrored wiki files (created if missing) |
| `delete_stale`      | no       | bool  | Remove files in `output_dir` that are not present in Redmine. Default `true`. |
| `filename_extension`| no       | str   | File extension to use for written files (default `md`)       |
| `debug`             | no       | bool  | Enable verbose debug logging; messages are returned in `debug_log`. Default `false`. |

| `rewrite_links`     | no       | bool  | Rewrite Redmine wiki links and wiki-style links to local filenames. Default `false`. |

---

### Example Playbook

```yaml
- hosts: localhost
  gather_facts: false
  tasks:
    - name: Mirror Redmine wiki into docs
      refol.general.redmine_wiki_mirror:
        redmine_url: "https://redmine.example.com"
        project: myproject
        api_key: "{{ lookup('env','REDMINE_API_KEY') }}"
        output_dir: ./docs/redmine
        delete_stale: true
        filename_extension: md
        debug: true
      register: mirror_result

    - name: Show mirror result
      debug:
        var: mirror_result
```

---

### Testing

Run the included smoke playbook to verify the module. The test playbook is `tests/test_redmine_wiki_mirror.yml` and writes output to `tests/tmp_redmine_wiki` by default.

Quick syntax check (no network calls):

```bash
ansible-playbook --syntax-check tests/test_redmine_wiki_mirror.yml
```

Run the test using an installed collection (no env overrides needed if your `ansible.cfg` has the correct `collections_paths`):

```bash
export REDMINE_URL="https://homelab.refol.us"
export REDMINE_PROJECT="home-lab"
export REDMINE_API_KEY="<your_api_key>"
ansible-playbook tests/test_redmine_wiki_mirror.yml
```

If you're developing in-tree and want to run the test against the local `plugins/` folders (without installing the collection), either set these environment variables for the run:

```bash
export ANSIBLE_LIBRARY=./plugins/modules
export ANSIBLE_MODULE_UTILS=./plugins/module_utils
export REDMINE_URL="https://homelab.refol.us"
export REDMINE_PROJECT="home-lab"
export REDMINE_API_KEY="<your_api_key>"
ansible-playbook tests/test_redmine_wiki_mirror.yml
```

Or add the local plugin paths to `ansible.cfg` in the repo root (see notes above) so Ansible discovers them automatically.

Cleanup after running the test

To remove the temporary files written by the smoke test:

```bash
rm -rf tests/tmp_redmine_wiki
```

Or remove only the files that were synced in the last run by inspecting `mirror_result.synced_pages` in the playbook output and deleting those paths.

### Return Values

| Key           | Type  | Description                                      |
| ------------- | ----- | ------------------------------------------------ |
| `changed`     | bool  | Whether files were created, updated, or deleted  |
| `synced_pages`| list  | Paths of files created or updated during the run |
| `deleted_pages`| list | Paths of files deleted when `delete_stale` is true |
| `debug_log`   | list  | Debug messages collected when `debug=true` (always returned) |

---
