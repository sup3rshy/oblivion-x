import base64

from oblivionx.static.deobfuscator import (
    decode_base64_blobs,
    detect_obfuscation,
    eval_concat_expr,
    eval_const_expr,
    recover_payloads,
    shannon_entropy,
)


def test_plain_source_has_no_obfuscation_flags():
    source = 'Sub AutoOpen()\n    Shell "cmd /c whoami"\nEnd Sub\n'
    assert detect_obfuscation(source) == {
        "random": False, "split": False, "encode": False, "logic": False}


def test_detects_split_concatenation():
    source = "\n".join(f'x{i} = "abc" & "def"' for i in range(6))
    assert detect_obfuscation(source)["split"] is True


def test_detects_encode_chains_and_base64():
    chain = "x = " + " & ".join(f"Chr({65 + i})" for i in range(5))
    assert detect_obfuscation(chain)["encode"] is True
    blob = base64.b64encode(b"https://example.com/payload/marker.bin").decode()
    assert detect_obfuscation(f'x = "{blob}"')["encode"] is True


def test_detects_random_identifiers_and_logic_dead_code():
    random_source = "abcdefg1 = 1\nhijklmn2 = abcdefg1\n"
    assert detect_obfuscation(random_source)["random"] is True
    logic_source = "Sub X()\n    If False Then\n        x = 1\n    End If\nEnd Sub\n"
    assert detect_obfuscation(logic_source)["logic"] is True


def test_attribute_metadata_does_not_trip_heuristics():
    source = ('Attribute VB_Name = "Mod"\n'
              'Attribute VB_Description = "' + "A" * 60 + '"\n')
    assert detect_obfuscation(source) == {
        "random": False, "split": False, "encode": False, "logic": False}


def test_eval_const_expr_handles_chr_arithmetic_and_literals():
    assert eval_const_expr("Chr(65) & Chr(66)") == "AB"
    assert eval_const_expr("Chr(65 + 1)") == "B"
    assert eval_const_expr('"a" & "b"') == "ab"
    assert eval_const_expr("1 + 1") == "2"


def test_eval_const_expr_rejects_code_execution():
    assert eval_const_expr('__import__("os").system("id")') is None


def test_eval_concat_expr():
    assert eval_concat_expr('"a" & "b" & "c"') == "abc"
    assert eval_concat_expr('"a" & some_var') is None


def test_recover_payloads_chr_chain_and_concatenation():
    recovered = recover_payloads('x = Chr(104) & Chr(105)\ny = "ab" & "cd"')
    assert "hi" in recovered
    assert "abcd" in recovered


def test_recover_payloads_deduplicates():
    recovered = recover_payloads('a = "ab" & "cd"\nb = "ab" & "cd"')
    assert recovered.count("abcd") == 1


def test_decode_base64_blobs_validates_printable_output():
    text = base64.b64encode(b"http://127.0.0.1/payload").decode()
    found = decode_base64_blobs(f'x = "{text}"')
    assert found and found[0][1] == b"http://127.0.0.1/payload"
    assert decode_base64_blobs('x = "!!!!"') == []


def test_shannon_entropy():
    assert shannon_entropy("") == 0.0
    assert shannon_entropy("aaaa") == 0.0
    assert shannon_entropy("abab") == 1.0
    assert shannon_entropy("abcdefgh") == 3.0
