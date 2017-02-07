# coding: utf-8
import json
import copy
import re
import os
import graph
from markdown2 import markdown
from bs4 import BeautifulSoup

from ReminderStore import ReminderStore

class Model(ReminderStore):
  def __init__(self):
    ReminderStore.__init__(self, 'AWZ')

    self.link_regexp = re.compile(r'\[([^\]]*)\]\(awz-([^)]+)\)')

    if not 'graph_state' in self:
      self['graph_state'] = json.dumps({
        'graph_history': [ 'start' ],
        'graph_index': 0,
        'connections_from': {},
        'connections_to': {}
    })
    self.state = json.loads(self['graph_state'])
    
    self.state.setdefault('graph_index', len(self.state['graph_history']) - 1)

    self.state.setdefault('connections_from', {})
    self.state.setdefault('connections_to', {})

    start_up = [ 'start', 'help' ]
    for key in start_up:
      if not key in self:
        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), key + '.md')
        if os.path.exists(filename):
          with open(filename) as file_in:
            init_string = file_in.read()
            self[key] = init_string

  def push(self, key):
    #type = 'internal' if url else 'cross'
    # Only add a new item if different from previous current
    s = self.state
    if key != s['graph_history'][s['graph_index']]:
      new_index = s['graph_index'] + 1
      new_history = s['graph_history'][:new_index]
      #new_history.append({ 'type': type, 'key': key, 'url': url, 'caret_pos': caret_pos })
      new_history.append(key)
      l = len(new_history)
      if l > 10:
        new_index -= l - 10
      if new_index < 0:
        new_index = 0
      s['graph_history'] = new_history[-10:]
      s['graph_index'] = new_index
    self.save_state()

  def save_state(self):
    self['graph_state'] = json.dumps(self.state)

  def can_move_back(self):
    return self.state['graph_index'] > 0

  def back(self):
    if self.can_move_back():
      self.state['graph_index'] = self.state['graph_index'] - 1
      self.save_state()
      return self.state['graph_history'][self.state['graph_index']]
    return None

  def can_move_forward(self):
    return self.state['graph_index'] < (len(self.state['graph_history']) - 1)

  def forward(self):
    if self.can_move_forward():
      self.state['graph_index'] = self.state['graph_index'] + 1
      self.save_state()
      return self.state['graph_history'][self.state['graph_index']]
    return None

  def list_titles(self):
    titles = []
    for key in self:
      if key == 'graph_state': continue
      titles.append(self.get_title(key))
    return titles

  def get_title(self, key):
    title = self[key]
    if not title:
      title = '# Empty'
      self[key] = title
    line_end = title.find('\n')
    if line_end > -1:
      title = title[:line_end]
    return self._flatten(title)
   
  def initialize_connections(self, key):
    self.connections_from.setdefault(key, {})
    self.connections_to.setdefault(key, {})
   
  def add_connections(self, from_key, to_key):
    self.initialize_connections(from_key)
    self.initialize_connections(to_key)
    
    self.connections_from[from_key][to_key] = True
    self.connections_to[to_key][from_key] = True
      
  def clean_old_connections(self, key):
    """ Clean out old child connections before adding updated ones - keeps the connectivity graph up to date. """
    if key in self.connections_from:
      for other_key in self.connections_from[key]:
        if other_key in self.connections_to:
          del self.connections_to[other_key][key]
      
  def is_connected(self, this, that):
    return that in self.connections_from[this] or this in self.connections_from[that]
      
  def get_neighborhood_graph(self, key, node_limit = 20):
    node_lookup = {}    
    graph_nodes = []
    tiers = []
    parent = {}
    
    self.connections_from = self.state['connections_from']
    self.connections_to = self.state['connections_to']
    
    center = graph.Node(key, self.get_title(key))
    node_lookup[key] = center
    graph_nodes.append(center)
    tiers.append([center])
    
    def add_node(from_key, to_key, on_tier):
      to_node = graph.Node(to_key, self.get_title(to_key))
      node_lookup[to_key] = to_node
      on_tier.append(to_node)
      graph_nodes.append(to_node)
      parent[to_node] = node_lookup[from_key]
    
    node_count = current_tier = 0
    while node_count < node_limit:
    #for i in range(distance):
      tier = []
      tiers.append(tier)
      for node in tiers[current_tier]:
        key = node.key
        
        # Add direct descendants
        children = self.get_children(key)
        self.clean_old_connections(key)
        for child_key in children:
          self.add_connections(key, child_key)
          if (current_tier == 0 or node_count < node_limit) and child_key not in node_lookup:
            add_node(key, child_key, tier)
            node_count += 1
          child_node = node_lookup.get(child_key, None)
          if child_node:
            node.add_edge(child_node)
            
        # Add previously seen connections, 'parent' etc.
        if (current_tier == 0 or node_count < node_limit) and key in self.connections_to:
          for other_key in self.connections_to[key]:
            if other_key not in node_lookup:
              add_node(key, other_key, tier)
              node_count += 1
            node.add_edge(node_lookup[other_key])
      current_tier += 1
      
    # Finalize with lowest tier cross-connections
    for node in tiers[current_tier]:
      key = node.key
      for other_key in self.connections_to[key]:
        if other_key in node_lookup:
          node.add_edge(node_lookup[other_key])
      for other_key in self.connections_from[key]:
        if other_key in node_lookup:
          node.add_edge(node_lookup[other_key])
          
    # Set connectivity-based importance
    # Importance = outgoing-incoming connections
    for node in graph_nodes:
      key = node.key
      self.initialize_connections(key)
      node.importance = len(self.connections_from[key]) - len(self.connections_to[key])
          
    self.state['connections_from'] = self.connections_from
    self.state['connections_to'] = self.connections_to
    
    self.save_state()
          
    return (graph_nodes, node_lookup, tiers, parent)

  def set_new(self, value = ''):
    value = self._flatten(value)
    if value == '':
      value = 'New'
    key = self.new_item('# ' + value)
    return (key, value)

  def _flatten(self, text):
    html = markdown(text).strip()
    soup = BeautifulSoup(html, "html5lib")
    return soup.get_text()

  def get_history_before_current(self):
    current_index = self.state['graph_index'] + 1
    return copy.copy(self.state['graph_history'][:current_index])

  def get_children(self, key):
    markd = self[key]
    seen = {}
    children = []
    matches = self.link_regexp.findall(markd)
    for item in matches:
      key1 = item[1]
      if not key1 in seen:
        children.append(key1)
        seen[key1] = item[0]
    changed = False
    for key2 in seen:
      title = self.get_title(key2)
      if title != seen[key2]:
        changed = True
        replacer = re.compile(r'\[([^\]]*)\]\(awz-' + key2 + '\)')
        markd = replacer.sub('[' + title + '](awz-' + key2 + ')', markd)
    if changed:
      self[key] = markd
    return children

