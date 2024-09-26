#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = """
module: page
short_description: Manage Wiki.js Pages
description:
    - Create, delete, or update Wiki.js pages
    - You need to supply the API-endpoint and an API-key
author: "Tom Andre Munkhaug (@tombayo)"
options:
  api_url:
    type: str
    required: true
    description:
      - The url to the Wiki.js api endpoint
  api_key:
    type: str
    required: true
    description:
      - API key for authenticating with wiki.js
  state:
    type: str
    description:
      - Can either be `present` or `absent`.
      - `present` will update or create a page.
      - `absent` will delete a page. 
    default: present
  id:
    type: int
    description:
      - The Wiki.js internal identificator for a page.
      - Is required if no `path` is specified
  title:
    type: str
    description:
      - The title of the page.
  description:
    type: str
    description:
      - The description of the page.
  content:
    type: str
    required: true
    description:
      - The content of the page. Must be of valid syntax given by `editor`.
  path:
    type: str
    description:
      - The virtual path of the page.
      - Can be omitted if `id` is present instead.
      - `id` must be present when changing the path of a page.
  editor:
    type: str
    default: markdown
    description:
      - The type or editor of the page.
      - Can be either `markdown`, `asciidoc`, or `code`. The latter is raw HTML.
      - `content` provided must have valid syntax from this attribute.
  isPrivate:
    type: bool
    default: False
    description:
      - Whether or not to keep the page private.
  isPublished:
    type: bool
    default: True
    description:
      - Whether or not to publish the page.
  locale:
    type: str
    default: en
    description:
      - The locale of the page.
  publishEndDate:
    type: str
    description:
      - Date when the page is no longer published.
  publishStartDate:
    type: str
    description:
      - Date when the page starts to be published.
  scriptCss:
    type: str
    description:
      - Not sure what this does, please refer to the Wiki.js documentation.
  scriptJs:
    type: str
    description:
      - Not sure what this does, please refer to the Wiki.js documentation.
  tags:
    type: list
    description:
      - List of tags to apply to the page
"""

EXAMPLES = """
- name: Create a page
  tombayo.wikijs.page:
    api_url: "{{ wikijs_api_url }}"
    api_key: "{{ wikijs_api_key }}"
    path: mytopic/mypage
    title: My page about a Topic
    description: This page contains information about the Topic.
    content: |
      # Topic
      This is a markdown-formatted document describing the Topic.

  delegate_to: localhost
  register: my_new_page

- debug:
  msg: "The ID of my new page is: {{ my_new_page.page.id }}"

"""

import traceback
from ansible.module_utils.basic import AnsibleModule

from ..module_utils.api import api_argspec

try:
    from wikijs import WikiJs
    from wikijs import exceptions as WikiJsExceptions
except ImportError:
    HAS_ANOTHER_LIBRARY = False
    ANOTHER_LIBRARY_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_ANOTHER_LIBRARY = True
    ANOTHER_LIBRARY_IMPORT_ERROR = False

def _param_converter(module: AnsibleModule) -> dict:
    """Converts the parameters of an `AnsibleModule` to a dictionary 
    that can be used for functions in `WikiJs`."""
    params = dict()
    # Only add non-None values:
    for key in module.params.keys():
        if module.params[key] is not None:
            params[key] = module.params[key]

    # Remove params we cant pass to WikiJs:
    del(params['api_url'])
    del(params['api_key'])
    del(params['state'])

    return params

def _find_page_by_path(module: AnsibleModule, wikijs: WikiJs) -> int:
    """Returns the ID of page with path as defined in `module.params['path']`."""

    try:
      page = wikijs.fetch_page_by_path(module.params['path'], module.params['locale'])
    
    except WikiJsExceptions.PageNotFound:
        # Page does not exist, which is exactly what we're checking.
        # Any other Exceptions will bubble up.
        return 0

    return int(page['id'])

def _create_page(module: AnsibleModule, wikijs: WikiJs) -> int:
    params = _param_converter(module)
    if 'id' in params.keys():
        del(params['id'])

    try:
        page = wikijs.create_page(**params)
    except Exception as e:
        return {'msg':f"Failed to create page {params['path']}", 'exception':type(e).__name__, 'debug':traceback.format_exc()}
    
    return {'msg':f"Created page with path {page['path']} - got id {page['id']}.",'changed':True, 'page':page}

def _update_page(module: AnsibleModule, wikijs: WikiJs, id: int) -> int:
    params = _param_converter(module)
    params['id'] = id

    try:
        oldpage = wikijs.fetch_page(id)
        
        tags = list(set(params['tags']) - set(oldpage['tags']))
        del(params['tags'])
        del(oldpage['tags']) # Remove tags for the below operation

        stripped = dict(params.items() - oldpage.items()) # Remove identical entries

        if len(tags) > 0:
            stripped['tags'] = tags # Re-add the tags if they're different

        if len(stripped) == 0:
            return {
                'msg':f"No need to update page.",
                'changed':False,
                'page':oldpage,
                'oldpage':oldpage,
                'incomingpage':params,
                'changes':stripped
            }

        if ('path' in stripped.keys() or 'locale' in stripped.keys()):
            # if either path or locale changes, we need to move:
            page = wikijs.move_page(id, stripped['path'], stripped['locale'])

        page = wikijs.update_page(id, **stripped)

    except Exception as e:
        return {'msg':f"Failed to update page with id {id}", 'exception':type(e).__name__, 'debug':traceback.format_exc()}
    
    return {
        'msg':f"Updated page with id {id} and path {params['path']}.",
        'changed':True,
        'page':page,
        'oldpage':oldpage,
        'incomingpage':params,
        'changes':stripped
    }

def main():
    module_args = dict(
        state=dict(default='present', choices=['present','absent']),
        id=dict(type='int'),
        title=dict(),
        description=dict(),
        content=dict(),
        path=dict(),
        editor=dict(default='markdown', choices=['markdown','asciidoc','code']),
        isPrivate=dict(type='bool', default=False),
        isPublished=dict(type='bool', default=True),
        locale=dict(default='en'),
        publishEndDate=dict(),
        publishStartDate=dict(),
        scriptCss=dict(),
        scriptJs=dict(),
        tags=dict(type='list', elements='str', default=[])
    )
    module = AnsibleModule(argument_spec={**module_args, **api_argspec}, supports_check_mode=False)

    if not HAS_ANOTHER_LIBRARY:
        module.fail_json(msg="Missing library dependency", exception=ANOTHER_LIBRARY_IMPORT_ERROR)

    wikijs = WikiJs(module.params['api_url'], module.params['api_key'], False)

    id = module.params['id'] or _find_page_by_path(module, wikijs)

    if not id:
        result = _create_page(module, wikijs)
    else:
        result = _update_page(module, wikijs, id)

    if 'exception' in result.keys():
        module.fail_json(**result)

    module.exit_json(**result)

if __name__ == '__main__':
    main()