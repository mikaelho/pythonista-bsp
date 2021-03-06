# coding: utf-8

import model, graph, ui, copy, math, random, extend, gestures, functools, colorsys, objc_util, time
from runasync import run_async

from awz import EditorView

gesture = gestures.Gestures()

class MarginView(extend.Extender):
  margin = 5
  def size_to_fit(self):
    ui.Label.size_to_fit(self)
    self.frame = (
      self.x - self.margin,
      self.y - self.margin,
      self.width + 2 * self.margin,
      self.height + 2 * self.margin
    )

class NodeLabel(extend.Extender):
  
  def __init__(self, node):
    self.name = node.key
    self.text = node.title
    
    # Formatting
    self.alignment = ui.ALIGN_CENTER
    self.number_of_lines = 0
    self.background_color = (0.9, 1.0, 0.9, 0.9)
    #self.border_color = (0.7, 1.0, 0.7, 0.8)
    self.border_color = 'white'
    self.border_width = 2
    #self.corner_radius = 2
    self.font = ('<system>', 14) #('PingFang HK', 14)
    self.flex = 'LRTB'
    self.set_rounded(5)
    
    # Gestures    
    self.touch_enabled = True
    gesture.add_tap(self, self.tap_handler)
    gesture.add_pan(self, self.pan_handler)
    
  @objc_util.on_main_thread
  def set_rounded(self, radius):
    self.corner_radius = radius
    objc_util.ObjCInstance(self).clipsToBounds = True
    
  def tap_handler(self, data):
    self.superview.select(self.name)
    
  def pan_handler(self, data):
    self.superview.move_node(self, data.location)
    """
    if data.state == gestures.Gestures.BEGAN:
      self.pan_previous = data.translation
    if data.state == gestures.Gestures.CHANGED:
      self.superview.move_node(self, data.translation - self.pan_previous)
      self.pan_previous = data.translation
    """
  def set_colors(self, importance):
    (r, g, b) = self.heatmap_color(importance)
    self.background_color = (r, g, 0.1)
    self.text_color = 'white'
    self.tint_color = 'white'
    
  def heatmap_color(self, value):
    saturates_at = 3
    # Convert to range 0..1
    value = max(value, -saturates_at)
    value = min(value, saturates_at)
    value += saturates_at
    value /= 2.0 * saturates_at
    #value /= saturates_at
    h = 1.0 - value
    return colorsys.hls_to_rgb(h, 0.4, 0.3)

class ForceGraphView(ui.View):

  frame_duration = 1/100
  total_frames = 100
  iterations_per_frame = 10
  center_node_fixed = False

  def __init__(self, data_model):
    self.background_color = 'white'
    self.model = data_model
    self.node_lookup = {}
    #self.previous_positions = {}
    self.positions = {}
    self.fixed_nodes = set()
    self.highlighted = set()
    self.animate_duration = 0.5
    self.center_position = graph.Vector(0,0)
    
    # Gestures
    gesture.add_pinch(self, self.pinch)
    gesture.add_screen_edge_pan(self, self.back, edges = gestures.Gestures.EDGE_LEFT)
    
  def pinch(self, data):
    if data.state == gestures.Gestures.BEGAN:
      self.previous_scale = 0
    if data.state == gestures.Gestures.CHANGED:
      delta = data.scale - self.previous_scale
      if abs(delta) > 0.2:
        self.node_limit += int(3.0 * delta / abs(delta))
        #print(self.node_limit)
        self.previous_scale = data.scale
        self.focus()
    if data.state == gestures.Gestures.ENDED:
      print(data.scale)
    
  def back(self, data):
    if data.state == gestures.Gestures.BEGAN:
      key = self.model.back()
      if key:
        self.focus(key)
    
  def show_editor_view(self, data):
    if data.state == gestures.Gestures.BEGAN:
      editor_view.open_current()
      v.push_view(editor_view)
  
  def hide_editor_view(self, data):
    if data.state == gestures.Gestures.BEGAN:
      self.focus()
      v.pop_view()
     
  def draw(self):
    if self.positions and len(self.positions) > 1:
      nodes = list(self.positions.keys())
      for i in range(len(nodes) - 1):
        for j in range(i + 1, len(nodes)):
          n1 = nodes[i]
          n2 = nodes[j]
          if n2 in n1.edges:
            #pos1 = self.positions[n1]
            #pos2 = self.positions[n2]
            pos1 = self[n1.key].center
            pos2 = self[n2.key].center
            path = ui.Path()
            path.move_to(pos1.x, pos1.y)
            path.line_to(pos2.x, pos2.y)
            if n1.key in self.highlighted and n2.key in self.highlighted:
              path.line_width = 3
              ui.set_color('darkgray')
            else:
              path.line_width = 1
              ui.set_color('lightgray')
            path.stroke()
      l = self[self.selected_node_key]
      ui.set_color((0,0,0,0.1))
      for d in range(1, 6):
        #d = 3
        path = ui.Path.rounded_rect(l.x - d, l.y - d, l.width + 2 * d, l.height + 2 * d, 2 * d)
        path.fill()
  
  @run_async
  def select(self, key):
    self.selected_node_key = key
    self.set_needs_display()
    time.sleep(0.05)
    self.model.push(self.selected_node_key)
    self.focus(self.selected_node_key)
    #editor_view.open(self.selected_node_key, self)
    
  def focus(self, key = None):
    if not key: key = self.selected_node_key
    else: self.selected_node_key = key
    
    self.stop_animation()
    self.fixed_nodes = set()
    node_limit = int(self.width * self.height / 13900)

    history = self.model.get_history_before_current()
    self.highlighted = set()
    for key in history:
      self.highlighted.add(key)
    
    (graph_nodes, self.node_lookup, tiers, parent) = self.model.get_neighborhood_graph(key, node_limit)
    
    self.selected_node = self.node_lookup[key]
    
    target_bounds = (0.1 * self.width, 0.1 * self.height, 0.8 * self.width, 0.8 * self.height)
    target_center = graph.Vector(self.width/2, self.height/2)
    
    center_node = self.selected_node = tiers[0][0]
    
    if self.center_node_fixed:
      center_label = self[key]
      if center_label:
        self.center_node_position = center_label.center
        slide_vector = target_center - self.center_node_position
        distance = slide_vector.length()
        slide_vector_length = slide_vector.length()
        self.slide_unit_vector = graph.Vector(0, 0) if slide_vector_length == 0 else slide_vector / slide_vector_length
        total_units = sum(range(1, self.total_frames + 1))
        self.slide_distance_per_unit = distance / total_units
      else:
        self.positions[center_node] = target_center
        self.slide_unit_vector = graph.Vector(0, 0)
        self.slide_distance_per_unit = 0
    
    previous_positions = self.positions
    self.positions = {}
    keys = set()
    for tier in tiers:
      for node in tier:
        keys.add(node.key)
        if node in previous_positions:
          self.positions[node] = previous_positions[node]
        elif node in parent and parent[node] in previous_positions:
          self.positions[node] = previous_positions[parent[node]]
          #else:
            #self.positions[node] = (random.random(), random.random())
    #fixed_nodes = [ center_node ]
    
    self.layouter = functools.partial(graph.force_layout, graph_nodes, center_node, iterations = self.iterations_per_frame, target_bounds = target_bounds)
    
    for tier in reversed(tiers):
      for node in tier:
        l = self[node.key]
        if not l:
          l = NodeLabel(MarginView(ui.Label()), node)
          l.alpha = 0.0
          self.add_subview(l)
        l.text = node.title
        l.size_to_fit()
        l.bring_to_front()
        l.set_colors(node.importance)
        l.touch_enabled = True
          
    for l in self.subviews:
      if l.name not in keys:
        l.touch_enabled = False
        l.send_to_back()
        def fade_out():
          l.alpha = 0.0
        ui.animate(fade_out, duration = 0.3)
        
    self.frame_count = 0
    
    self.animate_layout()
    #ui.delay(self.tick, self.frame_duration)
        
  @run_async      
  def animate_layout(self):
    while self.frame_count < self.total_frames:
      self.tick()
      time.sleep(self.frame_duration)
      
  def tick(self):
    if self.center_node_fixed:
      slide_this_frame = (self.total_frames - self.frame_count) * self.slide_distance_per_unit
      self.positions[self.selected_node] += self.slide_unit_vector * slide_this_frame
    
    self.frame_count += 1
    
    self.positions = self.layouter(positions = self.positions, fixed = self.fixed_nodes)
    #self.positions = self.scaler(positions = self.positions)
    
    for node in self.positions:
      l = self[node.key]
      l.center = self.positions[node]
      l.alpha = 1.0
      
    self.set_needs_display()
    
  def move_node(self, label, location):
    self.stop_animation()
    
    loc = ui.convert_point(location, label, self)
    label.center = loc
    n = self.node_lookup[label.name]
    self.positions[n] = graph.Vector.from_pos(loc)
    self.fixed_nodes.add(n)
    self.tick()
    
  def stop_animation(self):
    ui.cancel_delays()
    self.frame_count = self.total_frames

data = model.Model()
current_key = data.get_history_before_current()[-1]

graph_view = ForceGraphView(data)
editor_view = EditorView(data, graph_view)

# Gestures for moving between main views
gesture.add_screen_edge_pan(graph_view, graph_view.show_editor_view, edges = gestures.Gestures.EDGE_RIGHT)
gesture.add_screen_edge_pan(editor_view, graph_view.hide_editor_view, edges = gestures.Gestures.EDGE_LEFT)

v = ui.NavigationView(graph_view)
v.navigation_bar_hidden = True

v.present()

graph_view.focus(current_key)

