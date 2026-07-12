"""集中管理選擇器。

策略：語意錨點（label / aria-label / button name）為主，PrimeVue 語意 class 為輔。
不使用 Tailwind utility class、不依賴 Vue 動態 ID（pv_id_*）。

證據來源（2026-05-05 從前端 src 挖出，詳 lib/selectors_candidates.md）：
- STFilter.vue InputText 有 :aria-label="item.Name"；MultiSelect / DatePicker 無，需經 <label> 錨定
- EVEventEntity.ts getCondition() 確定 3 個篩選欄位
- STCommon.model.ts hasLabel 預設 true → <label> 一定渲染
"""
from __future__ import annotations
from playwright.sync_api import Locator, Page


class EventListPage:
    """活動列表頁（/entry/evevent）的元件選擇器。"""

    PATH = "/entry/evevent"

    @staticmethod
    def name_input(page: Page) -> Locator:
        return page.get_by_label("活動名稱").first

    @staticmethod
    def organizer_input(page: Page) -> Locator:
        return (
            page.locator("label")
            .filter(has_text="主辦單位")
            .locator("xpath=..")
            .locator(".p-multiselect")
        )

    @staticmethod
    def date_input(page: Page) -> Locator:
        return (
            page.locator("label")
            .filter(has_text="活動日期")
            .locator("xpath=..")
            .locator("input.p-datepicker-input")
        )

    @staticmethod
    def reset_button(page: Page) -> Locator:
        return page.get_by_role("button", name="重置")

    @staticmethod
    def apply_button(page: Page) -> Locator:
        return page.get_by_role("button", name="查詢")

    @staticmethod
    def list_rows(page: Page) -> Locator:
        return page.locator("table tbody tr")

    # --- 通用 helper：依表頭文字取欄位 ---

    @staticmethod
    def table_headers(page: Page) -> list[str]:
        headers = page.locator("table thead th, table thead td")
        return [(headers.nth(i).inner_text() or "").strip() for i in range(headers.count())]

    @staticmethod
    def column_index_by_header(page: Page, *keywords: str) -> int:
        """傳入一個或多個關鍵字，回傳第一個 header 文字含任一關鍵字的欄位 index。

        keywords 用「任一命中」語意：例如 column_index_by_header(page, "報到單位", "負責單位")
        會找到任一表頭含 "報到單位" 或 "負責單位" 的欄。
        """
        if not keywords:
            raise ValueError("至少傳一個 keyword")
        headers = EventListPage.table_headers(page)
        for i, h in enumerate(headers):
            if any(k in h for k in keywords):
                return i
        raise AssertionError(f"找不到含任一關鍵字 {keywords} 的表頭；現有表頭：{headers}")

    @staticmethod
    def cell_text(row: Locator, *keywords: str) -> str:
        """row 是某一行 Locator；依關鍵字找欄位 index 取該格文字。"""
        idx = EventListPage.column_index_by_header(row.page, *keywords)
        return (row.locator("td").nth(idx).inner_text() or "").strip()

    @staticmethod
    def column_values(page: Page, *keywords: str) -> list[str]:
        """取整個欄位所有列的值。"""
        idx = EventListPage.column_index_by_header(page, *keywords)
        rows = EventListPage.list_rows(page)
        return [(rows.nth(i).locator("td").nth(idx).inner_text() or "").strip() for i in range(rows.count())]

    # --- 沿用：原 name_cell_text 改用通用 helper ---

    @staticmethod
    def name_cell_text(row: Locator) -> str:
        return EventListPage.cell_text(row, "活動名稱")

    # --- 操作欄（src 解碼 2026-05-06：EVEventEntity.actionCol 4 個 icon group）---
    # 順序：1=activityData / 2=enrollList / 3=activityLink / 4=moreActions
    # icon 透過 STMenubarAction.Url 對應 icon-chart / icon-file / icon-link / icon-more

    @staticmethod
    def action_cell(row: Locator) -> Locator:
        """操作欄整格（最後一欄）。"""
        idx = EventListPage.column_index_by_header(row.page, "操作")
        return row.locator("td").nth(idx)

    @staticmethod
    def action_icon(row: Locator, group: int) -> Locator:
        """操作欄 4 個 icon 之一（group: 1=活動數據, 2=報名名單, 3=活動連結, 4=更多）。"""
        if group not in (1, 2, 3, 4):
            raise ValueError("group 必須是 1/2/3/4")
        # 使用者觀察：DOM 是 td > div > div:nth-child(N) 結構
        return EventListPage.action_cell(row).locator(f"div > div:nth-child({group})")

    @staticmethod
    def create_button(page: Page) -> Locator:
        """活動列表頁「新增」按鈕（aria-label="新增"，DOM 事實：2026-05-20 dump）。"""
        return page.get_by_role("button", name="新增", exact=True)

    @staticmethod
    def menu_item_by_text(page: Page, text: str) -> Locator:
        """展開 menu 後的選項，依文字命中。"""
        return page.get_by_role("menuitem", name=text).or_(
            page.get_by_text(text, exact=True)
        ).first


class DashboardDetailPage:
    """活動數據總覽頁（/DashboardDetail/source=EVEvent&pkid=<id>）。

    src 解碼 2026-05-06：
    - URL pattern：`/DashboardDetail/source=EVEvent&pkid=<pkid>`（注意 `?` → `=`）
    - 圖表暫隱藏（P1 階段，全 mock 註解掉）
    - 報名名單 section title 元素 id="registrationListTitle"，文字="報名名單"
    - viewEnrollList 跳轉時用 sessionStorage.dashboardDetailScrollTo='registrationList' 觸發 scrollIntoView
    - 報名名單 toolbar 有「下載報名資料」按鈕（src: PageSectionADActivityRegistrationList），但 handleToolbarAction 目前是 console.log，無真實匯出
    """

    @staticmethod
    def url_pattern_match(url: str, pkid: str | None = None) -> bool:
        if "DashboardDetail" not in url:
            return False
        if "source=EVEvent" not in url:
            return False
        if pkid and f"pkid={pkid}" not in url:
            return False
        return True

    @staticmethod
    def registration_title(page: Page) -> Locator:
        """報名名單 section 的標題。"""
        return page.locator("#registrationListTitle").or_(
            page.get_by_text("報名名單", exact=True)
        ).first

    @staticmethod
    def download_registration_button(page: Page) -> Locator:
        """報名名單 section 的「下載報名資料」toolbar 按鈕（目前只 console.log）。"""
        return page.get_by_role("button", name="下載報名資料")

    @staticmethod
    def page_title_text(page: Page) -> str:
        """頁面 title（左側青條 + 標題，會顯示活動名稱）。"""
        return (
            page.locator('[class*="leadingHeadline"], h1, h2').first.inner_text() or ""
        ).strip()


class ActivityInfoPage:
    """活動資訊頁（公開報名頁，/ActivityInfo?evMainEventId=...&evEventId=...）。

    src 解碼 2026-05-14（ActivityInfo.vue）：
    - 主視覺 banner：<img :src="bannerImageUrl" alt="" @load="imageLoaded = true">
    - imageLoaded=true 後 img 有 opacity-100 class；未載入時 opacity-0
    - bannerImageUrl 由 fileSvc.getImageByResourceId(fileResourceId) 取得
    """

    @staticmethod
    def banner_img(page: "Page") -> "Locator":
        return page.locator("img.object-cover").first

    @staticmethod
    def banner_loaded(page: "Page") -> "Locator":
        """圖片載入完成後 opacity-100 class 的 img。"""
        return page.locator("img.object-cover.opacity-100").first


class EVEventEditPage:
    """活動編輯頁（/EVEventEdit/source=EVEvent&pkid=<id>）。

    src 解碼 2026-05-06（EVEventEdit.controller.ts）：
    - 從活動列表「點活動名稱」進入（SetEvent_CellClick 處理 'name' field）
    - startTime/endTime 兩個 DatePicker，IsShowTime: true, hourFormat: '24'
    - **未實作**先後順序防呆：controller 中沒設 minDate/maxDate/disabledDates，submit 也無時間順序 validate
    """

    @staticmethod
    def url_pattern_match(url: str, pkid: str | None = None) -> bool:
        if "EVEventEdit" not in url:
            return False
        if "source=EVEvent" not in url:
            return False
        if pkid and f"pkid={pkid}" not in url:
            return False
        return True

    @staticmethod
    def date_input_by_label(page: Page, label_text: str) -> Locator:
        """依 label 文字找 DatePicker 的 input。"""
        return (
            page.locator("label")
            .filter(has_text=label_text)
            .locator("xpath=..")
            .locator("input.p-datepicker-input")
        ).first

    @staticmethod
    def field_datepicker_input(page: Page, field_id: str) -> Locator:
        """依 data-field-id 找 datepicker 內的 input（不依賴 label 文字，結構穩定）。"""
        return page.locator(f"[data-field-id='{field_id}'] input.p-datepicker-input").first

    @staticmethod
    def start_time_input(page: Page) -> Locator:
        return EVEventEditPage.field_datepicker_input(page, "ActivityInfo_Introduction_startTime")

    @staticmethod
    def end_time_input(page: Page) -> Locator:
        return EVEventEditPage.field_datepicker_input(page, "ActivityInfo_Introduction_endTime")

    @staticmethod
    def save_button(page: Page) -> Locator:
        return page.get_by_role("button", name="儲存").or_(
            page.get_by_role("button", name="確認修改")
        ).first

    @staticmethod
    def open_direct(page: Page, base_url: str, pkid: str) -> None:
        """直連 EVEventEdit 頁（用 config['event_edit_pkid']）。比從列表點入快且穩定。"""
        url = f"{base_url}/entry/EVEventEdit/source=EVEvent&pkid={pkid}"
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

    @staticmethod
    def open_from_event_list(page: Page, base_url: str) -> None:
        """從活動列表點第一筆活動名稱進入 EVEventEdit 頁。"""
        page.goto(base_url + EventListPage.PATH, wait_until="domcontentloaded")
        EventListPage.reset_button(page).wait_for(state="visible", timeout=15000)
        page.wait_for_timeout(1500)
        first_row = EventListPage.list_rows(page).nth(0)
        idx = EventListPage.column_index_by_header(page, "活動名稱")
        first_row.locator("td").nth(idx).click()
        page.wait_for_url("**/EVEventEdit/**", timeout=15000)
        page.wait_for_timeout(2000)

    @staticmethod
    def field_container(page: Page, field_id: str) -> Locator:
        """依 data-field-id 找欄位容器（EVEventEdit 每個欄位的唯一穩定錨點）。"""
        return page.locator(f"[data-field-id='{field_id}']")

    @staticmethod
    def field_label(page: Page, field_id: str) -> Locator:
        """依 data-field-id 找欄位主 label（容許前綴 * 必填符號）。
        用 .first 避免 radiobutton/checkbox 子選項 label 觸發 strict mode。"""
        return page.locator(f"[data-field-id='{field_id}'] label").first

    @staticmethod
    def field_component(page: Page, field_id: str, pc_name: str) -> Locator:
        """依 data-field-id + data-pc-name 找欄位內的 PrimeVue 元件。"""
        return page.locator(f"[data-field-id='{field_id}'] [data-pc-name='{pc_name}']").first

    @staticmethod
    def section_header(page: Page, title: str) -> Locator:
        """找 EVEventEdit 頁的 section header，依標題文字定位。
        DOM 事實（2026-05-18 HTML dump）：
          <div data-anchor="ActivityMgmt_ActivityInfo" ...>
            <div class="text-h3 ...">活動資訊</div>  ← 直接子 div，純文字，非 heading 元素
          </div>
        用 [data-anchor] > div + has_text 定位，不依賴 Tailwind class 或 heading role。
        """
        return page.locator("[data-anchor] > div").filter(has_text=title).first


class CitizenLoginPage:
    """公民端獨立登入頁（路徑由 config.citizen_entry_path 決定）。

    注意：公民端登入入口與後台 /entry/login 不同，路徑待確認後填入 config。
    selector 暫以 placeholder 為主（與後台登入頁同名元件，待 HTML dump 後修正）。
    """

    @staticmethod
    def open(page: Page, base_url: str, citizen_entry_path: str) -> None:
        page.goto(base_url + citizen_entry_path, wait_until="domcontentloaded")

    @staticmethod
    def username_input(page: Page) -> Locator:
        return page.get_by_placeholder("請輸入帳號")

    @staticmethod
    def password_input(page: Page) -> Locator:
        return page.get_by_placeholder("請輸入密碼")

    @staticmethod
    def submit_button(page: Page) -> Locator:
        return page.get_by_role("button", name="登入")


class CitizenRegistrationPage:
    """前台活動報名頁（/ActivityInfo?evMainEventId=...&evEventId=...）。

    selector 暫以語意猜測為主；待實際 HTML dump 後對照修正。
    """

    PATH_TEMPLATE = "/ActivityInfo?evMainEventId={main_id}&evEventId={event_id}"

    @staticmethod
    def privacy_agree_button(page: Page) -> Locator:
        """個資使用聲明同意彈窗「同意」按鈕。"""
        return page.get_by_role("button", name="同意")

    @staticmethod
    def submit_button(page: Page) -> Locator:
        """報名表單送出按鈕。"""
        return page.get_by_role("button", name="送出")

    @staticmethod
    def activity_title(page: Page) -> Locator:
        """頁面顯示的活動標題（用於驗證頁面對應正確活動）。"""
        return page.locator("h1, h2").first
