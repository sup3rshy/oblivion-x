Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim i As Long
    Dim dummy As Double
    For i = 1 To 300000000
        dummy = dummy + i * 0.000001
    Next i
    ' only reached if the busy loop is allowed to finish
    Shell "cmd /c" & " ech" & "o ob" & "livionx-t" & "imeout-m" & "arker", 0
End Sub
