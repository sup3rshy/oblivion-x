Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim jybosg1pnivrj As Long
    Dim lps4wdhm As Double
    For jybosg1pnivrj = 1 To 300000000
        lps4wdhm = lps4wdhm + jybosg1pnivrj * 0.000001
    Next jybosg1pnivrj
    ' only reached if the busy loop is allowed to finish
    Shell "cmd /c echo oblivionx-timeout-marker", 0
End Sub
