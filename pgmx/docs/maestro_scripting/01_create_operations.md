# Operaciones de Maquinado (Create*)

---

## CreateBlockingProfile Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateBlockingProfile Method
IScripting Interface See Also Send Feedback

Create a blocking profile. The start point is used as the starting point for subsequent segments/arcs.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
BlockingProfile CreateBlockingProfile(
string name,
double startX,
double startY,
double offset
)
```
#### Parameters
name
Type: System..::..String
Name of the blocking profile.
startX
Type: System..::..Double
X coordinate of the first point of the blocking profile.
startY
Type: System..::..Double
Y coordinate of the first point of the blocking profile.
offset
Type: System..::..Double
Offset with respect of the blocking profile.
#### Return Value
The blocking profile created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateChamfer Method

﻿
Collapse AllExpand All Members: Show All Members: Filtered Members: Filtered Members: Filtered
C#
Include Protected Members
Include Inherited Members
Xilog Maestro Scripting Language
IScripting..::..CreateChamfer Method
IScripting Interface See Also Send Feedback

# Overload List
Name Description
CreateChamfer(String, String, Double, Double, Int32)
Create a chamfer between two geometries identified by their name.

CreateChamfer(String, Int32, Int32, Double, Double, Int32)
Create a chamfer between two adjacent elements of the active polyline.

CreateChamfer(String, String, String, Double, Double, Int32)
Create a chamfer between two adjacent elements of the active polyline.

CreateChamfer(String, Double, Double, Double, Int32, String, TypeOfProcess, String, String, Double, Double, Double, Double)
Create a chamfer operation by using the active geometry.

# See Also
IScripting Interface
IScripting Members
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateChamfer Method  String  Double  Double  Double  Int32  String    String  String  Double  Double  Double  Double

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateChamfer Method (String, Double, Double, Double, Int32, String, , String, String, Double, Double, Double, Double)
IScripting Interface See Also Send Feedback

Create a chamfer operation by using the active geometry.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Operation CreateChamfer(
string name,
double chamferWidth,
double chamferHeight,
double overcutLength,
int toolPosition,
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
chamferWidth
Type: System..::..Double
Width of the chamfer.
chamferHeight
Type: System..::..Double
Height of the chamfer.
overcutLength
Type: System..::..Double
Overcut length of the chamfer.
toolPosition
Type: System..::..Int32

Tool position: position of the tool with respect to the geometry.
0 - Tool is at the left of the geometry on top plane (IC = 0).
1 - Tool is at the left of the geometry projected on bottom plane (IC = 1).
2 - Tool is at the right of the geometry on top plane (IC = 2).
3 - Tool is at the right of the geometry projected on bottom plane (IC = 3)

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
CreateChamfer Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateChamfer Method  String  Int32  Int32  Double  Double  Int32

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateChamfer Method (String, Int32, Int32, Double, Double, Int32)
IScripting Interface See Also Send Feedback

Create a chamfer between two adjacent elements of the active polyline.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Polyline CreateChamfer(
string geom,
int element1,
int element2,
double length1,
double length2,
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
Index of the second element.
length1
Type: System..::..Double
Length of the first segment of the chamfer.
length2
Type: System..::..Double
Length of the second segment of the chamfer.
option
Type: System..::..Int32
Creation options:
option = 0 => Chamfer given two lengths.

#### Return Value
The polyline with the chamfer.
# See Also
IScripting Interface
CreateChamfer Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateChamfer Method  String  String  Double  Double  Int32

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateChamfer Method (String, String, Double, Double, Int32)
IScripting Interface See Also Send Feedback

Create a chamfer between two geometries identified by their name.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Segment CreateChamfer(
string geom1,
string geom2,
double length1,
double length2,
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
length1
Type: System..::..Double
Length of the first segment of the chamfer.
length2
Type: System..::..Double
Length of the second segment of the chamfer.
option
Type: System..::..Int32
Creation options:
option = 0 => Chamfer given two lengths.

#### Return Value
The geometry (chamfer) created.
# See Also
IScripting Interface
CreateChamfer Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateChamfer Method  String  String  String  Double  Double  Int32

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateChamfer Method (String, String, String, Double, Double, Int32)
IScripting Interface See Also Send Feedback

Create a chamfer between two adjacent elements of the active polyline.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Polyline CreateChamfer(
string geom,
string element1,
string element2,
double length1,
double length2,
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
length1
Type: System..::..Double
Length of the first segment of the chamfer.
length2
Type: System..::..Double
Length of the second segment of the chamfer.
option
Type: System..::..Int32
Creation options:
option = 0 => Chamfer given two lengths.

#### Return Value
The polyline with the chamfer.
# See Also
IScripting Interface
CreateChamfer Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateContourPocket Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateContourPocket Method
IScripting Interface See Also Send Feedback

Create a countour pocket operation by using the active geometry.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Operation CreateContourPocket(
string name,
double depth,
string description,
TypeOfProcess typeOfProcess,
string tool,
string head,
double inputSpeed,
double rotSpeed,
double speed,
double overlap,
bool finalPass,
params string[] bossNames
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
inputSpeed
Type: System..::..Double
Entry speed into piece. (V in XGO Xilog), if not set the value programmed in the tooling will be used (optional parameter).
rotSpeed
Type: System..::..Double
Rotation speed of tool (S in XG0 Xilog), if not set the value programmed in the tooling will be used (optional parameter).
speed
Type: System..::..Double
Milling speed, if not set the value programmed in the tooling will be used (optional parameter).
overlap
Type: System..::..Double
Overlap (%).
finalPass
Type: System..::..Boolean
If true a final pass will be performed.
bossNames
Type: array<System..::..String>[]()[][]
Name of geometries which define bosses/islands (optional parameter).
#### Return Value
The operation created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
IScripting..::..CreateRoughFinish(String, Double, String, TypeOfProcess, String, String, Int32, Double, Double, Double, Double)
IScripting..::..CreateContour(String, Double, Int32, Int32, String, TypeOfProcess, String, String, Int32, Double, Double, Double, Double)
SCM Group S.P.A

---

## CreateDrill Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateDrill Method
IScripting Interface See Also Send Feedback

Create a drilling operation.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Operation CreateDrill(
string name,
double x,
double y,
double depth,
double diameter,
string description,
TypeOfProcess typeOfProcess,
string tool,
string head,
int dischargeSteps,
double rotSpeed,
double boringSpeed,
string kindOfHole,
double taperHeight,
Nullable<double> securityQuote
)
```
#### Parameters
name
Type: System..::..String
Name of the operation.
x
Type: System..::..Double
Coordinate X of the hole.
y
Type: System..::..Double
Coordinate Y of the hole.
depth
Type: System..::..Double
Depth of the operation.
diameter
Type: System..::..Double
Hole diameter.
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
dischargeSteps
Type: System..::..Int32
Number of chip discharge steps.
rotSpeed
Type: System..::..Double
Rotation speed of tool (S in Xilog), if not set the value programmed in the tooling will be used (optional parameter).
boringSpeed
Type: System..::..Double
Boring speed (V in Xilog).
kindOfHole
Type: System..::..String
Hole type: P=flat, L=lance, S=taper (optional parameter: default is P).
taperHeight
Type: System..::..Double
Taper height.
securityQuote
Type: System..::..Nullable<(Of <(<'Double>)>)>
Security quote
#### Return Value
The operation created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateIso Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateIso Method
IScripting Interface See Also Send Feedback

Create the NC function ISO operation.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Operation CreateIso(
string name,
string instruction,
string optionalParameters,
bool isXiso
)
```
#### Parameters
name
Type: System..::..String
The name.
instruction
Type: System..::..String
The Iso istruction to execute.
optionalParameters
Type: System..::..String
optional parameters.
isXiso
Type: System..::..Boolean
Xiso flag (optional parameter).
#### Return Value
[Missing <returns> documentation for "M:ScmGroup.XCam.Scripting.IScripting.CreateIso(System.String,System.String,System.String,System.Boolean)"]
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateMultiStepDrillingStrategy Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateMultiStepDrillingStrategy Method
IScripting Interface See Also Send Feedback

Create the machining strategy for a multistep drilling (will be valid only with the first operation created after strategy creation).

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
MultiStepDrillingStrategy CreateMultiStepDrillingStrategy(
bool isStepDepth,
int stepNumber,
double stepDepth
)
```
#### Parameters
isStepDepth
Type: System..::..Boolean
If true step depth parameter is used, else false number of steps parameter is used.
stepNumber
Type: System..::..Int32
Number of steps.
stepDepth
Type: System..::..Double
Depth of each step.
#### Return Value
The strategy created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreatePark Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreatePark Method
IScripting Interface See Also Send Feedback

Create the NC function park.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Operation CreatePark(
string name,
string stopType,
Nullable<bool> toMinQuote
)
```
#### Parameters
name
Type: System..::..String
Name of the machine function.
stopType
Type: System..::..String
Type of stop: Nothing (no stop), NoUnlock (Stop with standby for start), Unlock (Stop with workpiece release and standby for start)
toMinQuote
Type: System..::..Nullable<(Of <(<'Boolean>)>)>
if true park will be done on the left side.
#### Return Value
The machine function created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateSingleStepDrillingStrategy Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateSingleStepDrillingStrategy Method
IScripting Interface See Also Send Feedback

Create the machining strategy for a single step drilling operation.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
SingleStepDrillingStrategy CreateSingleStepDrillingStrategy()
```
#### Return Value
The strategy created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateSlantedDrill Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateSlantedDrill Method
IScripting Interface See Also Send Feedback

Create a slanted drilling operation.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Operation CreateSlantedDrill(
string name,
double x,
double y,
double z,
double angleA,
double angleB,
double depth,
double diameter,
string description,
TypeOfProcess typeOfProcess,
string tool,
string head,
int dischargeSteps,
double rotSpeed,
double boringSpeed,
string kindOfHole,
double taperHeight,
Nullable<double> securityQuote
)
```
#### Parameters
name
Type: System..::..String
Name of the operation.
x
Type: System..::..Double
X coordinate of the hole.
y
Type: System..::..Double
Y coordinate of the hole.
z
Type: System..::..Double
Z coordinate of the hole (use null for z = piece height).
angleA
Type: System..::..Double
Tool angle with respect to the horizontal plane (degrees).
angleB
Type: System..::..Double
Tool angle with respect to the vertical plane (degrees).
depth
Type: System..::..Double
Depth of the operation.
diameter
Type: System..::..Double
Hole diameter.
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
dischargeSteps
Type: System..::..Int32
Number of chip discharge steps.
rotSpeed
Type: System..::..Double
Rotation speed of tool (S in Xilog), if not set the value programmed in the tooling will be used (optional parameter).
boringSpeed
Type: System..::..Double
Boring speed (V in Xilog).
kindOfHole
Type: System..::..String
Hole type: P=flat, L=lance, S=taper (optional parameter: default is P).
taperHeight
Type: System..::..Double
Taper height.
securityQuote
Type: System..::..Nullable<(Of <(<'Double>)>)>
Security quote
#### Return Value
The operation created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## CreateSlot Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..CreateSlot Method
IScripting Interface See Also Send Feedback

Create a slot operation

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Operation CreateSlot(
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
double overMaterial,
double angle,
Nullable<double> endDepth
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
angle
Type: System..::..Double
Angle of the operation from the workplane (optional parameter).
endDepth
Type: System..::..Nullable<(Of <(<'Double>)>)>
End Depth of the operation (optional parameter).
#### Return Value
The operation created.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

