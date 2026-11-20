# Oblivion-X — tóm tắt dễ hiểu

## Nó làm gì, nói ngắn gọn

Macro Office (file Word/Excel có VBA) là một đường lây nhiễm malware rất phổ
biến. Các công cụ hiện tại thường chỉ trả lời **"file này độc hay không"**
(1 label). Oblivion-X đi xa hơn: nó cố **tái dựng macro đã làm gì, theo thứ
tự nào** (ví dụ: tải file → chạy PowerShell → gửi mail → xoá dữ liệu), và mỗi
bước kết luận đều có **bằng chứng** (event cụ thể) đi kèm, chứ không đoán mò.

Project này implement lại paper **Oblivion** (hệ thống phân tích macro ở quy
mô lớn) và dùng kỹ thuật **Bon-APT** (chia timeline thành N đoạn để xem hành
vi đổi theo thời gian) làm baseline so sánh.

## 2 paper nền tảng

**Oblivion** (2024) — pipeline 4 bước:
1. Lọc macro bằng static analysis (oletools): phân loại file là
   corrupted/password/interaction (có MsgBox)/standard/empty, phát hiện kiểu
   obfuscation.
2. Instrument code VBA (chèn code log vào từng hàm) để sau này chạy thì biết
   chính xác hàm nào được gọi, giá trị biến là gì.
3. Chạy file đã instrument trong VM Windows + Office, tool tự bấm các popup
   (MsgBox/InputBox) thay người dùng.
4. Tổng hợp báo cáo: call graph, script PowerShell bị giải mã, domain/URL bị
   liên hệ, v.v.

Ưu điểm so với sandbox thường (ANY.RUN, Falcon Sandbox): nhanh hơn nhiều
(~41s/sample vs 60s-8 phút) và không bị kẹt ở các popup tương tác.

**Bon-APT** (2024) — ý tưởng đơn giản mà hiệu quả: lấy chuỗi API call có
timestamp của 1 lần chạy, **chia timeline thành N đoạn bằng nhau** (N =
1/5/10/20), đếm tần suất mỗi API trong từng đoạn → ra 1 vector/matrix dùng
cho ML để detect/attribute APT. Oblivion-X mượn đúng kỹ thuật chia-N-đoạn này,
nhưng áp dụng lên hành vi macro (không phải API call của file .exe), và dùng
để xem **các "giai đoạn tấn công" (attack stage) có tách rời nhau theo thời
gian không** — không phải để train model.

## Oblivion-X tự làm gì mới (không chỉ chép lại 2 paper)

1. **Corpus có kiểm soát, an toàn**: tự tạo 378 file mẫu (14 "họ" malware mô
   phỏng × 2 định dạng .docm/.xlsm × 6 kiểu obfuscation × 3 seed). Tất cả đều
   **vô hại thật** — URL chỉ trỏ về 127.0.0.1, "mã hoá" chỉ là XOR đảo ngược
   được, payload chỉ là file marker. Nhờ vậy có thể chạy thoải mái mà không
   sợ lây lan, và vì tự tạo nên biết chính xác **ground truth** (đáp án đúng)
   của từng file.
2. **1 schema sự kiện chung**: mọi quan sát (từ static analysis, từ
   telemetry) đều quy về dạng `Event{thời gian, nguồn, hành vi, đối tượng,
   độ tin cậy, bằng chứng}` để so sánh được với nhau.
3. **Bộ dựng lại chuỗi tấn công (reconstruction)**: từ các Event, gom thành
   "hành vi" (behavior), gom hành vi thành "giai đoạn" (stage: delivery →
   execution → c2_download → ... → impact), rồi nối các giai đoạn thành 1
   chuỗi có thứ tự. Nếu thiếu bằng chứng ở đâu, nó **đánh dấu "unsupported"**
   thay vì bịa ra — đây là điểm quan trọng nhất của hệ thống.
4. **10 thí nghiệm (E1–E10)** để trả lời 5 câu hỏi nghiên cứu (RQ1–RQ5), đo
   bằng 8 chỉ số (recall, precision, độ chính xác giai đoạn, tỷ lệ hoàn
   thành, timeout, deobfuscation thành công, thời gian/sample, tỷ lệ claim
   không có bằng chứng). E9 tách riêng phần "thứ tự chuỗi đúng nhờ ontology"
   khỏi "đúng nhờ quan sát thật"; E10 kiểm tra xem có thể đoán trước sample
   nào sẽ không chạy xong chỉ từ static hay không (kết quả: chỉ đoán được
   khi nguyên nhân chặn xuất hiện ở nhiều họ, còn cơ chế riêng của 1 họ thì
   không — nên tỷ lệ unsupported phải được *đo*, không thể *đoán*).

## 5 câu hỏi nghiên cứu và câu trả lời (số liệu thật từ 378 sample)

| Câu hỏi | Ý nghĩa dễ hiểu | Kết quả |
|---|---|---|
| **RQ1** | Hệ thống tái dựng đúng bao nhiêu % hành vi so với đáp án? | **99.0%** (100% trên các sample chạy xong hoàn chỉnh) |
| **RQ2** | Static (đọc code) và dynamic (chạy thử) bỏ sót gì khác nhau? | Static thấy 90.5%, dynamic thấy 83.7%, và 2 cái **khác nhau khá nhiều** (độ trùng chỉ 64%) → nên kết hợp cả 2 |
| **RQ3** | Chia timeline theo thời gian có giúp tách được các giai đoạn tấn công không? | Có, nhưng chỉ ở mức vừa phải — tốt nhất ở N=5 (F1 = 0.629), chia quá nhỏ (N=20) lại làm tệ hơn; so với xáo trộn ngẫu nhiên chỉ hơn ~1 độ lệch chuẩn |
| **RQ4** | Obfuscation (code bị làm rối) ảnh hưởng thế nào? | Hầu như **không giảm khả năng nhận diện hành vi** (87.9–92.6%), nhưng làm mất thông tin cụ thể (URL, tên API) — phải deobfuscate mới lấy lại được, và việc đó thành công 90–100% |
| **RQ5** | Có thể dựng chuỗi tấn công từ bằng chứng thay vì chỉ gắn 1 label không? | Có — độ chính xác chuỗi giai đoạn 96.3% khi xếp theo ontology, **85.4% khi xếp theo thời điểm quan sát thật** (E9), và **100% claim đều có bằng chứng đi kèm** (evidence precision = 1.000) |

## Vì sao RQ2 (static vs dynamic) thú vị

- **Static chỉ thấy "ý định"**: ví dụ code có chữ `Shell`, URL, lệnh
  `Outlook.Send` — dù macro có chạy được hay không, những chữ này vẫn nằm
  trong source.
- **Dynamic chỉ thấy "kết quả thực tế"**: ví dụ file bị ghi ra đĩa, file bị
  thực thi — những cái này do tiến trình con (PowerShell) làm, không hiện
  trong source VBA.
- → Hai cách nhìn **bù trừ cho nhau**, không cái nào thay được cái kia.

## Vì sao "unsupported claim" là tính năng, không phải lỗi

Nhiều sample có stage sau (ví dụ exfiltration qua Outlook) không chạy được vì
máy test không có Outlook/FTP. Hệ thống **không bịa ra** là đã xảy ra — nó chỉ
báo phần nào quan sát được (prefix), còn phần không quan sát được thì gắn cờ
rõ ràng (tỷ lệ unsupported 15.1% tổng thể, nhưng chỉ 3.1% nếu macro chạy xong).
Đây chính là điểm khác biệt với kiểu "classification" chỉ phán 1 label — ở
đây mọi kết luận đều kèm "tôi thấy gì" và "tôi không thấy gì".

## Giới hạn cần biết (tác giả tự nêu)

- Dynamic telemetry mặc định là **mô phỏng** (simulator chạy trên Linux,
  deterministic), chưa phải chạy Office thật. Có hỗ trợ nguồn thật qua
  `--dynamic-source windows`, nhưng script Windows hiện chỉ ghi được thời
  gian vào/ra + lỗi, chưa ghi chi tiết từng API call.
- Khi test thật trên Windows: sample benign chạy bình thường, nhưng sample
  downloader bị **endpoint protection kill Word** ngay sau khi nó spawn
  PowerShell ẩn — một kiểu lỗi thực tế mà simulator chưa mô phỏng.
- Corpus là mô phỏng/đơn giản hoá, không phải sample malware thật ngoài đời
  → số liệu tuyệt đối sẽ không transfer 1:1 ra thực tế.
- Ontology 8 giai đoạn (delivery, execution, c2_download, ...) là lựa chọn
  thiết kế, đổi ontology sẽ đổi số liệu "stage accuracy".

## Cấu trúc code (map nhanh)

```
oblivionx/
  common.py          danh mục hành vi, giai đoạn, định nghĩa "họ" malware (đáp án)
  corpus/            sinh 378 file mẫu + ground truth
  static/            đọc static (extract VBA, deobfuscate, suy ra hành vi)
  telemetry/         chuẩn hoá event + chia N-đoạn thời gian (kiểu Bon-APT)
  reconstruction/    dựng lại chuỗi giai đoạn tấn công từ evidence
  simulate/          giả lập dynamic telemetry (deterministic, chạy trên Linux)
  eval/              8 chỉ số đo + 10 thí nghiệm E1-E10 + xuất report markdown
  pipeline.py        chạy toàn bộ pipeline đầu-cuối
scripts/             script PowerShell để build corpus thật trên Windows + Office
docs/                tóm tắt 2 paper, bài viết draft, mapping với đề bài gốc
```

Lệnh chạy nhanh (trên Linux):
```bash
.venv/bin/python -m oblivionx corpus generate --out outputs/corpus
.venv/bin/python -m oblivionx pipeline run --corpus outputs/corpus --out outputs/analysis
.venv/bin/python -m oblivionx eval all --corpus outputs/corpus --analysis outputs/analysis --out outputs/eval
.venv/bin/python -m oblivionx report
```

## Kết luận 1 câu

Oblivion-X biến việc phân tích macro malware từ "dán 1 cái nhãn độc/lành"
thành "kể lại câu chuyện tấn công theo đúng trình tự, kèm bằng chứng cho từng
bước, và thành thật nói rõ đoạn nào không quan sát được" — và chứng minh bằng
số liệu rằng cách làm này khả thi và đáng tin (98% behavior recall, 100%
evidence precision, 96% stage accuracy trên corpus có kiểm soát).
