Attribute VB_Name = "NewMacros"
Public Function XorChar(ByVal c As String) As String
    XorChar = Chr(Asc(c) Xor 42)
End Function
