import vcCore as vc
import vcBehaviors as vc_beh
import vcGeometry
vc_gst = vcGeometry.vcGeometrySetType
import re
import os
import numpy as np
import json

comp = vc.getComponent()
app = vc.getApplication()
bar = app.findMaterial("256")
sim = vc.getSimulation()
world = vc.getWorld()    
direction = comp.Properties['Direction']
geometry = comp.findFeature("Geometry")
 
folder = r"C:/Users/LiuCh1/Downloads/ppf/curtain/session-1"
folder2 = r"C:/Users/LiuCh1/Downloads/ppf/curtain/session"
folder3 = r"C:/Users/LiuCh1/Downloads/ppf/VisualComponents2/session"
SCALE = 1000.0
batch = 4096

def toggle_components(arg):
  sphere = world.findComponent("Sphere")
  pieces = world.findComponent("Pieces")
  
  if direction.Value == "Simulation to Server":
    geometry.Visible = False    
    sphere.Visible = True
    pieces.Visible = True
  elif direction.Value == "Server to Simulation":
    geometry.Visible = True    
    sphere.Visible = False
    pieces.Visible = False
  
  geometry.rebuild()
  comp.Material = comp.Material
    
direction.OnChanged.reset()
direction.OnChanged += toggle_components
  
def natural_keys(text):    
  return [int(c) if c.isdigit() else c.lower() for c in re.split('([0-9]+)', text)]

async def OnRun():
  
  sphere = world.findComponent("Sphere")
  pieces = world.findComponent("Pieces")
 
  if direction.Value == "Simulation to Server":
    geometry.Visible = False
    geometry.rebuild()
    sphere.Visible = True
    pieces.Visible = True
    
    await vc.delay(1.01)
    path_data = {}
    path_data['pieces'] = pieces.Properties['Pieces'].Value
    path_data['spacing'] = pieces.Properties['Spacing'].Value
    path_data['path'] = []
    
    for i in range(300):
      
      sphere.update()
      old_x = sphere.WorldPositionMatrix.Px / SCALE
      old_y = sphere.WorldPositionMatrix.Py / SCALE
      old_z = sphere.WorldPositionMatrix.Pz / SCALE
      
      await vc.delay(0.01)
      
      sphere.update()
      x = sphere.WorldPositionMatrix.Px / SCALE
      y = sphere.WorldPositionMatrix.Py / SCALE
      z = sphere.WorldPositionMatrix.Pz / SCALE
     
      path_data['path'].append([[(x - old_x), (z - old_z), (-y + old_y)], (i / 100.0 + 0.01)])                

    with open(f"{folder}/output/path_data.json", "w") as f:
      json.dump(path_data, f)
    
  elif direction.Value == "Server to Simulation":
    geometry.Visible = True
    geometry.rebuild()
    sphere.Visible = False
    pieces.Visible = False
    
    vertices = {}
    
    tri_raw = np.fromfile(f"{folder3}/bin/tri.bin", dtype=np.int32).reshape(-1, 6)[:, [0, 2, 4]]             
    
    for root, dirs, files in os.walk(f"{folder3}/output/"):
      for f in files:
        if f.endswith(".bin"):
          verts = np.fromfile(f"{folder3}/output/{f}", dtype=np.float32).reshape(-1, 3)
          vertices[f] = verts
   
    frame_keys = sorted(vertices.keys(), key = natural_keys)
    
    pieces = []    
    for i in range(1, 11):
      piece = [i for i in range(batch * (i -1), batch * i)]
      pieces.append(piece)
    
    uvs = []
    for i in range(10):   
      uv = [(0.1 * i + 0.1, 0.1 * i + 0.1)] * batch      
      uvs.append(uv)
      
    #'''
    geometry.Geometry.clear()
    geometry.rebuild()
    
    triangle_set = geometry.Geometry.createGeometrySet(vc_gst.TRIANGLE_SET)
    triangle_set.UseTextureCoordinates = True
    triangle_set.UseDynamicTextureCoordinates = True
    triangle_set.Material = bar
    
    data_vertices = vertices[frame_keys[0]]
    for vertex in data_vertices:
      triangle_set.addPoint(vertex[0] * SCALE, -vertex[2] * SCALE, vertex[1] * SCALE)
    
    for indexes in tri_raw:
      triangle_set.addTriangle(indexes[0], indexes[1], indexes[2])
    
    for i in range(10):           
      triangle_set.setTextureCoordinates(pieces[i], uvs[i])
      
    
    geometry.rebuild()
    comp.Material = comp.Material
    app.render()
    #'''    
    
    for frame_key in frame_keys:
      geometry.Geometry.clear()
      geometry.rebuild()
      
      triangle_set = geometry.Geometry.createGeometrySet(vc_gst.TRIANGLE_SET)
      triangle_set.UseTextureCoordinates = True
      triangle_set.UseDynamicTextureCoordinates = True
      triangle_set.Material = bar
    
      data_vertices = vertices[frame_key]
      for vertex in data_vertices:
        triangle_set.addPoint(vertex[0] * SCALE, -vertex[2] * SCALE, vertex[1] * SCALE)
      
      for indexes in tri_raw:
        triangle_set.addTriangle(indexes[0], indexes[1], indexes[2])
      
      for i in range(10):           
        triangle_set.setTextureCoordinates(pieces[i], uvs[i])
      
      geometry.rebuild()
      comp.Material = comp.Material
      app.render()
      await vc.delay(0.0166666666666667)
