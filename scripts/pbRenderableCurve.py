import pymel.core as pm


class UI(object):
    def __init__(self):
        title = 'pbRenderableCurve'
        version = 1.0

        if pm.window('pbRCurve', exists=True):
            pm.deleteUI('pbRCurve')

        with pm.window('pbRCurve', title='{0} | {1}'.format(title, version), s=False) as window:
            with pm.columnLayout():
                with pm.frameLayout(l='Selection:', cll=True, bs='out'):
                    with pm.rowLayout(nc=2):
                        pm.button(l='Make Renderable', c=self.makeRenderable)
                        pm.button(l='Remove Renderable')

                with pm.frameLayout(l='Mesh Settings:', cll=True, bs='out'):
                    with pm.columnLayout():
                        pm.radioButtonGrp(l='Polygon Type:', sl=0, nrb=2,
                                          labelArray2=['Quads', 'Tris'])

                        pm.intSliderGrp(l='Thickness:', f=True)
                        pm.intSliderGrp(l='Sides', f=True)
                        pm.intSliderGrp(l='Samples', f=True)

        window.show()


class Curve(object):
    def __init__(self):
        pass

    def makeRenderable(self, *args):
        sel = pm.selected()
        stroke, brush = self.createBrush(sel[0])
        self.strokeToMesh(stroke, brush)

    def createBrush(self, curve):
        brush = pm.createNode('brush', name='{0}Brush'.format(curve))
        stroke = pm.stroke(name='{0}Stroke'.format(curve), seed=0, pressure=True)

        brush.outBrush.connect(stroke.brush)
        pm.connectAttr('time1.outTime', brush.time)

        # Brush Defualts
        brush.brushWidth.set(1)
        brush.tubeSections.set(8)
        brush.strokeTime.set(1)

        # set divisions
        spans = curve.spans.get()
        deg = curve.degree.get()
        samples = (spans + 1) * deg
        if deg > 1:
            samples = (spans * 5) + 1

        stroke.getShape().pathCurve[0].samples.set(samples)

        stroke.useNormal.set(0)
        stroke.normalY.set(1.0)

        curve.ws.connect(stroke.getShape().pathCurve[0].curve)

        stroke.perspective.set(1)
        stroke.displayPercent.set(100.0)

        return stroke, brush

    def strokeToMesh(self, stroke, brush):
        # Stroke settings
        stroke.meshVertexColorMode.set(0)
        stroke.meshQuadOutput.set(1)

        # output mesh stuff
        meshName = brush.replace('Brush', "Mesh")
        mesh = pm.createNode('mesh', n='%sShape' % meshName)
        print mesh
