# coding: utf-8
import collections, math, random, numbers

class Vector(collections.namedtuple('Vector', ('x', 'y'))):
  __slots__ = ()

  @classmethod
  def from_pos(cls, pos_tuple):
    return cls(pos_tuple[0], pos_tuple[1])
  
  def from_to(pos1, pos2):
    return Vector.from_pos(pos2) - Vector.from_pos(pos1)

  def __abs__(self):
      return type(self)(abs(self.x), abs(self.y))

  def __int__(self):
      return type(self)(int(self.x), int(self.y))

  def __add__(self, other):
      return type(self)(self.x + other.x, self.y + other.y)

  def __sub__(self, other):
      return type(self)(self.x - other.x, self.y - other.y)

  def __mul__(self, other):
      return type(self)(self.x * other, self.y * other)

  def __truediv__(self, other):
      return type(self)(self.x / other, self.y / other)

  def dot_product(self, other):
      return self.x * other.x + self.y * other.y

  def distance_to(self, other):
      """ uses the Euclidean norm to calculate the distance """
      return (other - self).length()
      #return hypot((self.x - other.x), (self.y - other.y))
      
  def length(self):
    return math.hypot(self.x, self.y)

class Node():
  def __init__(self, key, title = 'Empty', importance = 0):
    self.key = key
    self.title = title
    self.edges = set()
    self.importance = importance
  def add_edge(self, other_node):
    self.edges.add(other_node)
    other_node.edges.add(self)
  def __hash__(self):
    return hash(self.key)
  def __eq__(self, other):
    return self.key == other.key
  def __repr__(self):
    return self.title
      
def force_layout(nodes, center_node, iterations = 10, positions = None, target_bounds = (0, 0, 1, 1), fixed = None, center_fixed = False):

  if len(nodes) == 0:
    return{}
  if len(nodes) < 2:
    return # Not enough graph to layout
  if not positions:
    positions = {}
  if not fixed:
    fixed = set()
  if center_fixed:
    fixed.add(center_node)
  deltas = {}
  gravity = False
  k = 0.01

  for node in nodes:
    if node not in positions:
      positions[node] = Vector(random.random(), random.random())
    deltas[node] = Vector(0, 0)
  
  center_vector = positions[center_node]
  
  for iter in range(iterations):
    #print('---' + str(iter))
    #print(positions)
    
    # Center pull
    if gravity:
      for node in positions:
        if node not in fixed:
          pull = (center_vector - positions[node]) * k
          deltas[node] += pull
    
    # Edges pull, nodes repel (push)
    for i in range(len(nodes) - 1):
      for j in range(i + 1, len(nodes)):
        n1 = nodes[i]
        n2 = nodes[j]
        #v = Vector.from_to(positions[n1], positions[n2])
        v = positions[n2] - positions[n1]
        l = v.length()
        if l == 0: # Overlapping
          v = Vector((random.random()-0.5)/100, (random.random()-0.5)/100)
          l = v.length()
        push = v / v.length()
        deltas[n1] -= push
        deltas[n2] += push
        if n2 in n1.edges:
          pull = v * k
          deltas[n1] += pull
          deltas[n2] -= pull
    
    # Nodes move
    for node in positions.keys():
      if node not in fixed:
        positions[node] += deltas[node]
  
  if center_fixed:
    return scale_centric(positions, center_node, target_bounds, fixed)
  else:
    return scale_even(positions, center_node, target_bounds, fixed)
  
def scale_centric(positions, center_node, target_bounds, fixed):
  center = positions[center_node]
  min_x = max_x = min_y = max_y = 0
  
  nodes = positions.keys()
  for node in nodes:
    position = positions[node]
    dx = position.x - center.x
    dy = position.y - center.y
    max_x = max(max_x, dx)
    min_x = min(min_x, dx)
    max_y = max(max_y, dy)
    min_y = min(min_y, dy)
  
  """
  sx = center.x - max_x
  sy = center.y - max_y
  sw = 2 * max_x
  sh = 2 * max_y
  """
  
  (tx, ty, tw, th) = target_bounds
  
  low_cx = 0 if min_x == 0 else (center.x - tx)/abs(min_x)
  high_cx = 0 if max_x == 0 else (tx + tw - center.x)/max_x
  low_cy = 0 if min_y == 0 else (center.y - ty)/abs(min_y)
  high_cy = 0 if max_y == 0 else (ty + th - center.y)/max_y

  converted_positions = {}
  
  for node in nodes:
    pos = positions[node]
    if node in fixed:
      converted_positions[node] = positions[node]
    else:
      dx = pos.x - center.x
      dy = pos.y - center.y
      converted_positions[node] = Vector(
        center.x + dx * (high_cx if dx > 0 else low_cx),
        center.y + dy * (high_cy if dy > 0 else low_cy)
      )
    
  return converted_positions

def scale_even(positions, center_node, target_bounds, fixed):
  min_x = max_x = min_y = max_y = None
  
  for node in positions:
    pos = positions[node]
    if not isinstance(max_x, numbers.Number):
      max_x = min_x = pos.x
      max_y = min_y = pos.y
    else: 
      max_x = max(max_x, pos.x)
      min_x = min(min_x, pos.x)
      max_y = max(max_y, pos.y)
      min_y = min(min_y, pos.y)

  sx = min_x
  sy = min_y
  sw = max_x - min_x
  sh = max_y - min_y
  
  (tx, ty, tw, th) = target_bounds
  
  cx = tw/sw
  cy = th/sh
  
  converted_positions = {}
  
  for node in positions:
    pos = positions[node]
    if node in fixed:
      converted_positions[node] = positions[node]
    else:
      converted_positions[node] = Vector(
        tx + cx * (pos.x - sx),
        ty + cy * (pos.y - sy)
      )
    
  return converted_positions

if __name__ == '__main__':
  v = Vector(1,2)
  v2 = Vector.from_pos((3,4))
  
  assert (v + v2) / 2.0 == Vector(2, 3)
  assert v * 0.1 == Vector(0.1, 0.2)
  assert v2[1] == 4
  assert v.distance_to(v2) == math.sqrt(8) #2.8284271247461903
  
  a = Node('a','A')
  b = Node('b','B')
  c = Node('c','C')
  d = Node('d','D')
  
  a.add_edge(b)
  a.add_edge(c)
  c.add_edge(d)
  
  nodes = [ a, b, c, d ]
  positions = force_layout(nodes, b, 100)
  
  x = Node('a', 'A')
  y = Node('a', 'B')
  assert x == y
  
  positions = {
    a: Vector(-1, -1),
    b: Vector(2, 2),
    c: Vector(1, 1),
    d: Vector(-0.5, 1.5)
  }
  
  target_bounds = (0, 0, 10, 10)
  
  print(scale(positions, c, target_bounds, set()))
  
