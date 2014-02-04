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
                    with pm.columnLayout():
                        self.selField = pm.textFieldGrp(text='No Curves Selected', ed=False, l='Curve:')
                        with pm.rowLayout(nc=2):
                            self.renderableUI = pm.checkBox(l='Renderable')
                            pm.checkBox(l='Mesh Selection')

                with pm.frameLayout(l='Mesh Settings:', cll=True, bs='out') as self.meshUI:
                    with pm.columnLayout():
                        pm.radioButtonGrp(l='Polygon Type:', sl=0, nrb=2,
                                          labelArray2=['Quads', 'Tris'])

                        pm.intSliderGrp(l='Thickness:', f=True)
                        pm.intSliderGrp(l='Sides', f=True)
                        pm.intSliderGrp(l='Samples', f=True)

        window.show()
        pm.scriptJob(event=['SelectionChanged', self.refresh], protected=True, p=window)
        self.refresh()

    def refresh(self):
        curves = self.getCurves()
        if len(curves) == 1:
            self.selField.setText(curves[0])
            self.meshUI.setEnable(True)
            self.isRenderable(curves)
        elif len(curves) > 1:
            self.selField.setText('{0} Curves Selected'.format(len(curves)))
            self.meshUI.setEnable(True)
            self.isRenderable(curves)
        else:
            self.selField.setText('No Curves Selected')
            self.meshUI.setEnable(False)
            self.renerableUI.setValue(False)

    def getCurves(self):
        sel = pm.selected()
        curveList = []
        if sel:
            for i in sel:
                if isinstance(i.getShape(), pm.nt.NurbsCurve):
                    curveList.append(Curve(i.getShape()))
        return curveList

    def isRenderable(self, curves):
        pass


class Curve(object):
    def __init__(self, curve):
        self.curve = curve

        # self.createBrush(self.curve)
        # self.strokeToMesh()

        # Curve Attributes
        # self.thickness = self.brush.brushWidth
        # self.sides = self.brush.tubeSections
        # self.samples = self.stroke.sampleDensity

    def makeRenderable(self, curve):
        pass

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

    def isRenderable(self):
        strokes = self.curve.getShape()
        if len(strokes):
            return True
        else:
            return False
