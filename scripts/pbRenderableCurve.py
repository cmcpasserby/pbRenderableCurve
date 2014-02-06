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
                            self.renderableUI = pm.checkBox(l='Renderable', cc=self.bcRenderable)
                            pm.checkBox(l='Mesh Selection')

                with pm.frameLayout(l='Mesh Settings:', cll=True, bs='out') as self.meshUI:
                    with pm.columnLayout():
                        self.attrs = [FloatAttr(1.0, 0.0, 128.0, 'Thickness'),
                                      IntAttr(3, 3, 64, 'Sides'),
                                      IntAttr(1, 1, 32, 'Samples')]

        window.show()
        pm.scriptJob(event=['SelectionChanged', self.refresh], protected=True, p=window)
        self.refresh()

    def refresh(self):
        curves = getCurves()
        if len(curves) == 1:
            self.selField.setText(curves[0])
            self.renderableUI.setValue(curves[0].isRenderable())
            self.getValues()
        elif len(curves) > 1:
            self.selField.setText('{0} Curves Selected'.format(len(curves)))
            self.renderableUI.setValue(all(i.isRenderable() for i in curves))
            self.getValues()
        else:
            self.selField.setText('No Curves Selected')
            self.renderableUI.setValue(False)
            self.setEnable(False)

    def bcRenderable(self, *args):
        curves = getCurves()
        if not curves[0].isRenderable():
            curves[0].makeRenderable()
        else:
            curves[0].makeNonRenderable()
        self.refresh()

    def getValues(self):
        for i in self.attrs:
            i.get()
            i.setEnable(True)

    def setEnable(self, val):
        for i in self.attrs:
            i.setEnable(val)


class Curve(object):
    def __init__(self, curve):
        self.curve = curve

        if self.isRenderable():
            self.stroke = self.curve.getShape().connections(shapes=True, type='stroke')[0]
            self.brush = self.stroke.connections(type='brush')[0]

            self.thickness = self.brush.brushWidth
            self.sides = self.brush.tubeSections
            self.samples = self.stroke.sampleDensity

    def __str__(self):
        return str(self.curve)

    def makeRenderable(self):
        self.createBrush()
        self.strokeToMesh()
        self.curve.select()

    def makeNonRenderable(self):
        mesh = self.stroke.worldMainMesh[0].connections(shapes=True, type='mesh')
        pm.delete(self.brush)
        pm.delete(self.stroke.getParent())
        pm.delete(mesh[0].getParent())

    def createBrush(self):
        self.brush = pm.createNode('brush', name='{0}Brush'.format(self.curve))
        self.stroke = pm.stroke(name='{0}Stroke'.format(self.curve), seed=0, pressure=True)

        self.brush.outBrush.connect(self.stroke.brush)
        pm.connectAttr('time1.outTime', self.brush.time)

        # Brush Defualts
        self.brush.brushWidth.set(1)
        self.brush.tubeSections.set(8)
        self.brush.strokeTime.set(1)

        # Brush type mesh
        self.brush.brushType.set(5)

        # set divisions
        spans = self.curve.spans.get()
        deg = self.curve.degree.get()
        samples = (spans + 1) * deg
        if deg > 1:
            samples = (spans * 5) + 1

        self.stroke.getShape().pathCurve[0].samples.set(samples)

        self.stroke.useNormal.set(0)
        self.stroke.normalY.set(1.0)

        self.curve.ws.connect(self.stroke.getShape().pathCurve[0].curve)

        self.stroke.perspective.set(1)
        self.stroke.displayPercent.set(100.0)

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
        mesh.overrideEnabled.set(1)
        mesh.overrideDisplayType.set(2)
        self.stroke.visibility.set(0)

        # lambert Shadeing
        sg = pm.PyNode('initialShadingGroup')
        sg.add(mesh)

    def isRenderable(self):
        strokes = self.curve.getShape().connections(shapes=True, type='stroke')
        if strokes:
            return True
        else:
            return False


class IntAttr(object):
    def __init__(self, value, minValue, maxValue, name):
        self.name = name

        self.attr = pm.intSliderGrp(field=True, l=self.name, minValue=minValue, maxValue=maxValue,
                                    cc=self.set, dc=self.set)

    def get(self, *args):
        try:
            value = getattr(getCurves()[0], self.name.lower()).get()
            self.attr.setValue(value)
        except AttributeError:
            pass

    def set(self, *args):
        getattr(getCurves()[0], self.name.lower()).set(self.attr.getValue())

    def setEnable(self, val):
        self.attr.setEnable(val)


class FloatAttr(object):
    def __init__(self, value, minValue, maxValue, name):
        self.name = name
        self.attr = pm.floatSliderGrp(field=True, l=self.name, minValue=minValue, maxValue=maxValue,
                                      cc=self.set, dc=self.set, pre=3)

    def get(self, *args):
        try:
            value = getattr(getCurves()[0], self.name.lower()).get()
            self.attr.setValue(value)
        except AttributeError:
            pass

    def set(self, *args):
        getattr(getCurves()[0], self.name.lower()).set(self.attr.getValue())

    def setEnable(self, val):
        self.attr.setEnable(val)


def getCurves():
    sel = pm.selected()
    curveList = []
    if sel:
        for i in sel:
            if isinstance(i.getShape(), pm.nt.NurbsCurve):
                curveList.append(Curve(i))
    return curveList
