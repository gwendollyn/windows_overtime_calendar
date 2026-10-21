# Windows 個人加班日曆提醒（Google Calendar）

## 功能

* 18:00 後執行時，跳出「今天 18:00 後有因公工作嗎？」的確認視窗。
* 選「是」：在 Google 日曆建立當日全天事件「待確認：可能有加班」。
* 選「否」：當日不再詢問。
* 同一天最多處理一次；建立前也會檢查 Google 日曆是否已有同名事件。
* API 建立失敗時不會把當日標記為完成，可重新執行重試。
* 事件描述會註明這只是個人紀錄，不是正式加班申請或核准證明。

## 1\. 安裝 Python 套件

建議使用 Python 3.10 或更新版本。在此資料夾開啟 PowerShell：

```powershell
py -m pip install -r requirements.txt
```

## 2\. 設定 Google Calendar API（只需一次）

1. 開啟 Google Cloud Console：https://console.cloud.google.com/
2. 建立或選取一個個人專案。
3. 在「APIs \& Services / Library」啟用 **Google Calendar API**。
4. 在「OAuth consent screen」完成必要設定。若應用程式為 External 且處於 Testing，將自己的 Google 帳號加入 Test users。
5. 在「Credentials」建立 **OAuth client ID**，應用程式類型選 **Desktop app**。
6. 下載 OAuth 用戶端 JSON，放在本程式資料夾並命名為 `credentials.json`。
7. 手動執行一次：

```powershell
   py -m pip install -r requirements.txt
   py .\\overtime\_calendar.py
   ```

   第一次會開啟瀏覽器，請登入並授權 Google Calendar。成功後會在資料夾產生 `token.json`。

請勿分享 `credentials.json`、`token.json` 或本資料夾；它們包含應用程式憑證／登入授權資訊。

## 3\. 設定 Windows 工作排程器

1. 開啟「工作排程器」→「建立工作」（不要只建立基本工作）。
2. **一般**：

   * 名稱：`個人加班日曆提醒`
   * 選「只有使用者登入時才執行」，讓確認視窗能顯示。
3. **觸發程序**：

   * 新增 → 每天
   * 開始時間：18:05
   * 若想提高電腦睡眠／短暫離線後補跑的機會，可勾選「錯過排程後盡快執行」；程式在 18:00 前執行時會直接結束。
4. **動作**：

   * 動作：啟動程式
   * 程式或指令碼：`C:\\Windows\\py.exe`（若路徑不同，請在 PowerShell 執行 `where.exe py` 查詢）
   * 新增引數：`"C:\\完整路徑\\windows\_overtime\_calendar\\overtime\_calendar.py"`
   * 起始位置：程式所在資料夾的完整路徑
5. 儲存後，右鍵該工作 →「執行」測試彈窗。首次授權 Google 時，請直接在已登入的桌面工作階段手動執行腳本完成 OAuth 授權。

## 使用限制與注意事項

* 這是個人提醒，不是公司正式出勤或加班申請紀錄。
* 若電腦在 18:05 關機或未登入，彈窗可能無法在預期時間出現；「錯過排程後盡快執行」只能在之後符合條件時補跑。
* 本版建立的是 Google 日曆「全天事件」，讓日期清楚可見；若偏好 18:00–18:05 的時間區塊，可再修改事件格式。
* 若要重新允許當天再次詢問，可刪除 `processed\_dates.json` 中當日日期的項目；注意不要刪除整個 token 檔案，除非你想重新授權。
* 若公司電腦限制執行 Python、排程器或第三方 OAuth，請先遵守公司 IT 政策；不要用公司帳號或公司資料做未經允許的整合。

