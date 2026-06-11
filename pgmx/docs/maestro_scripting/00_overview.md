# IScripting — Visión General

---

## IScripting Interface

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
IScripting Interface
Members See Also Send Feedback

Interface that defines methods and properties available to build programs and macros.

Namespace: ScmGroup.XCam.Scripting
Assembly: ScmGroup.XCam.Scripting (in ScmGroup.XCam.Scripting.dll) Version: 1.0.0.0 (1.0.0.0)
# Syntax
C#

```
public interface IScripting
```
# See Also
IScripting Members
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## IScripting Members

﻿
Collapse AllExpand All Members: Show All Members: Filtered Members: Filtered Members: Filtered
C#
Include Protected Members
Include Inherited Members
Xilog Maestro Scripting Language
IScripting Members
IScripting Interface Methods Properties See Also Send Feedback

The IScripting type exposes the following members.
# Methods
Name Description
abs
Returns the absolute value of a specified number.

ABS
Returns the absolute value of a specified number.

acos
Returns the angle whose cosine is the specified number.

ACOS
Returns the angle whose cosine is the specified number.

AddArc2PointCenterToBlockingProfile
Add an arc given 2 point and center point to the active blocking profile.

AddArc2PointCenterToPolyline
Add an arc given 2 point and center point to the active polyline.

AddArc2PointCenterToToolpath
Add an arc given 2 point and center point to the active toolpath.

AddArc2PointRadiusToBlockingProfile
Add an arc given 2 points and radius to the active blocking profile.

AddArc2PointRadiusToPolyline
Add an arc given 2 points and radius to the active polyline.

AddArc2PointRadiusToToolpath
Add an arc given 2 points and radius to the active toolpath.

AddArc3PointsToBlockingProfile
Add an arc to the active blocking profile.

AddArc3PointsToPolyline
Add an arc to the active polyline.

AddArc3PointsToToolpath
Add an arc to the active toolpath.

AddArcCenterAngleToBlockingProfile
Add an arc given center point and angle swept by the arc to the active blocking profile.

AddArcCenterAngleToPolyline
Add an arc given center point and angle swept by the arc to the active polyline.

AddArcCenterAngleToToolpath
Add an arc given center point and angle swept by the arc to the active toolpath.

AddArcTanToBlockingProfile
Add an arc tangent to the previous element to the active blocking profile.

AddChamferToPolyline
Create a chamfer between two adjacent elements of the active polyline.

AddFilletToPolyline
Create a fillet between two adjacent elements of the active polyline.

AddSegmentTanToBlockingProfile
Add a line segment tangent to the previous element to the active blocking profile.

AddSegmentToBlockingProfile
Add a segment to the active blocking profile.

AddSegmentToPolyline
Add a segment to the active polyline.

AddSegmentToToolpath(Double, Double, Double)
Add a segment to the active toolpath.

AddSegmentToToolpath(Double, Double, Double, Nullable<(Of <<'(Double>)>>), Nullable<(Of <<'(Double>)>>))
Add a segment to the active 3D toolpath.

asin
Returns the angle whose sine is the specified number.

ASIN
Returns the angle whose sine is the specified number.

atan
Returns the angle whose tangent is the specified number.

ATAN
Returns the angle whose tangent is the specified number.

CloseBlockingProfile
Closes the current blocking profile with a line segment that connects the start and end points of the blocking profile.

ClosePolyline
Closes the current polyline with a line segment that connects the start and end points of the polyline.

cos
Returns the cosine of the specified angle.

COS
Returns the cosine of the specified angle.

Create3DRoughFinish
Create a 3D milling operation

CreateArc2PointCenter
Create an arc given 2 points and center point on the active workplane.

CreateArc2PointRadius
Create an arc given 2 points and radius on the active workplane.

CreateArc3Points
Create an arc given 3 points on the active workplane.

CreateArcCenterAngle
Create an arc given first point, center point and angle swept on the active workplane.

CreateBidirectionalMillingStrategy
Create the machining strategy for a milling with multiple passes in bidirectional way (will be valid only with the first operation created after strategy creation).

CreateBladeCut
Create a saw blade cut operation by using the active geometry.

CreateBlockingProfile
Create a blocking profile. The start point is used as the starting point for subsequent segments/arcs.

CreateChamfer(String, String, Double, Double, Int32)
Create a chamfer between two geometries identified by their name.

CreateChamfer(String, Int32, Int32, Double, Double, Int32)
Create a chamfer between two adjacent elements of the active polyline.

CreateChamfer(String, String, String, Double, Double, Int32)
Create a chamfer between two adjacent elements of the active polyline.

CreateChamfer(String, Double, Double, Double, Int32, String, TypeOfProcess, String, String, Double, Double, Double, Double)
Create a chamfer operation by using the active geometry.

CreateCircleCenterPoint(String, Double, Double, Double, Double)
Create a circle given center point and a point belonging on the circle on the active workplane.

CreateCircleCenterPoint(String, Double, Double, Double, Double, Boolean)
Create a circle given center point and a point belonging on the circle on the active workplane.

CreateCircleCenterRadius(String, Double, Double, Double)
Create a circle given center point and radius on the active workplane.

CreateCircleCenterRadius(String, Double, Double, Double, Boolean)
Create a circle given center point and radius on the active workplane.

CreateCombiflexUnloadUnitClamp
Create the NC function CombiflexUnloadUnitClamp operation.

CreateContour
Create a countour operation

CreateContourParallelStrategy
Create the machining strategy for a contour pocket machining.

CreateContourPocket
Create a countour pocket operation by using the active geometry.

CreateDrill
Create a drilling operation.

CreateEllipseCenterAxes
Create an ellipse with center point, major radius and minor radius on the active plane.

CreateFillet(String, String, Double, Int32)
Create a fillet between two geometries identified by their name.

CreateFillet(String, Int32, Int32, Double, Int32)
Create a fillet between two adjacent elements of the active polyline.

CreateFillet(String, String, String, Double, Int32)
Create a fillet between two adjacent elements of the active polyline.

CreateFinishedWorkpieceBox
Create a finished workpiece as a box. To define the raw and finished for the same workpiece use the same name.

CreateFinishedWorkpieceFromExtrusion
Create a finished workpiece as a solid extrusion along Z axis. The active geometry representing the boundary must be closed.

CreateHelicMillingStrategy
Create the machining strategy for a milling with an helic toolpath (is valid only with the first operation created after strategy creation).

CreateIso
Create the NC function ISO operation.

CreateMessage
Create the NC function message.

CreateMultiStepDrillingStrategy
Create the machining strategy for a multistep drilling (will be valid only with the first operation created after strategy creation).

CreateNullOperation
Create the NC function null operation.

CreatePark
Create the NC function park.

CreatePattern
Create a pattern of an operation.

CreatePlaneCutterLocationStrategy
Create the machining strategy for a 3D machininga operation with a fixed tool direction

CreatePolyline
Create a polyline on the active workplane. The start point is used as the starting point for subsequent segments/arcs.

CreateRawWorkpiece
Create a workpiece as a box.

CreateRawWorkpieceBox
Create a raw workpiece as a box. To define the raw and finished for the same workpiece use the same name.

CreateRawWorkpieceFromExtrusion
Create a workpiece as a solid extrusion along Z axis. The active geometry representing the boundary must be closed.

CreateRoughFinish
Create a milling operation by using the active geometry.

CreateScraping
Create a scraping operation by using the active geometry.

CreateSectioningMillingStrategy
Create the machining strategy for a sectioning milling (will be valid only with the first operation created after strategy creation).

CreateSegment
Create a line segment on the active workplane

CreateSingleStepDrillingStrategy
Create the machining strategy for a single step drilling operation.

CreateSlantedDrill
Create a slanted drilling operation.

CreateSlantedRoughFinish(String, Double, Double, Int32, Double, String, TypeOfProcess, String, String, Double, Double, Double, Double)
Create a slanted milling operation by using the active geometry.

CreateSlantedRoughFinish(String, Double, Double, Int32, Double, String, TypeOfProcess, String, String, Int32, Double, Double, Double, Double)
Create a slanted milling operation by using the active geometry.

CreateSlot
Create a slot operation

CreateToolpath
Create a toolpath. The start point is used as the starting point for subsequent segments/arcs.

CreateToolpath3D
Create a 3D toolpath. The start point is used as the starting point for subsequent segments.
Angles ZRotation and XRotation that defines tool axis rotation on the start point
are specified when creating the operation by using the method Create3DRoughFinish()

CreateTrimming
Create a trimming operation by using the active geometry.

CreateUnidirectionalMillingStrategy
Create the machining strategy for a milling with multiple passes in unidirectiona way (will be valid only with the first operation created after strategy creation).

CreateWorkPieceProbing
Create the NC function workpiece probing.

CreateWorkplan
Create a workplan

CreateWorkplane(String, Double)
Create a workplane parallel to the active workplane translated along the Z axis of the starting (active) plane by using offsetZ.

CreateWorkplane(String, Double, Double, Double, Double, Double)
Create a workplane given its origin and rotation with respect of Z and X axis.

CreateWorkplane(String, Double, Double, Double, Double, Double, Double, Double, Double, Double)
Create a workplane given tree points

DEF(Nullable<(Of <<'(Double>)>>))
Check if the variable has a valid value

DEF(String)
Check if the variable has a valid value

DeleteGeometry(Int32)
Delete a geometry identified by the index.

DeleteGeometry(String)
Delete a geometry identified by the name.

DeleteOperation(Int32)
Delete the operation identified by the index.

DeleteOperation(String)
Delete the operation identified by the name.

DeleteToolpath(Int32)
Delete a toopath identified by the index.

DeleteToolpath(String)
Delete a toopath identified by the name.

DeleteWorkpiece(Int32)
Delete a workpiece identified by the index.

DeleteWorkpiece(String)
Delete a workpiece identified by the name.

DeleteWorkplan(Int32)
Delete a workplan identified by the index.

DeleteWorkplan(String)
Delete a workplan identified by the name.

DeleteWorkplane(Int32)
Delete a workplane identified by the index.

DeleteWorkplane(String)
Delete a workplane identified by the name.

ExecMacro
Execute a macro.

exp
Returns e raised to the specified power.

EXP
Returns e raised to the specified power.

GetTool
Retrieve the tool identified by a specified name.

GetVersion
Read the version of Maestro executing the macro

ln
Returns the natural (base e) logarithm of a specified number.

LN
Returns the natural (base e) logarithm of a specified number.

log10
Returns the base 10 logarithm of a specified number.

LOG10
Returns the base 10 logarithm of a specified number.

Mirror
Mirror the object identified by the parameter 'name'.

NDEF(Nullable<(Of <<'(Double>)>>))
Check if the variable has a valid value

NDEF(String)
Check if the variable has a valid value

pow
Returns a specified number raised to the specified power.

POW
Returns a specified number raised to the specified power.

Print
Print an error message

rd
Returns the largest integral value less than or equal to the specified decimal number

RD
Returns the largest integral value less than or equal to the specified decimal number

RenameWorkplan
Rename the active workplan.

ResetApproachStrategy
Reset the active approach strategy.

ResetAuxiliaryHood
Reset the auxiliary hood position

ResetDustpan
Disable the NC function for the dustpan.

ResetJerk
Reset the machine function Jerk.

ResetJerk3D
Reset the machine function Jerk3D.

ResetPattern
Reset the active pattern.

ResetPneumaticHood
Reset the last position for the hood and enable automatic positioning.

ResetRetractStrategy
Reset the active retract strategy.

Rotate
Rotate the object identified by the parameter 'name'.

ru
Returns the smallest integral value that is greater than or equal to the specified input value

RU
Returns the smallest integral value that is greater than or equal to the specified input value

SelectGeometry(Int32)
Select a geometry as active geometry.

SelectGeometry(String)
Select a geometry as active geometry.

SelectOperation(Int32)
Select an operation as active operation.

SelectOperation(String)
Select an operation as active operation.

SelectToolpath(Int32)
Select a toolpath as active toolpath.

SelectToolpath(String)
Select a toolpath as active toolpath.

SelectWorkpiece(Int32)
Select a workpiece as active workpiece.

SelectWorkpiece(String)
Select a workpiece as active workpiece.

SelectWorkplan(Int32)
Select a workplan as active workplan.

SelectWorkplan(String)
Select a workplan as active workplan.

SelectWorkplane(Int32)
Select a workplane as active workplane.

SelectWorkplane(String)
Select a workplane as active workplane.
By using the keywords "Top", "Bottom", "Right", "Left", "Front", "Back" the main workplanes of the active workpiece will be activated.

SetApproachSecurityDistance
Set the approach security distance

SetApproachStrategy
Set the approach strategy.

SetAttribute
Set of an attribute related to the active geometry. Tipically, it is used before an operation added to the geometry.

SetAuxiliaryHoodPosition
Set the position of the auxiliary hood.

SetBrakes
Set the active brakes for the next operation.

SetDustpanOffset(Double)
Set the dustpan offset

SetDustpanOffset(Double, Nullable<(Of <<'(Int32>)>>), Nullable<(Of <<'(Boolean>)>>))
Enable the NC function for the dustpan.

SetDustpanPosition
Set the duspan position

SetJerk
Set the machine function Jerk in a modal way.

SetJerk3D
Set the machine function Jerk3D in a modal way.

SetMachiningParameters
Initialize the machining parameters to be used for the execution of the program

SetMirror
Set the mirror tranformation to enable

SetMirrorX
Set the mirror tranformation with respect to X axis to enable

SetMirrorY
Set the mirror tranformation with respect to Y axis to enable

SetPneumaticHoodPosition
Disable the automatic setting for the pneumatic hood and set its position.

SetRetractSecurityDistance
Set the retract security distance

SetRetractStrategy
Set the retract strategy.

SetRotation
Set the rotation tranformation to enable.

SetToolpathAttribute
Set of an attribute related to the active toolpath if any.

SetTranslation
Set the translation tranformation to enable.

SetUnrollHeadMode
Set the 5 axis unroll head mode

SetUnrollHeadRadiusMultiplier
Set the 5 axis unroll head mode radius multiplier

SetWorkpieceSetupPosition
Set the position of the active workpiece referring to the active workplan.

sin
Returns the sine of the specified angle.

SIN
Returns the sine of the specified angle.

sqrt
Returns the square root of a specified number.

SQRT
Returns the square root of a specified number.

tan
Returns the tangent of the specified angle.

TAN
Returns the tangent of the specified angle.

V
Get the value of a variabl double? (pX, pY, ecc...) or 0 if the variable is not defined

VALUE
Get the value of a variabl double? (pX, pY, ecc...) or 0 if the variable is not defined

# Properties
Name Description
ActiveGeometry
The active geometry. When adding a new geometry, it automatically becomes the active geometry.
When adding a new geometry, it automatically becomes the active geometry.

ActiveLeadInOut
The lead in-out (approach-rectract) properties active.
These property is modal and reamins active until it's modified.

ActiveMachineFunctions
Set of all the active machine functions. These functions are modal and are applied to all the machining
operations until they are reset.
Machine functions are set and reset by using methods provided by the script language.

ActiveOperation
The last machining operation added to the program.
When adding a new machining operation, it automatically becomes the active machining operation.

ActivePattern
The active pattern. If null is considered inactive.
It remains active until it is reset.

ActiveToolpath
The active toolpath. It can be used to add toolpath segments to the active machining operation.

ActiveWorkpiece
The workpiece to which are added next machining operation, geometries, workplans and workplanes
by using methods provided by the script language.
When adding a new workpiece, it automatically becomes the active workpiece.

ActiveWorkplan
The workplan to which are added next machining operation, geometries, and workplanes
by using methods provided by the script language.
When adding a new workplan, it automatically becomes the active workplan.

ActiveWorkplane
The workplane to which are added next geometries by using methods provided by the script language.
When adding a new workplane, it automatically becomes the active workplane.

# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## IScripting Methods

﻿
Collapse AllExpand All Members: Show All Members: Filtered Members: Filtered Members: Filtered
C#
Include Protected Members
Include Inherited Members
Xilog Maestro Scripting Language
IScripting Methods
IScripting Interface See Also Send Feedback

The IScripting type exposes the following members.
# Methods
Name Description
abs
Returns the absolute value of a specified number.

ABS
Returns the absolute value of a specified number.

acos
Returns the angle whose cosine is the specified number.

ACOS
Returns the angle whose cosine is the specified number.

AddArc2PointCenterToBlockingProfile
Add an arc given 2 point and center point to the active blocking profile.

AddArc2PointCenterToPolyline
Add an arc given 2 point and center point to the active polyline.

AddArc2PointCenterToToolpath
Add an arc given 2 point and center point to the active toolpath.

AddArc2PointRadiusToBlockingProfile
Add an arc given 2 points and radius to the active blocking profile.

AddArc2PointRadiusToPolyline
Add an arc given 2 points and radius to the active polyline.

AddArc2PointRadiusToToolpath
Add an arc given 2 points and radius to the active toolpath.

AddArc3PointsToBlockingProfile
Add an arc to the active blocking profile.

AddArc3PointsToPolyline
Add an arc to the active polyline.

AddArc3PointsToToolpath
Add an arc to the active toolpath.

AddArcCenterAngleToBlockingProfile
Add an arc given center point and angle swept by the arc to the active blocking profile.

AddArcCenterAngleToPolyline
Add an arc given center point and angle swept by the arc to the active polyline.

AddArcCenterAngleToToolpath
Add an arc given center point and angle swept by the arc to the active toolpath.

AddArcTanToBlockingProfile
Add an arc tangent to the previous element to the active blocking profile.

AddChamferToPolyline
Create a chamfer between two adjacent elements of the active polyline.

AddFilletToPolyline
Create a fillet between two adjacent elements of the active polyline.

AddSegmentTanToBlockingProfile
Add a line segment tangent to the previous element to the active blocking profile.

AddSegmentToBlockingProfile
Add a segment to the active blocking profile.

AddSegmentToPolyline
Add a segment to the active polyline.

AddSegmentToToolpath(Double, Double, Double)
Add a segment to the active toolpath.

AddSegmentToToolpath(Double, Double, Double, Nullable<(Of <<'(Double>)>>), Nullable<(Of <<'(Double>)>>))
Add a segment to the active 3D toolpath.

asin
Returns the angle whose sine is the specified number.

ASIN
Returns the angle whose sine is the specified number.

atan
Returns the angle whose tangent is the specified number.

ATAN
Returns the angle whose tangent is the specified number.

CloseBlockingProfile
Closes the current blocking profile with a line segment that connects the start and end points of the blocking profile.

ClosePolyline
Closes the current polyline with a line segment that connects the start and end points of the polyline.

cos
Returns the cosine of the specified angle.

COS
Returns the cosine of the specified angle.

Create3DRoughFinish
Create a 3D milling operation

CreateArc2PointCenter
Create an arc given 2 points and center point on the active workplane.

CreateArc2PointRadius
Create an arc given 2 points and radius on the active workplane.

CreateArc3Points
Create an arc given 3 points on the active workplane.

CreateArcCenterAngle
Create an arc given first point, center point and angle swept on the active workplane.

CreateBidirectionalMillingStrategy
Create the machining strategy for a milling with multiple passes in bidirectional way (will be valid only with the first operation created after strategy creation).

CreateBladeCut
Create a saw blade cut operation by using the active geometry.

CreateBlockingProfile
Create a blocking profile. The start point is used as the starting point for subsequent segments/arcs.

CreateChamfer(String, String, Double, Double, Int32)
Create a chamfer between two geometries identified by their name.

CreateChamfer(String, Int32, Int32, Double, Double, Int32)
Create a chamfer between two adjacent elements of the active polyline.

CreateChamfer(String, String, String, Double, Double, Int32)
Create a chamfer between two adjacent elements of the active polyline.

CreateChamfer(String, Double, Double, Double, Int32, String, TypeOfProcess, String, String, Double, Double, Double, Double)
Create a chamfer operation by using the active geometry.

CreateCircleCenterPoint(String, Double, Double, Double, Double)
Create a circle given center point and a point belonging on the circle on the active workplane.

CreateCircleCenterPoint(String, Double, Double, Double, Double, Boolean)
Create a circle given center point and a point belonging on the circle on the active workplane.

CreateCircleCenterRadius(String, Double, Double, Double)
Create a circle given center point and radius on the active workplane.

CreateCircleCenterRadius(String, Double, Double, Double, Boolean)
Create a circle given center point and radius on the active workplane.

CreateCombiflexUnloadUnitClamp
Create the NC function CombiflexUnloadUnitClamp operation.

CreateContour
Create a countour operation

CreateContourParallelStrategy
Create the machining strategy for a contour pocket machining.

CreateContourPocket
Create a countour pocket operation by using the active geometry.

CreateDrill
Create a drilling operation.

CreateEllipseCenterAxes
Create an ellipse with center point, major radius and minor radius on the active plane.

CreateFillet(String, String, Double, Int32)
Create a fillet between two geometries identified by their name.

CreateFillet(String, Int32, Int32, Double, Int32)
Create a fillet between two adjacent elements of the active polyline.

CreateFillet(String, String, String, Double, Int32)
Create a fillet between two adjacent elements of the active polyline.

CreateFinishedWorkpieceBox
Create a finished workpiece as a box. To define the raw and finished for the same workpiece use the same name.

CreateFinishedWorkpieceFromExtrusion
Create a finished workpiece as a solid extrusion along Z axis. The active geometry representing the boundary must be closed.

CreateHelicMillingStrategy
Create the machining strategy for a milling with an helic toolpath (is valid only with the first operation created after strategy creation).

CreateIso
Create the NC function ISO operation.

CreateMessage
Create the NC function message.

CreateMultiStepDrillingStrategy
Create the machining strategy for a multistep drilling (will be valid only with the first operation created after strategy creation).

CreateNullOperation
Create the NC function null operation.

CreatePark
Create the NC function park.

CreatePattern
Create a pattern of an operation.

CreatePlaneCutterLocationStrategy
Create the machining strategy for a 3D machininga operation with a fixed tool direction

CreatePolyline
Create a polyline on the active workplane. The start point is used as the starting point for subsequent segments/arcs.

CreateRawWorkpiece
Create a workpiece as a box.

CreateRawWorkpieceBox
Create a raw workpiece as a box. To define the raw and finished for the same workpiece use the same name.

CreateRawWorkpieceFromExtrusion
Create a workpiece as a solid extrusion along Z axis. The active geometry representing the boundary must be closed.

CreateRoughFinish
Create a milling operation by using the active geometry.

CreateScraping
Create a scraping operation by using the active geometry.

CreateSectioningMillingStrategy
Create the machining strategy for a sectioning milling (will be valid only with the first operation created after strategy creation).

CreateSegment
Create a line segment on the active workplane

CreateSingleStepDrillingStrategy
Create the machining strategy for a single step drilling operation.

CreateSlantedDrill
Create a slanted drilling operation.

CreateSlantedRoughFinish(String, Double, Double, Int32, Double, String, TypeOfProcess, String, String, Double, Double, Double, Double)
Create a slanted milling operation by using the active geometry.

CreateSlantedRoughFinish(String, Double, Double, Int32, Double, String, TypeOfProcess, String, String, Int32, Double, Double, Double, Double)
Create a slanted milling operation by using the active geometry.

CreateSlot
Create a slot operation

CreateToolpath
Create a toolpath. The start point is used as the starting point for subsequent segments/arcs.

CreateToolpath3D
Create a 3D toolpath. The start point is used as the starting point for subsequent segments.
Angles ZRotation and XRotation that defines tool axis rotation on the start point
are specified when creating the operation by using the method Create3DRoughFinish()

CreateTrimming
Create a trimming operation by using the active geometry.

CreateUnidirectionalMillingStrategy
Create the machining strategy for a milling with multiple passes in unidirectiona way (will be valid only with the first operation created after strategy creation).

CreateWorkPieceProbing
Create the NC function workpiece probing.

CreateWorkplan
Create a workplan

CreateWorkplane(String, Double)
Create a workplane parallel to the active workplane translated along the Z axis of the starting (active) plane by using offsetZ.

CreateWorkplane(String, Double, Double, Double, Double, Double)
Create a workplane given its origin and rotation with respect of Z and X axis.

CreateWorkplane(String, Double, Double, Double, Double, Double, Double, Double, Double, Double)
Create a workplane given tree points

DEF(Nullable<(Of <<'(Double>)>>))
Check if the variable has a valid value

DEF(String)
Check if the variable has a valid value

DeleteGeometry(Int32)
Delete a geometry identified by the index.

DeleteGeometry(String)
Delete a geometry identified by the name.

DeleteOperation(Int32)
Delete the operation identified by the index.

DeleteOperation(String)
Delete the operation identified by the name.

DeleteToolpath(Int32)
Delete a toopath identified by the index.

DeleteToolpath(String)
Delete a toopath identified by the name.

DeleteWorkpiece(Int32)
Delete a workpiece identified by the index.

DeleteWorkpiece(String)
Delete a workpiece identified by the name.

DeleteWorkplan(Int32)
Delete a workplan identified by the index.

DeleteWorkplan(String)
Delete a workplan identified by the name.

DeleteWorkplane(Int32)
Delete a workplane identified by the index.

DeleteWorkplane(String)
Delete a workplane identified by the name.

ExecMacro
Execute a macro.

exp
Returns e raised to the specified power.

EXP
Returns e raised to the specified power.

GetTool
Retrieve the tool identified by a specified name.

GetVersion
Read the version of Maestro executing the macro

ln
Returns the natural (base e) logarithm of a specified number.

LN
Returns the natural (base e) logarithm of a specified number.

log10
Returns the base 10 logarithm of a specified number.

LOG10
Returns the base 10 logarithm of a specified number.

Mirror
Mirror the object identified by the parameter 'name'.

NDEF(Nullable<(Of <<'(Double>)>>))
Check if the variable has a valid value

NDEF(String)
Check if the variable has a valid value

pow
Returns a specified number raised to the specified power.

POW
Returns a specified number raised to the specified power.

Print
Print an error message

rd
Returns the largest integral value less than or equal to the specified decimal number

RD
Returns the largest integral value less than or equal to the specified decimal number

RenameWorkplan
Rename the active workplan.

ResetApproachStrategy
Reset the active approach strategy.

ResetAuxiliaryHood
Reset the auxiliary hood position

ResetDustpan
Disable the NC function for the dustpan.

ResetJerk
Reset the machine function Jerk.

ResetJerk3D
Reset the machine function Jerk3D.

ResetPattern
Reset the active pattern.

ResetPneumaticHood
Reset the last position for the hood and enable automatic positioning.

ResetRetractStrategy
Reset the active retract strategy.

Rotate
Rotate the object identified by the parameter 'name'.

ru
Returns the smallest integral value that is greater than or equal to the specified input value

RU
Returns the smallest integral value that is greater than or equal to the specified input value

SelectGeometry(Int32)
Select a geometry as active geometry.

SelectGeometry(String)
Select a geometry as active geometry.

SelectOperation(Int32)
Select an operation as active operation.

SelectOperation(String)
Select an operation as active operation.

SelectToolpath(Int32)
Select a toolpath as active toolpath.

SelectToolpath(String)
Select a toolpath as active toolpath.

SelectWorkpiece(Int32)
Select a workpiece as active workpiece.

SelectWorkpiece(String)
Select a workpiece as active workpiece.

SelectWorkplan(Int32)
Select a workplan as active workplan.

SelectWorkplan(String)
Select a workplan as active workplan.

SelectWorkplane(Int32)
Select a workplane as active workplane.

SelectWorkplane(String)
Select a workplane as active workplane.
By using the keywords "Top", "Bottom", "Right", "Left", "Front", "Back" the main workplanes of the active workpiece will be activated.

SetApproachSecurityDistance
Set the approach security distance

SetApproachStrategy
Set the approach strategy.

SetAttribute
Set of an attribute related to the active geometry. Tipically, it is used before an operation added to the geometry.

SetAuxiliaryHoodPosition
Set the position of the auxiliary hood.

SetBrakes
Set the active brakes for the next operation.

SetDustpanOffset(Double)
Set the dustpan offset

SetDustpanOffset(Double, Nullable<(Of <<'(Int32>)>>), Nullable<(Of <<'(Boolean>)>>))
Enable the NC function for the dustpan.

SetDustpanPosition
Set the duspan position

SetJerk
Set the machine function Jerk in a modal way.

SetJerk3D
Set the machine function Jerk3D in a modal way.

SetMachiningParameters
Initialize the machining parameters to be used for the execution of the program

SetMirror
Set the mirror tranformation to enable

SetMirrorX
Set the mirror tranformation with respect to X axis to enable

SetMirrorY
Set the mirror tranformation with respect to Y axis to enable

SetPneumaticHoodPosition
Disable the automatic setting for the pneumatic hood and set its position.

SetRetractSecurityDistance
Set the retract security distance

SetRetractStrategy
Set the retract strategy.

SetRotation
Set the rotation tranformation to enable.

SetToolpathAttribute
Set of an attribute related to the active toolpath if any.

SetTranslation
Set the translation tranformation to enable.

SetUnrollHeadMode
Set the 5 axis unroll head mode

SetUnrollHeadRadiusMultiplier
Set the 5 axis unroll head mode radius multiplier

SetWorkpieceSetupPosition
Set the position of the active workpiece referring to the active workplan.

sin
Returns the sine of the specified angle.

SIN
Returns the sine of the specified angle.

sqrt
Returns the square root of a specified number.

SQRT
Returns the square root of a specified number.

tan
Returns the tangent of the specified angle.

TAN
Returns the tangent of the specified angle.

V
Get the value of a variabl double? (pX, pY, ecc...) or 0 if the variable is not defined

VALUE
Get the value of a variabl double? (pX, pY, ecc...) or 0 if the variable is not defined

# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## IScripting Properties

﻿
Collapse AllExpand All Members: Show All Members: Filtered Members: Filtered Members: Filtered
C#
Include Protected Members
Include Inherited Members
Xilog Maestro Scripting Language
IScripting Properties
IScripting Interface See Also Send Feedback

The IScripting type exposes the following members.
# Properties
Name Description
ActiveGeometry
The active geometry. When adding a new geometry, it automatically becomes the active geometry.
When adding a new geometry, it automatically becomes the active geometry.

ActiveLeadInOut
The lead in-out (approach-rectract) properties active.
These property is modal and reamins active until it's modified.

ActiveMachineFunctions
Set of all the active machine functions. These functions are modal and are applied to all the machining
operations until they are reset.
Machine functions are set and reset by using methods provided by the script language.

ActiveOperation
The last machining operation added to the program.
When adding a new machining operation, it automatically becomes the active machining operation.

ActivePattern
The active pattern. If null is considered inactive.
It remains active until it is reset.

ActiveToolpath
The active toolpath. It can be used to add toolpath segments to the active machining operation.

ActiveWorkpiece
The workpiece to which are added next machining operation, geometries, workplans and workplanes
by using methods provided by the script language.
When adding a new workpiece, it automatically becomes the active workpiece.

ActiveWorkplan
The workplan to which are added next machining operation, geometries, and workplanes
by using methods provided by the script language.
When adding a new workplan, it automatically becomes the active workplan.

ActiveWorkplane
The workplane to which are added next geometries by using methods provided by the script language.
When adding a new workplane, it automatically becomes the active workplane.

# See Also
IScripting Interface
ScmGroup.XCam.Scripting Namespace
SCM Group S.P.A

---

## ScmGroup XCam Scripting Namespace

﻿
Collapse AllExpand All
C#
Xilog Maestro Scripting Language
ScmGroup.XCam.Scripting Namespace
Send Feedback

Xilog Maestro Scripting Language
# Interfaces
Interface Description
IScripting
Interface that defines methods and properties available to build programs and macros.

SCM Group S.P.A

