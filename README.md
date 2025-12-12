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
