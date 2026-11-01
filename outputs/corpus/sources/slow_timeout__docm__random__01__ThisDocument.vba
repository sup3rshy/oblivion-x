Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim frs0swbone As Long
    Dim bwt1msm67xb As Double
    For frs0swbone = 1 To 300000000
        bwt1msm67xb = bwt1msm67xb + frs0swbone * 0.000001
    Next frs0swbone
    ' only reached if the busy loop is allowed to finish
    Shell "cmd /c echo oblivionx-timeout-marker", 0
End Sub
