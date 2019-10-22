import tinyland

def main(snap, ctx):
  # Draw shapes to context based on data in snapshot
  for id, markers in snap.markers.items():
    for marker in markers:
      rectName = 'rect' + str(id)
      ctx.rect(rectName, marker.center.x, marker.center.y, 150, 150)

tinyland.run(main)