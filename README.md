# WikiJS

Ansible collection to allow management of [Wiki.js](https://github.com/requarks/wiki/) data.

## Requirements

Python 3.7+ (currently only tested on Python 3.12)

My Python client API for Wiki.js `pip install git+https://github.com/tombayo/python-wikijs`

## Install

`ansible-galaxy collection install git+https://github.com/tombayo/tombayo.wikijs`

## Examples

### Create a page

```yaml
  - name: Create a page
    tombayo.wikijs.page:
    api_url: "{{ wikijs_api_url }}"
    api_key: "{{ wikijs_api_key }}"
    path: testing/testpage
    title: My page about a Topic
    description: This page contains information about the Topic.
    content: |
        # Topic
        This is a markdown-formatted document describing the Topic.

    register: my_new_page

  - name: Logging page ID
    ansible.builtin.debug:
    msg: "The ID of my new page is: {{ my_new_page.page.id }}"
```

### Update a page

```yaml
  - name: Update a page
    tombayo.wikijs.page:
    api_url: "{{ wikijs_api_url }}"
    api_key: "{{ wikijs_api_key }}"
    id: "{{ my_new_page.page.id }}"
    path: testing/testpage
    title: My page about a Topic
    description: This page changed the information about the Topic.
    content: |
        # Topic
        This is a markdown-formatted document describing the Topic.
        Now different than when initially created.
```
