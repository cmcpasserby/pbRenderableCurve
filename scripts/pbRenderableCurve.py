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
                        pm.button(l='Make Renderable')
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
        sel = pm.selected()
        self.createBrush(sel[0])
        self.strokeToMesh()

        # Attributes
        self.thickness = self.brush.brushWidth
        self.sides = self.brush.tubeSections
        self.samples = self.stroke.sampleDensity

    def createBrush(self, curve):
        self.brush = pm.createNode('brush', name='{0}Brush'.format(curve))
        self.stroke = pm.stroke(name='{0}Stroke'.format(curve), seed=0, pressure=True)

        self.brush.outBrush.connect(self.stroke.brush)
        pm.connectAttr('time1.outTime', self.brush.time)

        # Brush Defualts
        self.brush.brushWidth.set(1)
        self.brush.tubeSections.set(8)
        self.brush.strokeTime.set(1)

        # Brush type mesh
        self.brush.brushType.set(5)

        # set divisions
        spans = curve.spans.get()
        deg = curve.degree.get()
        samples = (spans + 1) * deg
        if deg > 1:
            samples = (spans * 5) + 1

        self.stroke.getShape().pathCurve[0].samples.set(samples)

        self.stroke.useNormal.set(0)
        self.stroke.normalY.set(1.0)

        curve.ws.connect(self.stroke.getShape().pathCurve[0].curve)

        self.stroke.perspective.set(1)
        self.stroke.displayPercent.set(100.0)

        return self.stroke, self.brush

    def strokeToMesh(self):
        # Stroke settings
        self.stroke.meshVertexColorMode.set(0)
        self.stroke.meshQuadOutput.set(1)
        self.stroke.meshPolyLimit.set(100000)

        # output mesh stuff
        meshName = self.brush.replace('Brush', "Mesh")
        mesh = pm.createNode('mesh', n='%sShape' % meshName)
        self.stroke.getShape().worldMainMesh[0].connect(mesh.inMesh)

        # Display mesh as ref
        mesh.overrideDisplayType.set(2)
        self.stroke.visibility.set(0)

        # brushType = self.brush.brushType.get()
        # hardEdges = self.brush.hardEdges.get()
        # self.stroke.meshHardEdges.set(hardEdges)
