# Estrategias de Fresado

---

## CreateBidirectionalMillingStrategy Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateBidirectionalMillingStrategy Method
IScripting Interface See Also Send Feedback

Create the machining strategy for a milling with multiple passes in bidirectional way (will be valid only with the first operation created after strategy creation).

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
BidirectionalMillingStrategy CreateBidirectionalMillingStrategy(
bool allowMultiplePasses,
double cuttingDepth,
double finishCuttingDepth
)
```
#### Parameters
allowMultiplePasses
Type: System..::..Boolean
If true, this is the standard roughing operation with multiple passes, i. e. several layers of material are
removed sequentially, taking into account the maximum cutting depth. If false, this is the special roughing operation for pre-cast features
with one pass
cuttingDepth
Type: System..::..Double
Pass depth in the direction axial to the tool
finishCuttingDepth
Type: System..::..Double
Final pass depth in the direction axial to the tool. If programmed is the pass that allows to reach the final depth programmed.
#### Return Value
The strategy created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateContourParallelStrategy Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateContourParallelStrategy Method
IScripting Interface See Also Send Feedback

Create the machining strategy for a contour pocket machining.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
ContourParallelStrategy CreateContourParallelStrategy(
bool insideToOutSide,
int rotationDirection,
bool allowMultiplePasses,
double cuttingDepth,
double finishCuttingDepth,
int strokeConnectionType,
bool isHelicStrategy
)
```
#### Parameters
insideToOutSide
Type: System..::..Boolean
If true machning operation is executed from inside t ooutside, false from outside to inside.
rotationDirection
Type: System..::..Int32
Direction used to perform machining.
0 = clockwise
0 = counterclockwise

allowMultiplePasses
Type: System..::..Boolean
If true, this is the standard roughing operation with multiple passes, i. e. several layers of material are
removed sequentially, taking into account the maximum cutting depth. If false, this is the special roughing operation for pre-cast features
with one pass
cuttingDepth
Type: System..::..Double
Pass depth in the direction axial to the tool
finishCuttingDepth
Type: System..::..Double
Final pass depth in the direction axial to the tool. If programmed is the pass that allows to reach the final depth programmed.
strokeConnectionType
Type: System..::..Int32
Tool behavior when it moves between two passes.
0 = Tool remains into the workpiece and moves at the start point of the next pass (straghtline)
1 = Tool exits from the workpiece, moves in rapid and moves at the start point of the next pass (liftshiftplunge).
isHelicStrategy
Type: System..::..Boolean
Flag to set the strategy as helic in Z.
#### Return Value
The strategy created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateHelicMillingStrategy Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateHelicMillingStrategy Method
IScripting Interface See Also Send Feedback

Create the machining strategy for a milling with an helic toolpath (is valid only with the first operation created after strategy creation).

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
HelicMillingStrategy CreateHelicMillingStrategy(
double cuttingDepth,
bool allowsFinishCutting,
double finishCuttingDepth
)
```
#### Parameters
cuttingDepth
Type: System..::..Double
Pass depth in the direction axial to the tool.
allowsFinishCutting
Type: System..::..Boolean
True to execute the final pass, false otherwise
finishCuttingDepth
Type: System..::..Double
Final pass depth in the direction axial to the tool. If programmed is the pass that allows to reach the final depth programmed.
#### Return Value
The strategy created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreatePlaneCutterLocationStrategy Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreatePlaneCutterLocationStrategy Method
IScripting Interface See Also Send Feedback

Create the machining strategy for a 3D machininga operation with a fixed tool direction

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
PlaneCutterLocationStrategy CreatePlaneCutterLocationStrategy(
double zRotation,
double xRotation
)
```
#### Parameters
zRotation
Type: System..::..Double
Tool direction rotation around Z.
xRotation
Type: System..::..Double
Tool direction rotation around X.
#### Return Value
The strategy created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateSectioningMillingStrategy Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateSectioningMillingStrategy Method
IScripting Interface See Also Send Feedback

Create the machining strategy for a sectioning milling (will be valid only with the first operation created after strategy creation).

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
SectioningMillingStrategy CreateSectioningMillingStrategy(
double firstCutDepth,
double outDistance,
double sideMovingDistance
)
```
#### Parameters
firstCutDepth
Type: System..::..Double
First saw blade cut depth.
outDistance
Type: System..::..Double
Distance from the edge of the piece to which the blade must take as a result of the incision.
sideMovingDistance
Type: System..::..Double
Movement orthogonally to the programmed linear trajectory, based of current tool correction, positive for external, negative for internal.
#### Return Value
The strategy created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateUnidirectionalMillingStrategy Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateUnidirectionalMillingStrategy Method
IScripting Interface See Also Send Feedback

Create the machining strategy for a milling with multiple passes in unidirectiona way (will be valid only with the first operation created after strategy creation).

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
UnidirectionalMillingStrategy CreateUnidirectionalMillingStrategy(
bool allowMultiplePasses,
double cuttingDepth,
double finishCuttingDepth,
int strokeConnectionType
)
```
#### Parameters
allowMultiplePasses
Type: System..::..Boolean
If true, this is the standard roughing operation with multiple passes, i. e. several layers of material are
removed sequentially, taking into account the maximum cutting depth. If false, this is the special roughing operation for pre-cast features
with one pass
cuttingDepth
Type: System..::..Double
Pass depth in the direction axial to the tool
finishCuttingDepth
Type: System..::..Double
Final pass depth in the direction axial to the tool. If programmed is the pass that allows to reach the final depth programmed.
strokeConnectionType
Type: System..::..Int32
Tool behavior when it moves between two passes.
0 = Tool remains into the workpiece and moves at the start point of the next pass (straghtline)
1 = Tool exits from the workpiece, moves in rapid and moves at the start point of the next pass (liftshiftplunge).
#### Return Value
The strategy created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

