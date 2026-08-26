# Báo Cáo Lab Day 21 - CI/CD cho AI Systems

| | |
|---|---|
| Họ và tên | ___ |
| MSSV | ___ |
| Lớp / Khóa | K4 |
| Repo GitHub | https://github.com/tKrulreal/K4-Track2-Day21-CI-CD-for-AI-Systems |
| Ngày nộp | 2026-08-21 |

---

## 1. Bộ Siêu Tham Số Đã Chọn và Lý Do

| Lần chạy | n_estimators | learning_rate | max_depth | f1_score | accuracy |
|---|---|---|---|---|---|
| 1 | 100 | 0.1 | 3 | 0.7109 | 0.878 |
| 2 | 50 | 0.05 | 2 | 0.6051 | 0.846 |
| 3 | 200 | 0.1 | 5 | 0.7149 | 0.874 |

**Bộ siêu tham số đã chọn:** `n_estimators=200`, `learning_rate=0.1`, `max_depth=5`.

**Lý do:** Bộ này cho f1_score cao nhất (0.7149) trên tập holdout và vượt ngưỡng chất lượng 0.65 của pipeline. Đáng chú ý, lần chạy có accuracy cao nhất là lần chạy 1 (0.878), nhưng lần chạy có f1_score cao nhất lại là lần chạy 3 (0.7149) — hai chỉ số không trùng nhau. Điều này cho thấy accuracy bị lớp đa số (75.2% mẫu có thu nhập thấp) kéo lên cao giả tạo, trong khi f1 của lớp dương phản ánh đúng chất lượng thực sự của mô hình trên lớp thiểu số. Quan sát thêm: giảm đồng thời n_estimators và learning_rate (lần chạy 2) làm f1 tụt mạnh xuống 0.6051 — dưới ngưỡng — chứng tỏ hai tham số này có quan hệ đánh đổi: mô hình cần đủ số cây và mỗi cây đóng góp đủ lớn để học được mẫu thu nhập cao.

---

## 2. Vì Sao Ngưỡng Chất Lượng Đặt Trên F1 Chứ Không Phải Accuracy

Tập dữ liệu Adult có phân bố lớp mất cân bằng: chỉ 24.8% mẫu thuộc lớp thu nhập > 50K (5539 mẫu dương trên 22361 mẫu ở tập train, 124/500 ở holdout). Một mô hình "đoán bừa" luôn trả lời thu nhập thấp sẽ đạt accuracy khoảng 0.752 mà không dự đoán đúng một mẫu dương nào — con số này trông ổn nhưng hoàn toàn vô dụng cho bài toán thực tế. F1 của lớp dương đo đồng thời precision và recall trên lớp thiểu số, nắm bắt được chất lượng thực sự mà accuracy bỏ sót. Khi gọi `f1_score` không truyền `average` nào (mặc định `binary`, lớp dương) là lựa chọn đúng; nếu dùng `average="weighted"` hay `average="macro"`, lớp đa số sẽ chi phối kết quả và ngưỡng 0.65 mất ý nghĩa cảnh báo chất lượng. Vì vậy toàn bộ pipeline — từ `train()` trả về `f1`, đến quality gate so sánh `f1 >= 0.65`, đến điền vào `outputs/report.json` — đều dùng f1 lớp dương làm chỉ số quyết định.

---

## 3. Khó Khăn Gặp Phải và Cách Giải Quyết

| Khó khăn | Nguyên nhân | Cách giải quyết |
|---|---|---|
| Pipeline trên GitHub Actions lỗi `dvc pull` ở job Train | DVC thiếu extension S3, không kết nối được cloud storage chứa data | Cài thêm `dvc[s3]` vào bước Install dependencies trước khi chạy `dvc pull`. |
| Local MLflow ghi vào `mlruns/` bị hỏng trong CI, làm Unit Test fail | Train job chạy `mlflow` mặc định ghi vào `./mlruns` nếu `MLFLOW_TRACKING_URI` chưa set, trùng thư mục của Unit Test | Tách MLflow local ra `mlruns_local` qua `mlflow.set_tracking_uri(...)` khi biến môi trường chưa được set, tránh đụng độ thư mục giữa hai job. |
| Release job SSH deploy tới EC2 fail với `getKeyFile error: open ~/.ssh/deploy_key: no such file or directory` | `appleboy/ssh-action` chạy script trong container Docker riêng (drone-ssh) chỉ mount `/github/workspace`; viết key vào `~/.ssh/deploy_key` trên runner nằm ngoài container và không được mount vào | Ghi key vào `<workspace>/.ssh/deploy_key` (relative path) và truyền `key_path: .ssh/deploy_key` — action resolve path theo workspace đã mount vào container. |

---

## 4. So Sánh Bước 2 và Bước 3 (bắt buộc, 2 - 3 câu)

| | f1_score | accuracy |
|---|---|---|
| Bước 2 (chỉ `train_batch1`) | 0.7149 | 0.874 |
| Bước 3 (thêm `train_batch2`) | 0.7354 | 0.882 |

**Nhận xét:** Cả f1_score (0.7149 → 0.7354) và accuracy (0.874 → 0.882) đều tăng nhẹ ở Bước 3, nhưng mức tăng khiêm tốn (khoảng +0.02 cho f1). Điều này phù hợp với nhận định trong tài liệu bước 3: hai batch `train_batch1` và `train_batch2` được chia ngẫu nhiên từ cùng một phân phối gốc của Adult, nên batch2 không mang thêm thông tin mới mà mô hình chưa học được từ batch1. Việc f1 vẫn tăng thay vì giảm chỉ là dao động ngẫu nhiên trong giới hạn chung của mô hình — điều được kiểm chứng ở Bước 3 không phải con số cao hơn, mà là pipeline tự động chạy đến cùng: từ commit dữ liệu → train lại → quality gate → release tới EC2, không cần thao tác thủ công.

---

## 5. Phần Bonus Đã Thực Hiện (nếu có)
