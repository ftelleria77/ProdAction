# Herramientas y Piezas

---

## ActiveWorkpiece Property

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..ActiveWorkpiece Property
IScripting Interface See Also Send Feedback

The workpiece to which are added next machining operation, geometries, workplans and workplanes
by using methods provided by the script language.
When adding a new workpiece, it automatically becomes the active workpiece.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Workpiece ActiveWorkpiece { get; }
```
#### Field Value
The active workpiece.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## ActiveWorkplan Property

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..ActiveWorkplan Property
IScripting Interface See Also Send Feedback

The workplan to which are added next machining operation, geometries, and workplanes
by using methods provided by the script language.
When adding a new workplan, it automatically becomes the active workplan.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Workplan ActiveWorkplan { get; }
```
#### Field Value
The active workplan.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## ActiveWorkplane Property

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..ActiveWorkplane Property
IScripting Interface See Also Send Feedback

The workplane to which are added next geometries by using methods provided by the script language.
When adding a new workplane, it automatically becomes the active workplane.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Workplane ActiveWorkplane { get; }
```
#### Field Value
The active workplane.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## DeleteWorkpiece Method

﻿
Collapse AllExpand All Members: Show All Members: Filtered Members: Filtered Members: Filtered
C#
Include Protected Members
Include Inherited Members
Xilog Maestro Scripting Language
IScripting..::..DeleteWorkpiece Method
IScripting Interface See Also Send Feedback

# Overload List
Name Description
DeleteWorkpiece(Int32)
Delete a workpiece identified by the index.

DeleteWorkpiece(String)
Delete a workpiece identified by the name.

# See Also
IScripting Interface
IScripting Members
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## DeleteWorkpiece Method  Int32

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..DeleteWorkpiece Method (Int32)
IScripting Interface See Also Send Feedback

Delete a workpiece identified by the index.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
void DeleteWorkpiece(
int index
)
```
#### Parameters
index
Type: System..::..Int32
Index of the workpiece to delete.
# See Also
IScripting Interface
DeleteWorkpiece Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## DeleteWorkpiece Method  String

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..DeleteWorkpiece Method (String)
IScripting Interface See Also Send Feedback

Delete a workpiece identified by the name.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
void DeleteWorkpiece(
string name
)
```
#### Parameters
name
Type: System..::..String
Name of the workpiece to delete.
# See Also
IScripting Interface
DeleteWorkpiece Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## DeleteWorkplan Method

﻿
Collapse AllExpand All Members: Show All Members: Filtered Members: Filtered Members: Filtered
C#
Include Protected Members
Include Inherited Members
Xilog Maestro Scripting Language
IScripting..::..DeleteWorkplan Method
IScripting Interface See Also Send Feedback

# Overload List
Name Description
DeleteWorkplan(Int32)
Delete a workplan identified by the index.

DeleteWorkplan(String)
Delete a workplan identified by the name.

# See Also
IScripting Interface
IScripting Members
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## DeleteWorkplan Method  Int32

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..DeleteWorkplan Method (Int32)
IScripting Interface See Also Send Feedback

Delete a workplan identified by the index.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
void DeleteWorkplan(
int index
)
```
#### Parameters
index
Type: System..::..Int32
Index of the workplan to delete.
# See Also
IScripting Interface
DeleteWorkplan Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## DeleteWorkplan Method  String

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..DeleteWorkplan Method (String)
IScripting Interface See Also Send Feedback

Delete a workplan identified by the name.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
void DeleteWorkplan(
string name
)
```
#### Parameters
name
Type: System..::..String
Name of the workplan to delete.
# See Also
IScripting Interface
DeleteWorkplan Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## DeleteWorkplane Method

﻿
Collapse AllExpand All Members: Show All Members: Filtered Members: Filtered Members: Filtered
C#
Include Protected Members
Include Inherited Members
Xilog Maestro Scripting Language
IScripting..::..DeleteWorkplane Method
IScripting Interface See Also Send Feedback

# Overload List
Name Description
DeleteWorkplane(Int32)
Delete a workplane identified by the index.

DeleteWorkplane(String)
Delete a workplane identified by the name.

# See Also
IScripting Interface
IScripting Members
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## DeleteWorkplane Method  Int32

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..DeleteWorkplane Method (Int32)
IScripting Interface See Also Send Feedback

Delete a workplane identified by the index.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
void DeleteWorkplane(
int index
)
```
#### Parameters
index
Type: System..::..Int32
Index of the workplane to delete.
# See Also
IScripting Interface
DeleteWorkplane Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## DeleteWorkplane Method  String

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..DeleteWorkplane Method (String)
IScripting Interface See Also Send Feedback

Delete a workplane identified by the name.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
void DeleteWorkplane(
string name
)
```
#### Parameters
name
Type: System..::..String
Name of the workplane to delete.
# See Also
IScripting Interface
DeleteWorkplane Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## GetTool Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..GetTool Method
IScripting Interface See Also Send Feedback

Retrieve the tool identified by a specified name.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Tool GetTool(
string tool
)
```
#### Parameters
tool
Type: System..::..String
Name of the tool.
#### Return Value
The tool retrieved or null if the tool is not present in the tooling file currently selected.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## RenameWorkplan Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..RenameWorkplan Method
IScripting Interface See Also Send Feedback

Rename the active workplan.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Workplan RenameWorkplan(
string name
)
```
#### Parameters
name
Type: System..::..String
[Missing <param name="name"/> documentation for "M:ScmGroup.XCam.Scripting.IScripting.RenameWorkplan(System.String)"]
#### Return Value
[Missing <returns> documentation for "M:ScmGroup.XCam.Scripting.IScripting.RenameWorkplan(System.String)"]
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## SelectWorkpiece Method

﻿
Collapse AllExpand All Members: Show All Members: Filtered Members: Filtered Members: Filtered
C#
Include Protected Members
Include Inherited Members
Xilog Maestro Scripting Language
IScripting..::..SelectWorkpiece Method
IScripting Interface See Also Send Feedback

# Overload List
Name Description
SelectWorkpiece(Int32)
Select a workpiece as active workpiece.

SelectWorkpiece(String)
Select a workpiece as active workpiece.

# See Also
IScripting Interface
IScripting Members
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## SelectWorkpiece Method  Int32

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..SelectWorkpiece Method (Int32)
IScripting Interface See Also Send Feedback

Select a workpiece as active workpiece.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Workpiece SelectWorkpiece(
int index
)
```
#### Parameters
index
Type: System..::..Int32
Index of the workpiece to activate.
#### Return Value
The selected workpiece.
# See Also
IScripting Interface
SelectWorkpiece Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## SelectWorkpiece Method  String

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..SelectWorkpiece Method (String)
IScripting Interface See Also Send Feedback

Select a workpiece as active workpiece.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Workpiece SelectWorkpiece(
string name
)
```
#### Parameters
name
Type: System..::..String
Name of the workpiece to activate.
#### Return Value
The selected workpiece.
# See Also
IScripting Interface
SelectWorkpiece Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## SelectWorkplan Method

﻿
Collapse AllExpand All Members: Show All Members: Filtered Members: Filtered Members: Filtered
C#
Include Protected Members
Include Inherited Members
Xilog Maestro Scripting Language
IScripting..::..SelectWorkplan Method
IScripting Interface See Also Send Feedback

# Overload List
Name Description
SelectWorkplan(Int32)
Select a workplan as active workplan.

SelectWorkplan(String)
Select a workplan as active workplan.

# See Also
IScripting Interface
IScripting Members
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## SelectWorkplan Method  Int32

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..SelectWorkplan Method (Int32)
IScripting Interface See Also Send Feedback

Select a workplan as active workplan.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Workplan SelectWorkplan(
int index
)
```
#### Parameters
index
Type: System..::..Int32
Index of the workplan to activate.
#### Return Value
The workplan selected.
# See Also
IScripting Interface
SelectWorkplan Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## SelectWorkplan Method  String

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..SelectWorkplan Method (String)
IScripting Interface See Also Send Feedback

Select a workplan as active workplan.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Workplan SelectWorkplan(
string name
)
```
#### Parameters
name
Type: System..::..String
Name of the workplan to activate.
#### Return Value
The workplan selected.
# See Also
IScripting Interface
SelectWorkplan Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## SelectWorkplane Method

﻿
Collapse AllExpand All Members: Show All Members: Filtered Members: Filtered Members: Filtered
C#
Include Protected Members
Include Inherited Members
Xilog Maestro Scripting Language
IScripting..::..SelectWorkplane Method
IScripting Interface See Also Send Feedback

# Overload List
Name Description
SelectWorkplane(Int32)
Select a workplane as active workplane.

SelectWorkplane(String)
Select a workplane as active workplane.
By using the keywords "Top", "Bottom", "Right", "Left", "Front", "Back" the main workplanes of the active workpiece will be activated.

# See Also
IScripting Interface
IScripting Members
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## SelectWorkplane Method  Int32

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..SelectWorkplane Method (Int32)
IScripting Interface See Also Send Feedback

Select a workplane as active workplane.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Workplane SelectWorkplane(
int index
)
```
#### Parameters
index
Type: System..::..Int32
Index of the workplane to activate.
#### Return Value
The workplane selected.
# See Also
IScripting Interface
SelectWorkplane Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## SelectWorkplane Method  String

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..SelectWorkplane Method (String)
IScripting Interface See Also Send Feedback

Select a workplane as active workplane.
By using the keywords "Top", "Bottom", "Right", "Left", "Front", "Back" the main workplanes of the active workpiece will be activated.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
Workplane SelectWorkplane(
string name
)
```
#### Parameters
name
Type: System..::..String
Name of the workplane to activate.
#### Return Value
The workplane selected.
# See Also
IScripting Interface
SelectWorkplane Overload
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## SetMachiningParameters Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..SetMachiningParameters Method
IScripting Interface See Also Send Feedback

Initialize the machining parameters to be used for the execution of the program

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
MachiningParameters SetMachiningParameters(
string executionFields,
int repetitions,
long tableOptions,
long mechanicalOptions,
bool continuousCycle
)
```
#### Parameters
executionFields
Type: System..::..String
Working area (same as - in the Xilog H header instruction).
repetitions
Type: System..::..Int32
Number of repetitions (same as R in the Xilog H header instruction)
tableOptions
Type: System..::..Int64
Settings for blobking type (same as V in the Xilog H header instruction).
mechanicalOptions
Type: System..::..Int64
Settings for mechanical options (same as T in the Xilog H header instruction).
continuousCycle
Type: System..::..Boolean
Enable continuous cycle execution (same as C in the Xilog H header instruction).
#### Return Value
[Missing <returns> documentation for "M:ScmGroup.XCam.Scripting.IScripting.SetMachiningParameters(System.String,System.Int32,System.Int64,System.Int64,System.Boolean)"]
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## SetToolpathAttribute Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..SetToolpathAttribute Method
IScripting Interface See Also Send Feedback

Set of an attribute related to the active toolpath if any.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
void SetToolpathAttribute(
string name,
double value
)
```
#### Parameters
name
Type: System..::..String
Attribute name. Allowed values: "FEED", "ROT", "DEPTH"
value
Type: System..::..Double
Attribute value. For boolean attributes (ON/OFF) use 0 for OFF and a value different from zero for ON
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## SetWorkpieceSetupPosition Method

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting..::..SetWorkpieceSetupPosition Method
IScripting Interface See Also Send Feedback

Set the position of the active workpiece referring to the active workplan.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
void SetWorkpieceSetupPosition(
double x,
double y,
double z,
double zRot
)
```
#### Parameters
x
Type: System..::..Double
X position of the workpiece.
y
Type: System..::..Double
Y position of the workpiece.
z
Type: System..::..Double
Z position of the workpiece.
zRot
Type: System..::..Double
Rotation with respect to the Z axis of the workpiece.
# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

