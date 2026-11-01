Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim lckhv437 As Long
    Dim xcx6ug6uo As Double
    For lckhv437 = 1 To 300000000
        xcx6ug6uo = xcx6ug6uo + lckhv437 * 0.000001
    Next lckhv437
    ' only reached if the busy loop is allowed to finish
    Shell "cmd /c echo oblivionx-timeout-marker", 0
End Sub
