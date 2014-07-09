import pymel.core as pm


class UI(object):
    def __init__(self):
        title = 'pbRenderableCurve'
        version = 1.02

        if pm.window('pbRCurve', exists=True):
            pm.deleteUI('pbRCurve')

        with pm.window('pbRCurve', title='{0} | {1}'.format(title, version), s=False) as window:
            with pm.columnLayout():
                with pm.frameLayout(l='Selection:', cll=True, bs='out'):
                    with pm.columnLayout():
                        self.selField = pm.textFieldGrp(text='No Curves Selected', ed=False, l='Curve:', cw2=[72, 192])
                        with pm.rowLayout(nc=2):
                            self.bRenderable = pm.checkBox(l='Renderable', cc=self.bcRenderable)

                with pm.frameLayout(l='Mesh Settings:', cll=True, bs='out') as self.meshUI:
                    with pm.columnLayout():
                        with pm.rowLayout(nc=4):
                            self.useNormal = pm.checkBox(l='Use Normal', cc=self.bcUseNormal)
                            self.normalVector = [pm.intField(width=62, en=False, value=0, cc=self.setNormal),
                                                 pm.intField(width=62, en=False, value=1, cc=self.setNormal),
                                                 pm.intField(width=62, en=False, value=0, cc=self.setNormal)]
                        self.meshAttrs = [AttrSlider(maxValue=128, name='Thickness', obj=getCurves, type_='float', fmn=0.0001),
                                          AttrSlider(value=3, minValue=3, maxValue=64, name='Sides', obj=getCurves, fmn=3, fmx=100),
                                          AttrSlider(minValue=1, maxValue=32, name='Samples', obj=getCurves, fmn=1, fmx=128)]

                with pm.frameLayout('Shell Settings:', cll=True, bs='out') as self.shellUI:
                    with pm.columnLayout():
                        self.bShell = pm.checkBox(l='Enable Shell', cc=self.bcShell)
                        self.shellAttrs = [AttrSlider(value=1, minValue=-64, maxValue=64, name='ShellThickness', obj=getCurves, type_='float'),
                                           AttrSlider(value=1, minValue=1, maxValue=64, name='ShellDivisions', obj=getCurves, fmn=1, fmx=32)]

        window.show()
        pm.scriptJob(event=['SelectionChanged', self.refresh], protected=True, p=window)
        self.refresh()

    def refresh(self):
        curves = getCurves()
        if len(curves) == 1:
            self.selField.setText(curves[0])
            self.getValues(curves)

        elif len(curves) > 1:
            self.selField.setText('%s Curves Selected' % len(curves))
            self.getValues(curves)

        else:
            self.selField.setText('No Curves Selected')
            self.bRenderable.setValue(False)
            self.bShell.setValue(False)
            self.useNormal.setValue(False)
            for i in self.meshAttrs:
                i.setEnable(False)

            for i in self.shellAttrs:
                i.setEnable(False)

            for i in self.normalVector:
                i.setEnable(False)

    def bcRenderable(self, *args):
        curves = getCurves()

        if not all(i.isRenderable() for i in curves):
            for i in curves:
                i.makeRenderable()
        else:
            for i in curves:
                i.makeNonRenderable()
        pm.select([i.curve for i in curves])
        self.refresh()

    def bcShell(self, *args):
        curves = getCurves()
        if all(i.isRenderable() for i in curves):
            if not all(i.hasShell() for i in curves):
                for i in curves:
                    i.makeShell()
            else:
                for i in curves:
                    i.makeNonShell()

        pm.select([i.curve for i in curves])
        self.refresh()

    def getValues(self, curves):
        if all(i.isRenderable() for i in curves):
            self.bRenderable.setValue(True)
            for i in self.meshAttrs:
                i.get()
                i.setEnable(True)

            if all(i.hasShell() for i in curves):
                self.bShell.setValue(True)
                for i in self.shellAttrs:
                    i.get()
                    i.setEnable(True)
            else:
                self.bShell.setValue(False)
                for i in self.shellAttrs:
                    i.setEnable(False)

            if all(i.usesNormal() for i in curves):
                self.useNormal.setValue(True)
                nVector = curves[0].stroke.normal.get()
                for i in range(3):
                    self.normalVector[i].setValue(nVector[i])
                    self.normalVector[i].setEnable(True)
            else:
                self.useNormal.setValue(False)
                for i in self.normalVector:
                    i.setEnable(False)

        else:
            self.bRenderable.setValue(False)
            self.bShell.setValue(False)
            self.useNormal.setValue(False)
            for i in self.meshAttrs:
                i.setEnable(False)
            for i in self.shellAttrs:
                i.setEnable(False)
            for i in self.normalVector:
                i.setEnable(False)

    def bcUseNormal(self, *args):
        curves = getCurves()
        if all(i.isRenderable() for i in curves):
            if not all(i.usesNormal() for i in curves):
                for i in curves:
                    i.useNormal(True)
            else:
                for i in curves:
                    i.useNormal(False)
        else:
            self.useNormal.setValue(False)

        pm.select([i.curve for i in curves])
        self.refresh()

    def setNormal(self, *args):
        curves = getCurves()
        nrms = [i.getValue() for i in self.normalVector]
        for i in curves:
            i.stroke.normal.set(nrms)


class Curve(object):
    def __init__(self, curve):
        self.curve = curve

        if self.isRenderable():
            self.stroke = self.curve.getShape().connections(shapes=True, type=pm.nt.Stroke)[0]
            self.brush = self.stroke.connections(type=pm.nt.Brush)[0]

            self.thickness = self.brush.brushWidth
            self.sides = self.brush.tubeSections
            self.samples = self.stroke.sampleDensity

            self.mesh = self.stroke.worldMainMesh[0].connections()[0]
            if isinstance(self.mesh, pm.nt.PolyExtrudeFace):
                self.mesh = self.mesh.connections(type=pm.nt.Mesh)[0]

            if self.hasShell():
                self.extrudeNode = self.mesh.getShape().connections(type=pm.nt.PolyExtrudeFace)[0]
                self.shellthickness = self.extrudeNode.localTranslateZ
                self.shelldivisions = self.extrudeNode.divisions

    def __str__(self):
        return str(self.curve)

    def makeRenderable(self):
        if not self.isRenderable():
            self.createBrush()
            self.strokeToMesh()

    def makeNonRenderable(self):
        if self.isRenderable():
            if self.hasShell():
                self.makeNonShell()
            mesh = self.stroke.worldMainMesh[0].connections(shapes=True, type=pm.nt.Mesh)
            pm.delete(self.brush)
            pm.delete(self.stroke.getParent())
            pm.delete(mesh[0].getParent())

    def makeShell(self):
        if not self.hasShell():
            self.ExtrudeNode = pm.polyExtrudeFacet(self.mesh, ltz=1)

    def makeNonShell(self):
        if self.hasShell():
            pm.delete(self.extrudeNode)

    def createBrush(self):
        self.brush = pm.createNode('brush', name='{0}Brush'.format(self.curve))
        self.stroke = pm.stroke(name='{0}Stroke'.format(self.curve), seed=0, pressure=True)

        self.brush.outBrush >> self.stroke.brush
        pm.PyNode('time1').outTime >> self.brush.time

        # Brush Defualts
        self.brush.brushWidth.set(1)
        self.brush.tubeSections.set(8)
        self.brush.strokeTime.set(1)

        # Brush type mesh
        self.brush.brushType.set(5)

        # set divisions
        spans = self.curve.spans.get()
        deg = self.curve.attr('degree').get()
        samples = (spans + 1) * deg
        if deg > 1:
            samples = (spans * 5) + 1

        self.stroke.getShape().pathCurve[0].samples.set(samples)

        self.stroke.useNormal.set(0)
        self.stroke.normalY.set(1.0)

        self.curve.ws >> self.stroke.getShape().pathCurve[0].curve

        self.stroke.perspective.set(1)
        self.stroke.displayPercent.set(100.0)

    def strokeToMesh(self):
        # Stroke settings
        self.stroke.meshVertexColorMode.set(0)
        self.stroke.meshQuadOutput.set(1)
        self.stroke.meshPolyLimit.set(100000)

        # output mesh stuff
        meshName = self.brush.replace('Brush', "Mesh")
        self.mesh = pm.createNode('mesh', n='%sShape' % meshName)
        self.stroke.getShape().worldMainMesh[0] >> self.mesh.inMesh

        # Parent Stroke to mesh to clean up outliner
        self.stroke.setParent(self.mesh.getParent())

        # Display mesh as ref
        self.mesh.overrideEnabled.set(1)
        self.mesh.overrideDisplayType.set(2)
        self.stroke.visibility.set(0)

        # lambert Shadeing
        sg = pm.PyNode('initialShadingGroup')
        sg.add(self.mesh)

    def isRenderable(self):
        strokes = self.curve.getShape().connections(shapes=True, type=pm.nt.Stroke)
        if strokes:
            return True
        else:
            return False

    def hasShell(self):
        meshShape = self.mesh.getShape()
        if isinstance(meshShape.inMesh.connections()[0], pm.nt.PolyExtrudeFace):
            return True
        else:
            return False

    def useNormal(self, val):
        self.stroke.useNormal.set(val)

    def usesNormal(self):
        return self.stroke.useNormal.get()


class AttrSlider(object):
    def __init__(self, value=0, minValue=0, maxValue=32, name=None, obj=None, type_='int', en=False, fmx=10000, fmn=-10000):
        self.name = name
        self.obj = obj

        self.undoState = False

        if type_ == 'float':
            self.attr_ = pm.floatSliderGrp(field=True, l=self.name, value=value, minValue=minValue, maxValue=maxValue,
                                           cc=self.set, dc=self.set, pre=5, cw3=[72, 64, 128], en=en, fmx=fmx, fmn=fmn)
        elif type_ == 'int':
            self.attr_ = pm.intSliderGrp(field=True, l=self.name, value=value, minValue=minValue, maxValue=maxValue,
                                         cc=self.set, dc=self.set, cw3=[72, 64, 128], en=en, fmn=fmn, fmx=fmx)

    def get(self, *args):
        try:
            value = getattr(self.obj()[0], self.name.lower()).get()
            self.attr_.setValue(value)
        except AttributeError:
            pass

    def set(self, cc=False):
        if not cc and not self.undoState:
            self.undoState = True
            pm.undoInfo(openChunk=True)

        for i in self.obj():
            getattr(i, self.name.lower()).set(self.attr_.getValue())

        if cc and self.undoState:
            pm.undoInfo(closeChunk=True)
            self.undoState = False

    def setEnable(self, val):
        self.attr_.setEnable(val)


def getCurves():
    sel = pm.selected()
    curveList = []
    if sel:
        if isinstance(sel[0], pm.NurbsCurveCV):
            sel = list(set([i.node().getParent() for i in sel]))

        if all(isinstance(i, pm.nt.Transform) for i in sel):
            for i in sel:
                if isinstance(i.getShape(), pm.nt.NurbsCurve):
                    curveList.append(Curve(i))
    return curveList
