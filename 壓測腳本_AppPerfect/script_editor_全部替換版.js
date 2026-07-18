var engine; //Variable to store instance of ScriptEngine Instance

// ★★★ 全腳本唯一要改的一行 ★★★
// 把 REPLACE_ME 換成你從瀏覽器 Console 複製的 access_token（保留前面的 Bearer 和一個空格）
// token 過期時也只要改這一行，重新 Compile 再 Run 即可
var LOADTEST_TOKEN = 'Bearer REPLACE_ME';

function project_function() // script function for  Load Tester project FOXCCON
{
    var loadtest = engine.createLoadTest();
    loadtest.setRunDurationInHits(ILoadTest.HITS_PER_USER, 1);
    loadtest.setRampUpTime(0);
    loadtest.setTestDescription('');
    loadtest.setLoopStrategy(1/*virtual users*/, 1/*loop count*/);
    loadtest.setRunProjectOnMultipleMachines(false);
    loadtest.setSaveSuccessfulResponseDetails(false);
    loadtest.setStopOnFailedTaskCount(ILoadTest.HITS_PER_USER, 10);
    loadtest.collectTopTasks(10);
    loadtest.collectFailedTasks(10);
    loadtest.setUseRecordedCookiesWhileReplaying(false);
    loadtest.setUseSameTimeOut(false);
    loadtest.setTimeout(120);
    loadtest.setSaveAllTaskDetails(false);
    loadtest.setTaskDetailsBufferSize(8192);
    loadtest.setTreatTimeOutAsFailed(true);
    loadtest.setRecordThinkTime(true);
    loadtest.setDefaultThinkTime(0);
    loadtest.setIgnoreThinkTimeWhileReplaying(true);
    loadtest.setResolveSubTask(true);
    loadtest.setResponseTimeInMilliSeconds(true);
    loadtest.setThroughputType(ILoadTest.THROUGHPUT_IN_KB);
    loadtest.setCompleteActionGroupAfterTestStop(ILoadTest.NO_COMPLETE_ANY_ACTION_GROUP);
    loadtest.setCloseConnectionAfterEachIteration(false);
    loadtest.setShowCombinedChart(false);
    loadtest.setShowSystemMonitorChart(false);
    loadtest.setShowGroupSummaryChart(false);
    loadtest.setShowDBChart(false);
    loadtest.setShowUserVsThroughputChart(false);
    loadtest.setShowScatterPlot(true);
    loadtest.setShowTaskResponseChart(true);
    loadtest.setShowAverage90Percent(false);
    loadtest.setShowSubTasks(false);
    loadtest.setIgnoreOrUpdateTaskBasedOnResponseTime(false, 0, 10, 0);
    loadtest.setSystemMonitor(false);
    loadtest.setSimulateBrowser(true);
    loadtest.configureBrowserSimulation(ILoadTest.SIMULATE_BROWSER_IE, true, 50.0, 2, 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; AT&T CSM6.0; SV1; .NET CLR 1.0.3705)');
    loadtest.configureBrowserSimulation(ILoadTest.SIMULATE_BROWSER_FIREFOX, true, 50.0, 2, 'Mozilla/5.0 (Windows; U; Windows NT 5.0; en-US; rv:1.7.6) Gecko/20050223 Firefox/1.0.1');
    loadtest.configureBrowserSimulation(ILoadTest.SIMULATE_BROWSER_CHROME, false, 15.0, 2, 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en) AppleWebKit/526.9 (KHTML, like Gecko) Version/4.0dp1 Safari/526.8');
    loadtest.configureBrowserSimulation(ILoadTest.SIMULATE_BROWSER_SAFARI, false, 15.0, 2, 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.27 Safari/532.0');
    loadtest.configureBrowserSimulation(ILoadTest.SIMULATE_BROWSER_OPERA, false, 15.0, 2, 'Opera/9.00 (Windows NT 5.1; U; en)');
    loadtest.configureBrowserSimulation(ILoadTest.SIMULATE_BROWSER_IPHONE, false, 15.0, 2, 'Mozilla/5.0 (iPhone; U; CPU like Mac OS X; en) AppleWebKit/420+ (KHTML, like Gecko) Version/3.0 Mobile/1A543a Safari/419.3');
    loadtest.setClearCacheAfterEachIteration(true);
    loadtest.setThrottleNetworkBandwith(false);
    loadtest.setNetworkBandwithFetchCriteria(ILoadTest.FETCH_SAME_NB);
    loadtest.setLoadBalancing(false);
    loadtest.setIPFetchCriteria(ILoadTest.FETCH_SAME_IP);
    loadtest.setResponseTimeDistribution(100);
    loadtest.setReplayLinkedProjects(false);
    loadtest.addLinkProjectGroup('FOXCCON', 'ActionGroup1', false, 1, 100.0);
    loadtest.setLoadTestDatabase(false, '');
    loadtest.setConnectionPoolSettings(true, -1, 50, 10, 50);
    loadtest.setCloseDBConnectionAfter(ILoadTest.EVERY_TASK);
    loadtest.setGroupRunStrategy(ILoadTest.SEQUENTIAL_GROUP_SELECTION, ILoadTest.START_ACTION_END_REPEAT);
    var group = loadtest.addStartingGroup();
    group.setGroupPauseOption(false, 0, IGroup.PAUSE_START_OF_TEST, 0);
    group.setGroupStopOption(false, IGroup.STOP_AFTER_N_ITERATIONS, 0);
    group.setStartingURL('http://localhost:8396/petstore');
    group.setContainsLoginTask(false);
    group.setUseUrlRewritingSessionManagement(false);
    group.setAuthenticationMechanism(IHttpGroup.NO_AUTHENTICATION);
    group.setAuthenticationDomainName('');
    group.setUseClientSSLAuthentication(false);
    var group = loadtest.addActionGroup(IGroup.GROUP_HTTP, 'ActionGroup1');
    group.setIgnored(false);
    group.setRepeatCount(1);
    group.setRunVirtualUsers(100.0);
    group.setGroupPauseOption(false, 0, IGroup.PAUSE_START_OF_TEST, 0);
    group.setGroupStopOption(false, IGroup.STOP_AFTER_N_ITERATIONS, 0);
    group.setStartingURL('http://localhost:8396/petstore');
    group.setContainsLoginTask(false);
    group.setUseUrlRewritingSessionManagement(false);
    group.setAuthenticationMechanism(IHttpGroup.NO_AUTHENTICATION);
    group.setAuthenticationDomainName('');
    group.setUseClientSSLAuthentication(false);
    var group = loadtest.addEndingGroup();
    group.setGroupPauseOption(false, 0, IGroup.PAUSE_START_OF_TEST, 0);
    group.setGroupStopOption(false, IGroup.STOP_AFTER_N_ITERATIONS, 0);
    group.setStartingURL('http://localhost:8396/petstore');
    group.setContainsLoginTask(false);
    group.setUseUrlRewritingSessionManagement(false);
    group.setAuthenticationMechanism(IHttpGroup.NO_AUTHENTICATION);
    group.setAuthenticationDomainName('');
    group.setUseClientSSLAuthentication(false);
}

function global_validation(request)
{
}

function group_1() // script function for StartingGroup
{
}

function group_2() // script function for ActionGroup1
{
    executeTask_1();
    executeTask_2();
    executeTask_3();
    executeTask_4();
    executeTask_5();
    executeTask_6();
}

function executeTask_1() // script function for Task1 [/reventmodule/Entity/EVEvent?ids=34185325523320832&bindUserData=true]
{
    var request = engine.createGetRequest(1, 'Task1', 'https', 'qa-khcg-ai.foxconn.com', 443, '/reventmodule/Entity/EVEvent?ids=34185325523320832&bindUserData=true');
    request.setIgnored(false);
    request.setTimeout(120);
    request.addHeader('Authorization', LOADTEST_TOKEN, '');
    request.setExpectedResponseCode(200);
    var successful = engine.execute(request);
    if (!successful) {
        log('Task1 failed: ' + request.getReasonForFailure());
    }
    engine.release(request);
}

function executeTask_2() // script function for Task2 [/reventmodule/Basic/EVEventMedia?eVEventIds=34123425668794368]
{
    var request = engine.createGetRequest(2, 'Task2', 'https', 'qa-khcg-ai.foxconn.com', 443, '/reventmodule/Basic/EVEventMedia?eVEventIds=34123425668794368');
    request.setIgnored(false);
    request.setTimeout(120);
    request.addHeader('Authorization', LOADTEST_TOKEN, '');
    request.setExpectedResponseCode(200);
    var successful = engine.execute(request);
    if (!successful) {
        log('Task2 failed: ' + request.getReasonForFailure());
    }
    engine.release(request);
}

function executeTask_3() // script function for Task2b [/rstorage/Extended/FileResource/34184848690100224]（PC 版，用 fileResourceId 不是 media 記錄自己的 id）
{
    var request = engine.createGetRequest(3, 'Task2b', 'https', 'qa-citygpt.foxconn.com', 443, '/rstorage/Extended/FileResource/34184848690100224');
    request.setIgnored(false);
    request.setTimeout(120);
    request.addHeader('Authorization', LOADTEST_TOKEN, '');
    request.addHeader('ocp-apim-subscription-key', 'REPLACE_ME', '');
    request.addHeader('x-api-version', '1', '');
    request.setExpectedResponseCode(200);
    var successful = engine.execute(request);
    if (!successful) {
        log('Task2b failed: ' + request.getReasonForFailure());
    }
    engine.release(request);
}

function executeTask_4() // script function for Task2c [/rstorage/Extended/FileResource/34184848895096832]（行動版）
{
    var request = engine.createGetRequest(4, 'Task2c', 'https', 'qa-citygpt.foxconn.com', 443, '/rstorage/Extended/FileResource/34184848895096832');
    request.setIgnored(false);
    request.setTimeout(120);
    request.addHeader('Authorization', LOADTEST_TOKEN, '');
    request.addHeader('ocp-apim-subscription-key', 'REPLACE_ME', '');
    request.addHeader('x-api-version', '1', '');
    request.setExpectedResponseCode(200);
    var successful = engine.execute(request);
    if (!successful) {
        log('Task2c failed: ' + request.getReasonForFailure());
    }
    engine.release(request);
}

function executeTask_5() // script function for Task3 [/reventmodule/Basic/EVFormField?eVEventIds=34185325523320832&category=Registration&pageRows=999]
{
    var request = engine.createGetRequest(5, 'Task3', 'https', 'qa-khcg-ai.foxconn.com', 443, '/reventmodule/Basic/EVFormField?eVEventIds=34185325523320832&category=Registration&pageRows=999');
    request.setIgnored(false);
    request.setTimeout(120);
    request.addHeader('Authorization', LOADTEST_TOKEN, '');
    request.setExpectedResponseCode(200);
    var successful = engine.execute(request);
    if (!successful) {
        log('Task3 failed: ' + request.getReasonForFailure());
    }
    engine.release(request);
}

function executeTask_6() // script function for Task4 [/reventmodule/Entity/EVRegistration]
{
    var request = engine.createPostRequest(6, 'Task4', 'https', 'qa-khcg-ai.foxconn.com', 443, '/reventmodule/Entity/EVRegistration');
    request.setIgnored(false);
    request.setTimeout(120);
    request.addHeader('Authorization', LOADTEST_TOKEN, '');
    request.addHeader('Content-Type', 'application/json', '');
    request.addRequestEntity('{"evEventEntity":{"key":"34185325523320832"},"evRegistrationDatas":[{"evFormFieldEntity":{"key":"34185325526138880"},"value":"1"}],"evEventSessions":[{"key":"34185325525680128"}],"registrationSource":"LoadTest"}');
    request.setExpectedResponseCode(200);
    var successful = engine.execute(request);
    if (!successful) {
        log('Task4 failed: ' + request.getReasonForFailure());
    } else {
        log('Task4 response: ' + request.getResponseAsString());
    }
    engine.release(request);
}

function group_3() // script function for EndingGroup
{
}
