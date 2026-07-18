// AppPerfect LoadTest - Script Editor 專用
// 現況：你的專案已經有 executeTask_1（Task1 已成功建好），本檔只補 Task2~Task5。
//
// 用法：
//   1. Project -> Script Editor... 開啟
//   2. 把下面 executeTask_2 ~ executeTask_5（含 var registrationId;）整段貼在
//      現有 executeTask_1 函式的 "}" 之後、group_3() 之前
//   3. 【關鍵，別漏】把 group_2()（ActionGroup1）改成依序呼叫全部 Task：
//        function group_2() {
//            executeTask_1();
//            executeTask_2();
//            executeTask_2b();
//            executeTask_2c();
//            executeTask_3();
//            executeTask_4();
//            executeTask_5();
//        }
//      只貼函式定義、不改 group_2() 的話，AppPerfect 執行時不會呼叫這些新 Task。
//   4. Save + Compile（工具列按鈕），關閉編輯器，UI 樹狀圖應該會長出 Task2~Task5 節點
//   5. Project -> Verify Test Using Browser... 驗證

function executeTask_2() // Task2: 查詢活動媒體清單（圖片測試第一步，指向來源活動）
{
    var request = engine.createGetRequest(2, 'Task2',
        'https', 'qa-khcg-ai.foxconn.com', 443,
        '/reventmodule/Basic/EVEventMedia?eVEventIds=34123425668794368');
    request.setIgnored(false);
    request.addHeader('Authorization', '@LOADTEST_TOKEN@', 'LOADTEST_TOKEN', true);
    request.setExpectedResponseCode(200);
    var successful = engine.execute(request);
    if (!successful) {
        log('Task2 failed: ' + request.getReasonForFailure());
    }
    engine.release(request);
}

function executeTask_2b() // Task2b: 下載封面圖 PC 版 ★業主指定的圖片載入測試（注意換網域）
{
    var request = engine.createGetRequest(3, 'Task2b',
        'https', 'qa-citygpt.foxconn.com', 443,
        '/rstorage/Extended/FileResource/34184848693268480');
    request.setIgnored(false);
    request.addHeader('Authorization', '@LOADTEST_TOKEN@', 'LOADTEST_TOKEN', true);
    request.setExpectedResponseCode(200);
    var successful = engine.execute(request);
    if (!successful) {
        log('Task2b failed: ' + request.getReasonForFailure());
    }
    engine.release(request);
}

function executeTask_2c() // Task2c: 下載封面圖 行動版 ★業主指定的圖片載入測試
{
    var request = engine.createGetRequest(4, 'Task2c',
        'https', 'qa-citygpt.foxconn.com', 443,
        '/rstorage/Extended/FileResource/34184848895096832');
    request.setIgnored(false);
    request.addHeader('Authorization', '@LOADTEST_TOKEN@', 'LOADTEST_TOKEN', true);
    request.setExpectedResponseCode(200);
    var successful = engine.execute(request);
    if (!successful) {
        log('Task2c failed: ' + request.getReasonForFailure());
    }
    engine.release(request);
}

function executeTask_3() // Task3: 查詢報名表單欄位
{
    var request = engine.createGetRequest(5, 'Task3',
        'https', 'qa-khcg-ai.foxconn.com', 443,
        '/reventmodule/Basic/EVFormField?eVEventIds=34185325523320832&category=Registration&pageRows=999');
    request.setIgnored(false);
    request.addHeader('Authorization', '@LOADTEST_TOKEN@', 'LOADTEST_TOKEN', true);
    request.setExpectedResponseCode(200);
    var successful = engine.execute(request);
    if (!successful) {
        log('Task3 failed: ' + request.getReasonForFailure());
    }
    engine.release(request);
}

// 全域變數：存放 Task4 回應中的報名 id，供 Task5 使用
var registrationId;

function executeTask_4() // Task4: 確認報名（送出，最關鍵的一支）
{
    var request = engine.createPostRequest(6, 'Task4',
        'https', 'qa-khcg-ai.foxconn.com', 443,
        '/reventmodule/Entity/EVRegistration');
    request.setIgnored(false);
    request.addHeader('Authorization', '@LOADTEST_TOKEN@', 'LOADTEST_TOKEN', true);
    request.addHeader('Content-Type', 'application/json', '', true);
    request.addRequestEntity(
        '{"evEventEntity":{"key":"34185325523320832"},' +
        '"evRegistrationDatas":[{"evFormFieldEntity":{"key":"34185325526138880"},"value":"1"}],' +
        '"evEventSessions":[{"key":"34185325525680128"}],' +
        '"registrationSource":"LoadTest"}'
    );
    request.setExpectedResponseCode(200);
    var successful = engine.execute(request);
    if (!successful) {
        log('Task4 failed: ' + request.getReasonForFailure());
    } else {
        // 從回應 JSON 取出新報名記錄的 id，供 Task5（憑證 QR）使用
        try {
            var respText = request.getResponseAsString();
            var respObj = JSON.parse(respText);
            registrationId = respObj.id;
            log('Task4 registrationId = ' + registrationId);
        } catch (e) {
            log('Task4 回應解析失敗: ' + e);
        }
    }
    engine.release(request);
}

function executeTask_5() // Task5（可選）: 憑證 QR，需要 Task4 先成功取得 registrationId
{
    if (!registrationId) {
        log('Task5 skipped: 沒有 registrationId（Task4 尚未成功）');
        return;
    }
    var request = engine.createGetRequest(7, 'Task5',
        'https', 'qa-khcg-ai.foxconn.com', 443,
        '/reventmodule/Fetch/EVTicket/Qrcode/' + registrationId);
    request.setIgnored(false);
    request.addHeader('Authorization', '@LOADTEST_TOKEN@', 'LOADTEST_TOKEN', true);
    request.setExpectedResponseCode(200);
    var successful = engine.execute(request);
    if (!successful) {
        log('Task5 failed: ' + request.getReasonForFailure());
    }
    engine.release(request);
}
