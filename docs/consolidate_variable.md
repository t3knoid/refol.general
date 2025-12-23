# consolidate_variable

## Overview

The `consolidate_variable` module consolidates a target variable from all inventories under a **multi-inventory root** and recursively renders all Jinja2 expressions using merged role and inventory variables. It is intended for use in environments where multiple inventories exist under a single root folder.

---

## Requirements

* Python 3.6+
* Ansible 2.12+
* `jinja2` Python package

---

## Inventory Layout Support

`inventory_dir` must be a **multi-inventory root**, where each subdirectory represents a separate inventory. For example:

```
inventory/
├── test/
│   ├── group_vars/
│   └── host_vars/
└── prod/
    ├── group_vars/
    └── host_vars/
```

* The module scans all `group_vars` and `host_vars` inside each inventory subdirectory.
* Only files ending in `.yml` or `.yaml` are considered.
* **Single-inventory layouts** (e.g., `inventory/group_vars`) are **not supported**.
* If `inventory_dir` contains no subdirectories, no inventory variables will be loaded.

---

## Variables Scanning Order

1. **Role variables**: loaded from `roles_dir` under `defaults/` and `vars/`.
2. **Inventory variables**: loaded from **all subdirectories** under `inventory_dir`.
3. **Merging rules**:

   * Dictionaries are merged (values from inventory override role defaults).
   * Lists are extended.
4. **Target variable consolidation**:

   * The module searches for the target variable (e.g., `rproxy_setup_sites`) in each inventory subdirectory and merges them into a single list.

---

## Options

| Parameter       | Required | Type | Description                                                                                           |
| --------------- | -------- | ---- | ----------------------------------------------------------------------------------------------------- |
| `inventory_dir` | yes      | str  | Base directory containing multiple inventory folders. Must contain subdirectories for each inventory. |
| `roles_dir`     | no       | str  | Directory containing roles. Default is `roles`.                                                       |
| `target_var`    | yes      | str  | Name of the variable to consolidate. Must be a list-type variable.                                    |
| `debug`         | no       | bool | Enable debug output. Default `false`.                                                                 |

---

## Usage Hint

To respect the settings in `ansible.cfg` for inventory and roles directories:

```yaml
vars:
  inventory_dir_root: "{{ lookup('ansible.builtin.config','DEFAULT_HOST_LIST')[0] }}"
  roles_dir_root: "{{ lookup('ansible.builtin.config','DEFAULT_ROLES_PATH')[0] }}"
```

Then pass them to the module:

```yaml
- refol.general.consolidate_variable:
    inventory_dir: "{{ inventory_dir_root }}"
    roles_dir: "{{ roles_dir_root }}"
    target_var: rproxy_setup_sites
    debug: true
```

---

## Example Playbook

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

---

## Return Values

| Key         | Type | Description                                                  |
| ----------- | ---- | ------------------------------------------------------------ |
| `result`    | list | Fully consolidated and rendered list of the target variable. |
| `debug_log` | list | Optional debug trace output, present if `debug=true`.        |

---

## Notes

* The module **only supports multi-inventory roots**. Single inventory folders with `group_vars/` or `host_vars/` at the root level will not be processed.
* Recursive Jinja2 rendering resolves expressions using both role and inventory variables.
* This module is ideal for consolidating list-type variables like `rproxy_setup_sites` across multiple inventories.

## Testing 

Run the following smoke test to validate the consolidate_variable module.

```bash
ansible-playbook  ./tests/test_consolidate_variable.yml
```
