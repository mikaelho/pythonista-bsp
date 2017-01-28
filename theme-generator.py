# coding: utf-8
import ui, colorsys

def set_colors(importance, rgb_component, rgb_value, saturation, lightness):
  (r, g, b) = heatmap_color(importance, saturation, lightness)
  rgb = [r, g, b]
  rgb[rgb_component] = rgb_value
  return (rgb[0], rgb[1], rgb[2])
  
def heatmap_color(value, saturation, lightness):
  #h = 1.0 - value
  return colorsys.hls_to_rgb(value, lightness, saturation)

base_range = (0.1, 0.25, 0.5, 0.75, 0.9)
rgb_names = ('R', 'G', 'B')

def create_colors():
  line = 0
  for rgb_component in range(3):
    for rgb_value in base_range:
      for saturation in (0.25, 0.5, 0.75, 1):
        for lightness in (0.25, 0.5, 0.75):
          label = ui.Label()
          label.text = 'l: ' + str(lightness) + ' s: ' + str(saturation) + ' ' + rgb_names[rgb_component] + ': ' + str(rgb_value)        
          v.add_subview(label)
          column = 0
          line += 1
          label.frame = (20, line * line_height, 180, line_height)
          for value in base_range:
            color_box = ui.View()
            color_box.background_color = set_colors(value, rgb_component, rgb_value, saturation, lightness)
            color_box.frame = (200 + column * box_size, line * line_height, box_size, box_size)
            v.add_subview(color_box)
            column += 1
  return line

line_height = 31
box_size = 30

v = ui.ScrollView()
v.background_color = 'white'

v.present()

lines = create_colors()

v.content_size = (500, lines * line_height)
