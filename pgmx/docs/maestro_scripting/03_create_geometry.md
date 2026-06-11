# Geometría y Toolpaths

---

## Create3DRoughFinish Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..Create3DRoughFinish Method
IScripting Interface See Also Send Feedback

Create a 3D milling operation

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Operation Create3DRoughFinish(
string name,
string description,
TypeOfProcess typeOfProcess,
string tool,
string head,
double inputSpeed,
double rotSpeed,
double speed,
Nullable<double> inputZRotation,
Nullable<double> inputXRotation
)
```
#### Parameters
name
Type: System..::..String
Name of the operation.
description
Type: System..::..String
Description of the operation (optional parameter).
typeOfProcess
Type: TypeOfProcess
Type of operation, if not set a generic operation will be created (optional parameter).
tool
Type: System..::..String
Tool, if null or -1, tool will be selected automatically (optional parameter).
head
Type: System..::..String
Head to be used, if null or -1 head will be selected automatically (optional parameter).
inputSpeed
Type: System..::..Double
Entry speed into piece. (V in XGO Xilog), if not set the value programmed in the tooling will be used (optional parameter).
rotSpeed
Type: System..::..Double
Rotation speed of tool (S in XG0 Xilog), if not set the value programmed in the tooling will be used (optional parameter).
speed
Type: System..::..Double
Milling speed, if not set the value programmed in the tooling will be used (optional parameter).
inputZRotation
Type: System..::..Nullable<(Of <(<'Double>)>)>
Angle of rotation around the Z-axis (optional parameter).
inputXRotation
Type: System..::..Nullable<(Of <(<'Double>)>)>
Angle of rotation around the X-axis (optional parameter).
#### Return Value
The operation created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateArc2PointCenter Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateArc2PointCenter Method
IScripting Interface See Also Send Feedback

Create an arc given 2 points and center point on the active workplane.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Arc CreateArc2PointCenter(
string name,
double startX,
double startY,
double endX,
double endY,
double centerX,
double centerY,
bool isClockwise
)
```
#### Parameters
name
Type: System..::..String
Name of the geometry.
startX
Type: System..::..Double
X coordinate of the first point.
startY
Type: System..::..Double
Y coordinate of the first point.
endX
Type: System..::..Double
X coordinate of the last point.
endY
Type: System..::..Double
Y coordinate of the last point.
centerX
Type: System..::..Double
X coordinate of the center point.
centerY
Type: System..::..Double
Y coordinate of the center point.
isClockwise
Type: System..::..Boolean
If true the arc is clockwise.
#### Return Value
The geometry created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateArc2PointRadius Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateArc2PointRadius Method
IScripting Interface See Also Send Feedback

Create an arc given 2 points and radius on the active workplane.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Arc CreateArc2PointRadius(
string name,
double startX,
double startY,
double endX,
double endY,
double radius,
bool isClockwise,
bool isOver180
)
```
#### Parameters
name
Type: System..::..String
Name of the geometry.
startX
Type: System..::..Double
X coordinate of the first point.
startY
Type: System..::..Double
Y coordinate of the first point.
endX
Type: System..::..Double
X coordinate of the last point.
endY
Type: System..::..Double
Y coordinate of the last point.
radius
Type: System..::..Double
Radius of the arc.
isClockwise
Type: System..::..Boolean
If true the arc is clockwise.
isOver180
Type: System..::..Boolean
If true the arc sweeps an angle greater than 180 degrees.
#### Return Value
The geometry created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateArc3Points Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateArc3Points Method
IScripting Interface See Also Send Feedback

Create an arc given 3 points on the active workplane.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Arc CreateArc3Points(
string name,
double p1X,
double p1Y,
double p2X,
double p2Y,
double p3X,
double p3Y
)
```
#### Parameters
name
Type: System..::..String
Name of the geometry.
p1X
Type: System..::..Double
X coordinate of the point 1.
p1Y
Type: System..::..Double
Y coordinate of the point 1.
p2X
Type: System..::..Double
X coordinate of the point 2.
p2Y
Type: System..::..Double
Y coordinate of the point 2.
p3X
Type: System..::..Double
X coordinate of the point 3.
p3Y
Type: System..::..Double
Y coordinate of the point 3.
#### Return Value
The geometry created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateArcCenterAngle Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateArcCenterAngle Method
IScripting Interface See Also Send Feedback

Create an arc given first point, center point and angle swept on the active workplane.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Arc CreateArcCenterAngle(
string name,
double startX,
double startY,
double centerX,
double centerY,
double angle
)
```
#### Parameters
name
Type: System..::..String
Name of the geometry.
startX
Type: System..::..Double
X coordinate of the first point.
startY
Type: System..::..Double
Y coordinate of the first point.
centerX
Type: System..::..Double
X coordinate of the center point.
centerY
Type: System..::..Double
Y coordinate of the center point.
angle
Type: System..::..Double
Angle swept by the arc.
#### Return Value
The geometry created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateBladeCut Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateBladeCut Method
IScripting Interface See Also Send Feedback

Create a saw blade cut operation by using the active geometry.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Operation CreateBladeCut(
string name,
string description,
TypeOfProcess typeOfProcess,
string tool,
string head,
double angle,
int correction,
double inputSpeed,
double rotSpeed,
double speed,
double overMaterial,
bool cutPositionUpper,
bool materialPositionLeft,
double referenceOffset,
double extraDepth
)
```
#### Parameters
name
Type: System..::..String
Name of the operation.
description
Type: System..::..String
Description of the operation (optional parameter).
typeOfProcess
Type: TypeOfProcess
Type of operation, if not set a generic operation will be created (optional parameter).
tool
Type: System..::..String
Tool, if null or -1, tool will be selected automatically (optional parameter).
head
Type: System..::..String
Head to be used, if null or -1 head will be selected automatically (optional parameter).
angle
Type: System..::..Double
Rotation angle (degrees).
correction
Type: System..::..Int32
Tool correction.
C = 0, Tool center (default)
C = 1, left correction
C = 2, right correction
C = 3, in depth correction
C = 13, left correction + in depth correction
C = 23, right correction + in depth correction

inputSpeed
Type: System..::..Double
Entry speed into piece. (V in XGO Xilog), if not set the value programmed in the tooling will be used (optional parameter).
rotSpeed
Type: System..::..Double
Rotation speed of tool (S in XG0 Xilog), if not set the value programmed in the tooling will be used (optional parameter).
speed
Type: System..::..Double
Milling speed, if not set the value programmed in the tooling will be used (optional parameter).
overMaterial
Type: System..::..Double
Overmaterial, if not set 0 will be used (optional parameter).
cutPositionUpper
Type: System..::..Boolean
Reference position of the saw blade cut. true if upper cut position.
materialPositionLeft
Type: System..::..Boolean
Define the position of the workpiece to consider for the next machining operation. true for left position.
referenceOffset
Type: System..::..Double
Offset to the reference position of the saw blade cut.
extraDepth
Type: System..::..Double
Extra Depth of cutting.
#### Return Value
The operation created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateCircleCenterPoint Method

﻿
Collapse AllExpand All Members: Show All Members: Filtered Members: Filtered Members: Filtered
C#
Include Protected Members
Include Inherited Members
Xilog Maestro Scripting Language
IScripting..::..CreateCircleCenterPoint Method
IScripting Interface See Also Send Feedback

# Overload List
Name Description
CreateCircleCenterPoint(String, Double, Double, Double, Double)
Create a circle given center point and a point belonging on the circle on the active workplane.

CreateCircleCenterPoint(String, Double, Double, Double, Double, Boolean)
Create a circle given center point and a point belonging on the circle on the active workplane.

# See Also
IScripting Interface
IScripting Members
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateCircleCenterPoint Method  String  Double  Double  Double  Double

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateCircleCenterPoint Method (String, Double, Double, Double, Double)
IScripting Interface See Also Send Feedback

Create a circle given center point and a point belonging on the circle on the active workplane.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Circle CreateCircleCenterPoint(
string name,
double centerX,
double centerY,
double pointX,
double pointY
)
```
#### Parameters
name
Type: System..::..String
Name of the geometry.
centerX
Type: System..::..Double
X coordinate of the center point.
centerY
Type: System..::..Double
Y coordinate of the center point.
pointX
Type: System..::..Double
X coordinate of the circle point.
pointY
Type: System..::..Double
Y coordinate of the circle point.
#### Return Value
The geometry created.
# See Also
IScripting Interface
CreateCircleCenterPoint Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateCircleCenterPoint Method  String  Double  Double  Double  Double  Boolean

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateCircleCenterPoint Method (String, Double, Double, Double, Double, Boolean)
IScripting Interface See Also Send Feedback

Create a circle given center point and a point belonging on the circle on the active workplane.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Circle CreateCircleCenterPoint(
string name,
double centerX,
double centerY,
double pointX,
double pointY,
bool isClockwise
)
```
#### Parameters
name
Type: System..::..String
Name of the geometry.
centerX
Type: System..::..Double
X coordinate of the center point.
centerY
Type: System..::..Double
Y coordinate of the center point.
pointX
Type: System..::..Double
X coordinate of the circle point.
pointY
Type: System..::..Double
Y coordinate of the circle point.
isClockwise
Type: System..::..Boolean
If true circle is clockwise.
#### Return Value
The geometry created.
# See Also
IScripting Interface
CreateCircleCenterPoint Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateCircleCenterRadius Method

﻿
Collapse AllExpand All Members: Show All Members: Filtered Members: Filtered Members: Filtered
C#
Include Protected Members
Include Inherited Members
Xilog Maestro Scripting Language
IScripting..::..CreateCircleCenterRadius Method
IScripting Interface See Also Send Feedback

# Overload List
Name Description
CreateCircleCenterRadius(String, Double, Double, Double)
Create a circle given center point and radius on the active workplane.

CreateCircleCenterRadius(String, Double, Double, Double, Boolean)
Create a circle given center point and radius on the active workplane.

# See Also
IScripting Interface
IScripting Members
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateCircleCenterRadius Method  String  Double  Double  Double

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateCircleCenterRadius Method (String, Double, Double, Double)
IScripting Interface See Also Send Feedback

Create a circle given center point and radius on the active workplane.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Circle CreateCircleCenterRadius(
string name,
double centerX,
double centerY,
double radius
)
```
#### Parameters
name
Type: System..::..String
Name of the geometry.
centerX
Type: System..::..Double
X coordinate of the center point.
centerY
Type: System..::..Double
Y coordinate of the center point.
radius
Type: System..::..Double
Radius of the circle.
#### Return Value
The geometry created.
# See Also
IScripting Interface
CreateCircleCenterRadius Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateCircleCenterRadius Method  String  Double  Double  Double  Boolean

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateCircleCenterRadius Method (String, Double, Double, Double, Boolean)
IScripting Interface See Also Send Feedback

Create a circle given center point and radius on the active workplane.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Circle CreateCircleCenterRadius(
string name,
double centerX,
double centerY,
double radius,
bool isClockwise
)
```
#### Parameters
name
Type: System..::..String
Name of the geometry.
centerX
Type: System..::..Double
X coordinate of the center point.
centerY
Type: System..::..Double
Y coordinate of the center point.
radius
Type: System..::..Double
Radius of the circle.
isClockwise
Type: System..::..Boolean
If true circle is clockwise.
#### Return Value
The geometry created.
# See Also
IScripting Interface
CreateCircleCenterRadius Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateCombiflexUnloadUnitClamp Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateCombiflexUnloadUnitClamp Method
IScripting Interface See Also Send Feedback

Create the NC function CombiflexUnloadUnitClamp operation.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Operation CreateCombiflexUnloadUnitClamp(
string name,
double zQuote,
double yOffset
)
```
#### Parameters
name
Type: System..::..String
The name.
zQuote
Type: System..::..Double
Unload quote along Z axis.
yOffset
Type: System..::..Double
Offset along Y axis.
#### Return Value
[Missing <returns> documentation for "M:ScmGroup.XCam.Scripting.IScripting.CreateCombiflexUnloadUnitClamp(System.String,System.Double,System.Double)"]
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateContour Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateContour Method
IScripting Interface See Also Send Feedback

Create a countour operation

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Operation CreateContour(
string name,
double depth,
int typeOfContour,
int sideOfContour,
string description,
TypeOfProcess typeOfProcess,
string tool,
string head,
int correction,
double inputSpeed,
double rotSpeed,
double speed,
double overMaterial
)
```
#### Parameters
name
Type: System..::..String
Name of the operation.
depth
Type: System..::..Double
Depth of the operation.
typeOfContour
Type: System..::..Int32
Type of contour.
Workpiece = 0.
Selected geometry = 1.
sideOfContour
Type: System..::..Int32
Side of contour.
Internal = 0.
External = 1.
description
Type: System..::..String
Description of the operation (optional parameter).
typeOfProcess
Type: TypeOfProcess
Type of operation, if not set a generic operation will be created (optional parameter).
tool
Type: System..::..String
Tool, if null or -1, tool will be selected automatically (optional parameter).
head
Type: System..::..String
Head to be used, if null or -1 head will be selected automatically (optional parameter).
correction
Type: System..::..Int32
Tool correction.
C = 0, Tool center (default)
C = 1, left correction
C = 2, right correction

inputSpeed
Type: System..::..Double
Entry speed into piece. (V in XGO Xilog), if not set the value programmed in the tooling will be used (optional parameter).
rotSpeed
Type: System..::..Double
Rotation speed of tool (S in XG0 Xilog), if not set the value programmed in the tooling will be used (optional parameter).
speed
Type: System..::..Double
Milling speed, if not set the value programmed in the tooling will be used (optional parameter).
overMaterial
Type: System..::..Double
Overmaterial, if not set 0 will be used (optional parameter).
#### Return Value
The operation created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateEllipseCenterAxes Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateEllipseCenterAxes Method
IScripting Interface See Also Send Feedback

Create an ellipse with center point, major radius and minor radius on the active plane.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Ellipse CreateEllipseCenterAxes(
string name,
double centerX,
double centerY,
double majorRadius,
double minorRadius,
double angle
)
```
#### Parameters
name
Type: System..::..String
Name of the geometry.
centerX
Type: System..::..Double
X coordinate of the center point.
centerY
Type: System..::..Double
Y coordinate of the center point.
majorRadius
Type: System..::..Double
Value of the major radius.
minorRadius
Type: System..::..Double
Value of the minor radius.
angle
Type: System..::..Double
The angle of the major axis and the X axis of the active plane.
#### Return Value
The geometry created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateFillet Method

﻿
Collapse AllExpand All Members: Show All Members: Filtered Members: Filtered Members: Filtered
C#
Include Protected Members
Include Inherited Members
Xilog Maestro Scripting Language
IScripting..::..CreateFillet Method
IScripting Interface See Also Send Feedback

# Overload List
Name Description
CreateFillet(String, String, Double, Int32)
Create a fillet between two geometries identified by their name.

CreateFillet(String, Int32, Int32, Double, Int32)
Create a fillet between two adjacent elements of the active polyline.

CreateFillet(String, String, String, Double, Int32)
Create a fillet between two adjacent elements of the active polyline.

# See Also
IScripting Interface
IScripting Members
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateFillet Method  String  Int32  Int32  Double  Int32

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateFillet Method (String, Int32, Int32, Double, Int32)
IScripting Interface See Also Send Feedback

Create a fillet between two adjacent elements of the active polyline.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Polyline CreateFillet(
string geom,
int element1,
int element2,
double radius,
int option
)
```
#### Parameters
geom
Type: System..::..String
Name of the polyline.
element1
Type: System..::..Int32
Index of the first element.
element2
Type: System..::..Int32
Index of the first element.
radius
Type: System..::..Double
Radius of the fillet.
option
Type: System..::..Int32
Creation options:
option = 0 => Direct fillet.
option = 1 => Inverse fillet.
option = 2 => Clockwise fillet.
option = 3 => Counterclockwise fillet.

#### Return Value
The polyline with the fillet.
# See Also
IScripting Interface
CreateFillet Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateFillet Method  String  String  Double  Int32

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateFillet Method (String, String, Double, Int32)
IScripting Interface See Also Send Feedback

Create a fillet between two geometries identified by their name.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Arc CreateFillet(
string geom1,
string geom2,
double radius,
int option
)
```
#### Parameters
geom1
Type: System..::..String
Name of the first geometry.
geom2
Type: System..::..String
Name of the second geometry.
radius
Type: System..::..Double
Radius of the fillet.
option
Type: System..::..Int32
Creation options:
option = 0 => Direct fillet.
option = 1 => Inverse fillet.
option = 2 => Clockwise fillet.
option = 3 => Counterclockwise fillet.

#### Return Value
The geometry (fillet) created.
# See Also
IScripting Interface
CreateFillet Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateFillet Method  String  String  String  Double  Int32

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateFillet Method (String, String, String, Double, Int32)
IScripting Interface See Also Send Feedback

Create a fillet between two adjacent elements of the active polyline.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Polyline CreateFillet(
string geom,
string element1,
string element2,
double radius,
int option
)
```
#### Parameters
geom
Type: System..::..String
Name of the polyline.
element1
Type: System..::..String
Name of the first element.
element2
Type: System..::..String
Name of the second element.
radius
Type: System..::..Double
Radius of the fillet.
option
Type: System..::..Int32
Creation options:
option = 0 => Direct fillet.
option = 1 => Inverse fillet.
option = 2 => Clockwise fillet.
option = 3 => Counterclockwise fillet.

#### Return Value
The polyline with the fillet.
# See Also
IScripting Interface
CreateFillet Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateFinishedWorkpieceBox Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateFinishedWorkpieceBox Method
IScripting Interface See Also Send Feedback

Create a finished workpiece as a box. To define the raw and finished for the same workpiece use the same name.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Workpiece CreateFinishedWorkpieceBox(
string name,
double dx,
double dy,
double dz
)
```
#### Parameters
name
Type: System..::..String
Name of the workpiece.
dx
Type: System..::..Double
Workpiece length.
dy
Type: System..::..Double
Workpiece width.
dz
Type: System..::..Double
Workpiece height.
#### Return Value
The workpiece created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateFinishedWorkpieceFromExtrusion Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateFinishedWorkpieceFromExtrusion Method
IScripting Interface See Also Send Feedback

Create a finished workpiece as a solid extrusion along Z axis. The active geometry representing the boundary must be closed.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Workpiece CreateFinishedWorkpieceFromExtrusion(
string name,
double dz,
params string[] internalProfiles
)
```
#### Parameters
name
Type: System..::..String
Name of the workpiece.
dz
Type: System..::..Double
>Workpiece height.
internalProfiles
Type: array<System..::..String>[]()[][]
List of names of geometries to be used as internal profiles (workpiece holes).
#### Return Value
The workpiece created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateMessage Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateMessage Method
IScripting Interface See Also Send Feedback

Create the NC function message.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Operation CreateMessage(
string name,
string text,
bool waitForUserInput,
bool releaseWorkpiece
)
```
#### Parameters
name
Type: System..::..String
Name of the machine function.
text
Type: System..::..String
Text of the message.
waitForUserInput
Type: System..::..Boolean
If true text message stop the execution waiting the user input.
releaseWorkpiece
Type: System..::..Boolean
If true after execution stop workpiece will remain blocked.
#### Return Value
The machine function created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateNullOperation Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateNullOperation Method
IScripting Interface See Also Send Feedback

Create the NC function null operation.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Operation CreateNullOperation(
string name,
Nullable<double> X,
Nullable<double> Y,
Nullable<double> Q,
Nullable<double> speed,
Nullable<bool> spindleEnable,
string tool
)
```
#### Parameters
name
Type: System..::..String
Name of the machine function.
X
Type: System..::..Nullable<(Of <(<'Double>)>)>
Final position of head on axis X.
Y
Type: System..::..Nullable<(Of <(<'Double>)>)>
Final position of head on axis Y.
Q
Type: System..::..Nullable<(Of <(<'Double>)>)>
If not programmed or if the value is 0, quotas X and Y are considered referring to machine zero; if programmed on 1, quotas X and Y are considered referring to workpiece zero.
speed
Type: System..::..Nullable<(Of <(<'Double>)>)>
Speed to use for the movement (optional parameter).
spindleEnable
Type: System..::..Nullable<(Of <(<'Boolean>)>)>
Rotation speed of tool, if 0 (default value) is off (optional parameter).
tool
Type: System..::..String
Tool, if null or -1, tool will be selected automatically (optional parameter).
#### Return Value
The machine function created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreatePattern Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreatePattern Method
IScripting Interface See Also Send Feedback

Create a pattern of an operation.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Pattern CreatePattern(
int numberOfRows,
int numberOfColumns,
double rowsDistance,
double columnDistance,
double rotationAngle,
double rowLayoutAngle
)
```
#### Parameters
numberOfRows
Type: System..::..Int32
Number of rows.
numberOfColumns
Type: System..::..Int32
Number of columns.
rowsDistance
Type: System..::..Double
Distance between rows.
columnDistance
Type: System..::..Double
Distance between columns.
rotationAngle
Type: System..::..Double
Rotation 1.
rowLayoutAngle
Type: System..::..Double
Rotation 2 (required for oblique patterns).
#### Return Value
The pattern created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreatePolyline Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreatePolyline Method
IScripting Interface See Also Send Feedback

Create a polyline on the active workplane. The start point is used as the starting point for subsequent segments/arcs.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Polyline CreatePolyline(
string name,
double startX,
double startY
)
```
#### Parameters
name
Type: System..::..String
Name of the geometry.
startX
Type: System..::..Double
X coordinate of the first point of the polyline.
startY
Type: System..::..Double
X coordinate of the first point of the polyline.
#### Return Value
The geometry created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateRawWorkpieceBox Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateRawWorkpieceBox Method
IScripting Interface See Also Send Feedback

Create a raw workpiece as a box. To define the raw and finished for the same workpiece use the same name.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Workpiece CreateRawWorkpieceBox(
string name,
double dx,
double dy,
double dz,
double bx,
double by,
double bz
)
```
#### Parameters
name
Type: System..::..String
Name of the workpiece.
dx
Type: System..::..Double
Workpiece length.
dy
Type: System..::..Double
Workpiece width.
dz
Type: System..::..Double
Workpiece height.
bx
Type: System..::..Double
Distance in X of the raw geometry from the reference origin.
by
Type: System..::..Double
Distance in Y of the raw geometry from the reference origin.
bz
Type: System..::..Double
Distance in Z of the raw geometry from the reference origin.
#### Return Value
The workpiece created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateRawWorkpieceFromExtrusion Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateRawWorkpieceFromExtrusion Method
IScripting Interface See Also Send Feedback

Create a workpiece as a solid extrusion along Z axis. The active geometry representing the boundary must be closed.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Workpiece CreateRawWorkpieceFromExtrusion(
string name,
double dz,
double bx,
double by,
double bz,
params string[] internalProfiles
)
```
#### Parameters
name
Type: System..::..String
Name of the workpiece.
dz
Type: System..::..Double
Workpiece height.
bx
Type: System..::..Double
Distance in X of the raw geometry from the reference origin.
by
Type: System..::..Double
Distance in Y of the raw geometry from the reference origin.
bz
Type: System..::..Double
Distance in Z of the raw geometry from the reference origin.
internalProfiles
Type: array<System..::..String>[]()[][]
Lista di nomi delle geometrie da utilizzare come geometrie interne (ad esempio per definire una antina da sbattentare).
#### Return Value
The workpiece created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateRawWorkpiece Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateRawWorkpiece Method
IScripting Interface See Also Send Feedback

Create a workpiece as a box.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Workpiece CreateRawWorkpiece(
string name,
double bx1,
double bx2,
double by1,
double by2,
double bz1,
double bz2
)
```
#### Parameters
name
Type: System..::..String
Name of the workpiece.
bx1
Type: System..::..Double
X1 overmaterial.
bx2
Type: System..::..Double
X2 overmaterial.
by1
Type: System..::..Double
Y1 overmaterial.
by2
Type: System..::..Double
Y2 overmaterial.
bz1
Type: System..::..Double
Z1 overmaterial.
bz2
Type: System..::..Double
Z2 overmaterial.
#### Return Value
The workpiece created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateRoughFinish Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateRoughFinish Method
IScripting Interface See Also Send Feedback

Create a milling operation by using the active geometry.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Operation CreateRoughFinish(
string name,
double depth,
string description,
TypeOfProcess typeOfProcess,
string tool,
string head,
int correction,
double inputSpeed,
double rotSpeed,
double speed,
double overMaterial
)
```
#### Parameters
name
Type: System..::..String
Name of the operation.
depth
Type: System..::..Double
Depth of the operation.
description
Type: System..::..String
Description of the operation (optional parameter).
typeOfProcess
Type: TypeOfProcess
Type of operation, if not set a generic operation will be created (optional parameter).
tool
Type: System..::..String
Tool, if null or -1, tool will be selected automatically (optional parameter).
head
Type: System..::..String
Head to be used, if null or -1 head will be selected automatically (optional parameter).
correction
Type: System..::..Int32
Tool correction.
C = 0, Tool center (default)
C = 1, left correction
C = 2, right correction
C = 3, in depth correction
C = 13, left correction + in depth correction
C = 23, right correction + in depth correction

inputSpeed
Type: System..::..Double
Entry speed into piece. (V in XGO Xilog), if not set the value programmed in the tooling will be used (optional parameter).
rotSpeed
Type: System..::..Double
Rotation speed of tool (S in XG0 Xilog), if not set the value programmed in the tooling will be used (optional parameter).
speed
Type: System..::..Double
Milling speed, if not set the value programmed in the tooling will be used (optional parameter).
overMaterial
Type: System..::..Double
Overmaterial, if not set 0 will be used (optional parameter).
#### Return Value
The operation created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateScraping Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateScraping Method
IScripting Interface See Also Send Feedback

Create a scraping operation by using the active geometry.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Operation CreateScraping(
string name,
int toolApproach,
double depth,
string description,
TypeOfProcess typeOfProcess,
string tool,
string head,
int correction,
double inputSpeed,
double rotSpeed,
double speed,
double overMaterial
)
```
#### Parameters
name
Type: System..::..String
Name of the operation.
toolApproach
Type: System..::..Int32

Entry side: type of approach of the tool with respect to the geometry.
0 - Tool is parallel with the positive X-axis of the absolute reference system (IC = 0).
1 - Tool is perpendicular to the programmed trajectory on the right-hand side of the feed path (IC = 1).
2 - Tool is perpendicular to the programmed trajectory on the left-hand side of the feed path (IC = 2).
3 - Tool is parallel to the tangent of the starting point of the programmed trajectory (IC = 3). The angle of the tool remains fixed during machining (fixed position).
4 - Tool is parallel to the tangent of the current point of the programmed trajectory (IC = 4). The tool remains parallel with the path during machining (interpolated position).

depth
Type: System..::..Double
Depth of the operation.
description
Type: System..::..String
Description of the operation (optional parameter).
typeOfProcess
Type: TypeOfProcess
Type of operation, if not set a generic operation will be created (optional parameter).
tool
Type: System..::..String
Tool, if null or -1, tool will be selected automatically (optional parameter).
head
Type: System..::..String
Head to be used, if null or -1 head will be selected automatically (optional parameter).
correction
Type: System..::..Int32
Tool correction.
C = 0, Tool center (default)
C = 1, left correction
C = 2, right correction
C = 3, in depth correction
C = 13, left correction + in depth correction
C = 23, right correction + in depth correction

inputSpeed
Type: System..::..Double
Entry speed into piece. (V in XGO Xilog), if not set the value programmed in the tooling will be used (optional parameter).
rotSpeed
Type: System..::..Double
Rotation speed of tool (S in XG0 Xilog), if not set the value programmed in the tooling will be used (optional parameter).
speed
Type: System..::..Double
Milling speed, if not set the value programmed in the tooling will be used (optional parameter).
overMaterial
Type: System..::..Double
Overmaterial, if not set 0 will be used (optional parameter).
#### Return Value
The operation created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateSegment Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateSegment Method
IScripting Interface See Also Send Feedback

Create a line segment on the active workplane

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Segment CreateSegment(
string name,
double startX,
double startY,
double endX,
double endY
)
```
#### Parameters
name
Type: System..::..String
Name of the geometry.
startX
Type: System..::..Double
X coordinate of the first point.
startY
Type: System..::..Double
Y coordinate of the first point.
endX
Type: System..::..Double
X coordinate of the last point.
endY
Type: System..::..Double
Y coordinate of the last point.
#### Return Value
The geometry created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateSlantedRoughFinish Method

﻿
Collapse AllExpand All Members: Show All Members: Filtered Members: Filtered Members: Filtered
C#
Include Protected Members
Include Inherited Members
Xilog Maestro Scripting Language
IScripting..::..CreateSlantedRoughFinish Method
IScripting Interface See Also Send Feedback

# Overload List
Name Description
CreateSlantedRoughFinish(String, Double, Double, Int32, Double, String, TypeOfProcess, String, String, Double, Double, Double, Double)
Create a slanted milling operation by using the active geometry.

CreateSlantedRoughFinish(String, Double, Double, Int32, Double, String, TypeOfProcess, String, String, Int32, Double, Double, Double, Double)
Create a slanted milling operation by using the active geometry.

# See Also
IScripting Interface
IScripting Members
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateSlantedRoughFinish Method  String  Double  Double  Int32  Double  String    String  String  Double  Double  Double  Double

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateSlantedRoughFinish Method (String, Double, Double, Int32, Double, String, , String, String, Double, Double, Double, Double)
IScripting Interface See Also Send Feedback

Create a slanted milling operation by using the active geometry.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Operation CreateSlantedRoughFinish(
string name,
double angleA,
double angleB,
int toolApproach,
double depth,
string description,
TypeOfProcess typeOfProcess,
string tool,
string head,
double inputSpeed,
double rotSpeed,
double speed,
double overMaterial
)
```
#### Parameters
name
Type: System..::..String
Name of the operation.
angleA
Type: System..::..Double
Milling rotation angle (degrees).
angleB
Type: System..::..Double
Tool angle relative to the vertical plane (degrees).
toolApproach
Type: System..::..Int32

Entry side: type of approach of the tool with respect to the geometry.
0 - Tool is parallel with the positive X-axis of the absolute reference system (IC = 0).
1 - Tool is perpendicular to the programmed trajectory on the right-hand side of the feed path (IC = 1).
2 - Tool is perpendicular to the programmed trajectory on the left-hand side of the feed path (IC = 2).
3 - Tool is parallel to the tangent of the starting point of the programmed trajectory (IC = 3). The angle of the tool remains fixed during machining (fixed position).
4 - Tool is parallel to the tangent of the current point of the programmed trajectory (IC = 4). The tool remains parallel with the path during machining (interpolated position).

depth
Type: System..::..Double
Depth of the operation.
description
Type: System..::..String
Description of the operation (optional parameter).
typeOfProcess
Type: TypeOfProcess
Type of operation, if not set a generic operation will be created (optional parameter).
tool
Type: System..::..String
Tool, if null or -1, tool will be selected automatically (optional parameter).
head
Type: System..::..String
Head to be used, if null or -1 head will be selected automatically (optional parameter).
inputSpeed
Type: System..::..Double
Entry speed into piece. (V in XGO Xilog), if not set the value programmed in the tooling will be used (optional parameter).
rotSpeed
Type: System..::..Double
Rotation speed of tool (S in XG0 Xilog), if not set the value programmed in the tooling will be used (optional parameter).
speed
Type: System..::..Double
Milling speed, if not set the value programmed in the tooling will be used (optional parameter).
overMaterial
Type: System..::..Double
Overmaterial, if not set 0 will be used (optional parameter).
#### Return Value
The operation created.
# See Also
IScripting Interface
CreateSlantedRoughFinish Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateSlantedRoughFinish Method  String  Double  Double  Int32  Double  String    String  String  Int32  Double  Double  Double  Double

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateSlantedRoughFinish Method (String, Double, Double, Int32, Double, String, , String, String, Int32, Double, Double, Double, Double)
IScripting Interface See Also Send Feedback

Create a slanted milling operation by using the active geometry.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Operation CreateSlantedRoughFinish(
string name,
double angleA,
double angleB,
int toolApproach,
double depth,
string description,
TypeOfProcess typeOfProcess,
string tool,
string head,
int correction,
double inputSpeed,
double rotSpeed,
double speed,
double overMaterial
)
```
#### Parameters
name
Type: System..::..String
Name of the operation.
angleA
Type: System..::..Double
Milling rotation angle (degrees).
angleB
Type: System..::..Double
Tool angle relative to the vertical plane (degrees).
toolApproach
Type: System..::..Int32

Entry side: type of approach of the tool with respect to the geometry.
0 - Tool is parallel with the positive X-axis of the absolute reference system (IC = 0).
1 - Tool is perpendicular to the programmed trajectory on the right-hand side of the feed path (IC = 1).
2 - Tool is perpendicular to the programmed trajectory on the left-hand side of the feed path (IC = 2).
3 - Tool is parallel to the tangent of the starting point of the programmed trajectory (IC = 3). The angle of the tool remains fixed during machining (fixed position).
4 - Tool is parallel to the tangent of the current point of the programmed trajectory (IC = 4). The tool remains parallel with the path during machining (interpolated position).

depth
Type: System..::..Double
Depth of the operation.
description
Type: System..::..String
Description of the operation (optional parameter).
typeOfProcess
Type: TypeOfProcess
Type of operation, if not set a generic operation will be created (optional parameter).
tool
Type: System..::..String
Tool, if null or -1, tool will be selected automatically (optional parameter).
head
Type: System..::..String
Head to be used, if null or -1 head will be selected automatically (optional parameter).
correction
Type: System..::..Int32
Tool correction.
C = 0, Tool center (default)
C = 1, left correction
C = 2, right correction
C = 3, in depth correction
C = 13, left correction + in depth correction
C = 23, right correction + in depth correction

inputSpeed
Type: System..::..Double
Entry speed into piece. (V in XGO Xilog), if not set the value programmed in the tooling will be used (optional parameter).
rotSpeed
Type: System..::..Double
Rotation speed of tool (S in XG0 Xilog), if not set the value programmed in the tooling will be used (optional parameter).
speed
Type: System..::..Double
Milling speed, if not set the value programmed in the tooling will be used (optional parameter).
overMaterial
Type: System..::..Double
Overmaterial, if not set 0 will be used (optional parameter).
#### Return Value
The operation created.
# See Also
IScripting Interface
CreateSlantedRoughFinish Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateToolpath3D Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateToolpath3D Method
IScripting Interface See Also Send Feedback

Create a 3D toolpath. The start point is used as the starting point for subsequent segments.
Angles ZRotation and XRotation that defines tool axis rotation on the start point
are specified when creating the operation by using the method Create3DRoughFinish()

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
ToolPath3D CreateToolpath3D(
string name,
double startX,
double startY,
double startZ
)
```
#### Parameters
name
Type: System..::..String
Name of the toolpath.
startX
Type: System..::..Double
X coordinate of the first point of the toolpath.
startY
Type: System..::..Double
Y coordinate of the first point of the toolpath.
startZ
Type: System..::..Double
Z coordinate of the first point of the toolpath.
#### Return Value
The toolpath created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateToolpath Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateToolpath Method
IScripting Interface See Also Send Feedback

Create a toolpath. The start point is used as the starting point for subsequent segments/arcs.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
ToolPath CreateToolpath(
string name,
double startX,
double startY,
double startZ
)
```
#### Parameters
name
Type: System..::..String
Name of the toolpath.
startX
Type: System..::..Double
X coordinate of the first point of the toolpath.
startY
Type: System..::..Double
Y coordinate of the first point of the toolpath.
startZ
Type: System..::..Double
Z coordinate of the first point of the toolpath.
#### Return Value
The toolpath created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateTrimming Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateTrimming Method
IScripting Interface See Also Send Feedback

Create a trimming operation by using the active geometry.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Operation CreateTrimming(
string name,
int toolApproach,
double depth,
string description,
TypeOfProcess typeOfProcess,
string tool,
string head,
int correction,
double inputSpeed,
double rotSpeed,
double speed,
double overMaterial
)
```
#### Parameters
name
Type: System..::..String
Name of the operation.
toolApproach
Type: System..::..Int32

Entry side: type of approach of the tool with respect to the geometry.
0 - Tool is parallel with the positive X-axis of the absolute reference system (IC = 0).
1 - Tool is perpendicular to the programmed trajectory on the right-hand side of the feed path (IC = 1).
2 - Tool is perpendicular to the programmed trajectory on the left-hand side of the feed path (IC = 2).
3 - Tool is parallel to the tangent of the starting point of the programmed trajectory (IC = 3). The angle of the tool remains fixed during machining (fixed position).
4 - Tool is parallel to the tangent of the current point of the programmed trajectory (IC = 4). The tool remains parallel with the path during machining (interpolated position).

depth
Type: System..::..Double
Depth of the operation.
description
Type: System..::..String
Description of the operation (optional parameter).
typeOfProcess
Type: TypeOfProcess
Type of operation, if not set a generic operation will be created (optional parameter).
tool
Type: System..::..String
Tool, if null or -1, tool will be selected automatically (optional parameter).
head
Type: System..::..String
Head to be used, if null or -1 head will be selected automatically (optional parameter).
correction
Type: System..::..Int32
Tool correction.
C = 0, Tool center (default)
C = 1, left correction
C = 2, right correction
C = 3, in depth correction
C = 13, left correction + in depth correction
C = 23, right correction + in depth correction

inputSpeed
Type: System..::..Double
Entry speed into piece. (V in XGO Xilog), if not set the value programmed in the tooling will be used (optional parameter).
rotSpeed
Type: System..::..Double
Rotation speed of tool (S in XG0 Xilog), if not set the value programmed in the tooling will be used (optional parameter).
speed
Type: System..::..Double
Milling speed, if not set the value programmed in the tooling will be used (optional parameter).
overMaterial
Type: System..::..Double
Overmaterial, if not set 0 will be used (optional parameter).
#### Return Value
The operation created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateWorkPieceProbing Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateWorkPieceProbing Method
IScripting Interface See Also Send Feedback

Create the NC function workpiece probing.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Operation CreateWorkPieceProbing(
string name,
double x,
double y,
string tool,
string head,
int type,
int headReturnAfterProbing
)
```
#### Parameters
name
Type: System..::..String
Name of the machine function.
x
Type: System..::..Double
Coordinate X of the point to feel referring to the active workplane.
y
Type: System..::..Double
Coordinate Y of the point to feel referring to the active workplane.
tool
Type: System..::..String
Tool, if null or -1, tool will be selected automatically (optional parameter).
head
Type: System..::..String
Head to be used, if null or -1 head will be selected automatically (optional parameter).
type
Type: System..::..Int32
Type of probing (0 = probe all main faces of the workpiece, 1 = probe a specific point)
headReturnAfterProbing
Type: System..::..Int32
Define the rising of the head after feeling (0 = head moves up to the Z + limit switch, 1 = head remains at the probing Z, 2 = head moves up to the brushing over the workpiece)
#### Return Value
[Missing <returns> documentation for "M:ScmGroup.XCam.Scripting.IScripting.CreateWorkPieceProbing(System.String,System.Double,System.Double,System.String,System.String,System.Int32,System.Int32)"]
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateWorkplan Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateWorkplan Method
IScripting Interface See Also Send Feedback

Create a workplan

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Workplan CreateWorkplan(
string name
)
```
#### Parameters
name
Type: System..::..String
Name of the workplan.
#### Return Value
The workplan created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateWorkplane Method

﻿
Collapse AllExpand All Members: Show All Members: Filtered Members: Filtered Members: Filtered
C#
Include Protected Members
Include Inherited Members
Xilog Maestro Scripting Language
IScripting..::..CreateWorkplane Method
IScripting Interface See Also Send Feedback

# Overload List
Name Description
CreateWorkplane(String, Double)
Create a workplane parallel to the active workplane translated along the Z axis of the starting (active) plane by using offsetZ.

CreateWorkplane(String, Double, Double, Double, Double, Double)
Create a workplane given its origin and rotation with respect of Z and X axis.

CreateWorkplane(String, Double, Double, Double, Double, Double, Double, Double, Double, Double)
Create a workplane given tree points

# See Also
IScripting Interface
IScripting Members
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateWorkplane Method  String  Double

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateWorkplane Method (String, Double)
IScripting Interface See Also Send Feedback

Create a workplane parallel to the active workplane translated along the Z axis of the starting (active) plane by using offsetZ.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Workplane CreateWorkplane(
string name,
double offsetZ
)
```
#### Parameters
name
Type: System..::..String
Name of the workplane.
offsetZ
Type: System..::..Double
Offset along Z axis of the new workplane with respect of the active plane.
#### Return Value
The workplane created.
# See Also
IScripting Interface
CreateWorkplane Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateWorkplane Method  String  Double  Double  Double  Double  Double

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateWorkplane Method (String, Double, Double, Double, Double, Double)
IScripting Interface See Also Send Feedback

Create a workplane given its origin and rotation with respect of Z and X axis.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Workplane CreateWorkplane(
string name,
double X0,
double Y0,
double Z0,
double ZRotation,
double XRotation
)
```
#### Parameters
name
Type: System..::..String
Name of the workplane.
X0
Type: System..::..Double
X coordinate of the origin.
Y0
Type: System..::..Double
Y coordinate of the origin.
Z0
Type: System..::..Double
Z coordinate of the origin.
ZRotation
Type: System..::..Double
Angle of rotation around Z axis.
XRotation
Type: System..::..Double
Angle of rotation around X axis.
#### Return Value
The workplane created.
# See Also
IScripting Interface
CreateWorkplane Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateWorkplane Method  String  Double  Double  Double  Double  Double  Double  Double  Double  Double

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateWorkplane Method (String, Double, Double, Double, Double, Double, Double, Double, Double, Double)
IScripting Interface See Also Send Feedback

Create a workplane given tree points

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Workplane CreateWorkplane(
string name,
double p1X,
double p1Y,
double p1Z,
double p2X,
double p2Y,
double p2Z,
double p3X,
double p3Y,
double p3Z
)
```
#### Parameters
name
Type: System..::..String
Name of the workplane.
p1X
Type: System..::..Double
X coordinate of the first point.
p1Y
Type: System..::..Double
Y coordinate of the first point.
p1Z
Type: System..::..Double
Z coordinate of the first point.
p2X
Type: System..::..Double
X coordinate of the second point.
p2Y
Type: System..::..Double
Y coordinate of the second point.
p2Z
Type: System..::..Double
Z coordinate of the second point.
p3X
Type: System..::..Double
X coordinate of the third point.
p3Y
Type: System..::..Double
Y coordinate of the third point.
p3Z
Type: System..::..Double
Z coordinate of the third point.
#### Return Value
The workplane created.
# See Also
IScripting Interface
CreateWorkplane Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

