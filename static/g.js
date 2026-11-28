/* G안 글래스 화면 (#37, 담당 D).
 *
 * gr.HTML의 js_on_load 본문으로 실행된다. Gradio가 넘겨 주는 이름:
 *   element  — 컴포넌트 루트. 이 안에 화면 DOM을 직접 만든다(gr.HTML의 value는 바꾸지 않는다).
 *   trigger  — Python 이벤트 호출. trigger('submit', {path}) = 분석 시작, trigger('stop') = 멈추기.
 *   props    — 컴포넌트 속성. props.disclaimer = explain.DISCLAIMER.
 *   upload   — JS File을 서버에 올리고 {path, url}을 돌려준다.
 * 분석 진행·결과는 숨긴 gr.JSON의 change 이벤트가 window.gApp.update(view)로 넘겨 준다.
 *
 * 보안: 서버에서 온 문자열은 모두 textContent로 넣는다. innerHTML은 이 파일 안의 고정 SVG에만 쓴다.
 */
(function () {
  "use strict";

  var root = element.querySelector(".g-root") || element;
  var SVGNS = "http://www.w3.org/2000/svg";
  var ORDER = ["loading", "result", "compare", "why", "more"];
  var SEGS = [
    ["result", "결과"],
    ["compare", "명화"],
    ["why", "색·선"],
    ["more", "화풍"],
  ];
  // 기록 (FR9): 이 브라우저의 localStorage에만 둔다. 원본 사진은 저장하지 않는다(NFR6).
  var HIST_KEY = "g-history-v1";
  var HIST_MAX = 30;
  var HIST_THUMB_PX = 160;
  var HIST_WORK_PX = 96;
  var SWIPE_PX = 110;
  var UNDO_MS = 4000;
  var KINDS = ["전체", "사진", "그림", "스케치"];
  var STEPS = [
    ["이미지 맞추기", "긴 변을 512px로 맞춰요"],
    ["소재·분위기 보기", "CLIP으로 소재와 분위기를 봐요"],
    ["색·선 재기", "대표색과 선 특징을 재요"],
    ["두 관점 합치기", "Top 3와 신뢰 등급을 정해요"],
  ];
  var DISCLAIMER =
    (props && typeof props.disclaimer === "string" && props.disclaimer) ||
    "픽셀 수치 기반의 통계적 해석이며 미술사적 평가가 아닙니다.";
  var DRAG_CLOSE_PX = 120;
  var HOME_DELAY_MS = 480;

  // 이 파일 안의 고정 아이콘(서버 값 없음)
  var ICON = {
    logo:
      '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="1.6" stroke-linejoin="round" aria-hidden="true"><path d="M12 3a9 9 0 100 18c1.1 0 1.6-.8 1.6-1.6 0-.5-.2-.8-.5-1.2-.3-.3-.5-.7-.5-1.2 0-.9.7-1.6 1.6-1.6H16a5 5 0 005-5c0-4.2-4-7.4-9-7.4z"></path><circle cx="9" cy="10.5" r="2.8" stroke="#FBE3A6" stroke-width="1.8"></circle><circle cx="9" cy="10.5" r="0.9" fill="#FBE3A6" stroke="none"></circle><circle cx="15.2" cy="8.2" r="1.1" fill="#FFFFFF" stroke="none"></circle></svg>',
    album:
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="3"></rect><circle cx="9" cy="10" r="1.8"></circle><path d="M20.5 16l-5-5-8.5 8.5"></path></svg>',
    check:
      '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"></path></svg>',
    checkGreen:
      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#166534" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"></path></svg>',
    camera:
      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 8h3l2-3h6l2 3h3v11H4z"></path><circle cx="12" cy="13" r="3.5"></circle></svg>',
    next:
      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"></path></svg>',
    prev:
      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M15 6l-6 6 6 6"></path></svg>',
    legendMe:
      '<svg width="22" height="10" aria-hidden="true"><line x1="1" y1="5" x2="21" y2="5" stroke="#EA580C" stroke-width="2.2"></line><circle cx="11" cy="5" r="3.4" fill="#EA580C" stroke="#FFFFFF" stroke-width="1.5"></circle></svg>',
    legendAvg:
      '<svg width="22" height="10" aria-hidden="true"><line x1="1" y1="5" x2="21" y2="5" stroke="#1D4ED8" stroke-width="2" stroke-dasharray="5 4"></line></svg>',
    history:
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3.5 12a8.5 8.5 0 102.5-6"></path><path d="M3.5 4v4h4"></path><path d="M12 7.5V12l3 2"></path></svg>',
    historyDark:
      '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#4A4F5C" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3.5 12a8.5 8.5 0 102.5-6"></path><path d="M3.5 4v4h4"></path><path d="M12 7.5V12l3 2"></path></svg>',
    trash:
      '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 002 2h6a2 2 0 002-2l1-12M9 7V4h6v3"></path></svg>',
    chevron:
      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9BA1AD" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M9 6l6 6-6 6"></path></svg>',
  };

  // --- 작은 도우미 -----------------------------------------------------------

  function reduced() {
    return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }

  function setAttrs(el, attrs) {
    if (!attrs) return;
    Object.keys(attrs).forEach(function (k) {
      var v = attrs[k];
      if (v === null || v === undefined || v === false) return;
      if (k === "text") el.textContent = String(v);
      else if (k === "on") {
        Object.keys(v).forEach(function (ev) {
          el.addEventListener(ev, v[ev]);
        });
      } else el.setAttribute(k, v === true ? "" : String(v));
    });
  }

  function append(el, kids) {
    if (kids === null || kids === undefined) return;
    if (!Array.isArray(kids)) kids = [kids];
    kids.forEach(function (k) {
      if (k === null || k === undefined || k === false) return;
      el.appendChild(typeof k === "string" ? document.createTextNode(k) : k);
    });
  }

  function h(tag, attrs, kids) {
    var el = document.createElement(tag);
    setAttrs(el, attrs);
    append(el, kids);
    return el;
  }

  function sv(tag, attrs, kids) {
    var el = document.createElementNS(SVGNS, tag);
    setAttrs(el, attrs);
    append(el, kids);
    return el;
  }

  // 고정 SVG 문자열(ICON)만 받는다.
  function icon(name) {
    var t = document.createElement("template");
    t.innerHTML = ICON[name];
    return t.content.firstChild;
  }

  function str(v) {
    return v === null || v === undefined ? "" : String(v);
  }

  function num(v) {
    var n = Number(v);
    return isFinite(n) ? n : 0;
  }

  // 서버·저장소에서 온 이미지 주소는 data:image/... 만 쓴다(다른 주소로 요청을 보내지 않게).
  function safeImg(v) {
    return typeof v === "string" && /^data:image\/(jpeg|png|webp);base64,[A-Za-z0-9+/=]+$/.test(v)
      ? v
      : "";
  }

  function safeColor(v) {
    return typeof v === "string" && /^#[0-9a-fA-F]{6}$/.test(v) ? v : "";
  }

  // 받침에 따라 조사를 고른다. 한글이 아니면 "을(를)"처럼 둘 다 쓴다.
  function josa(word, withFinal, withoutFinal) {
    var c = str(word).charCodeAt(str(word).length - 1);
    if (c >= 0xac00 && c <= 0xd7a3) return (c - 0xac00) % 28 ? withFinal : withoutFinal;
    return withFinal + "(" + withoutFinal + ")";
  }

  // --- 상태 -----------------------------------------------------------------

  var st = {
    step: "home",
    closing: false,
    busy: false, // 서버 분석이 진행 중인지
    runId: 0,
    view: null,
    loadingStep: 0,
    stream: null,
    camToken: 0,
    camFailed: false,
    photoUrl: null,
    timers: [],
    rafs: [],
    toastT: 0,
    drag: null,
    cmpSel: 0, // 명화 페이지에서 고른 명화 번호
    whyMode: "avg", // 색·선 레이더 비교 대상: "avg"(1위 평균) | "work"(고른 명화)
    tabSeen: {}, // 처음 본 레이더 탭(처음에만 그리기 움직임, FR4.7)
    hist: [],
    histFilter: "전체",
    removing: false,
    undo: null,
    undoT: 0,
  };

  function later(ms, fn) {
    var t = setTimeout(fn, ms);
    st.timers.push(t);
    return t;
  }

  function clearAnims() {
    st.timers.forEach(clearTimeout);
    st.rafs.forEach(cancelAnimationFrame);
    st.timers = [];
    st.rafs = [];
  }

  // delay 뒤 dur 동안 0→1(감속)로 fn(p)를 부른다. 애니메이션 줄이기면 바로 fn(1).
  function runAnim(delay, dur, fn) {
    if (reduced()) {
      fn(1);
      return;
    }
    fn(0);
    later(delay, function () {
      var t0 = performance.now();
      function tick(now) {
        var p = Math.min(1, (now - t0) / dur);
        fn(1 - Math.pow(1 - p, 3));
        if (p < 1) st.rafs.push(requestAnimationFrame(tick));
      }
      st.rafs.push(requestAnimationFrame(tick));
    });
  }

  // --- 뼈대 -----------------------------------------------------------------

  var video = h("video", {
    class: "g-video",
    muted: true,
    playsinline: true,
    autoplay: true,
    "aria-hidden": "true",
  });
  video.muted = true;
  var photo = h("img", { class: "g-photo", alt: "" });
  var bg = h("div", { class: "g-bg", "aria-hidden": "true" }, [video, photo]);

  var frame = h("div", { class: "g-frame", "aria-hidden": "true" }, [
    h("span", { class: "g-c tl" }),
    h("span", { class: "g-c tr" }),
    h("span", { class: "g-c bl" }),
    h("span", { class: "g-c br" }),
  ]);
  var fileInput = h("input", {
    type: "file",
    accept: "image/*",
    class: "g-file",
    tabindex: "-1",
    "aria-hidden": "true",
    "data-testid": "g-file",
  });
  var albumBtn = h(
    "button",
    { type: "button", class: "g-album", "aria-label": "앨범에서 고르기", "data-testid": "g-album" },
    [icon("album")]
  );
  var shutterBtn = h(
    "button",
    { type: "button", class: "g-shutter", "aria-label": "찍어서 분석하기", "data-testid": "g-shutter" },
    [h("span")]
  );
  var histBtn = h(
    "button",
    { type: "button", class: "g-histbtn", "aria-label": "지난 분석 기록", "data-testid": "g-history" },
    [icon("history")]
  );
  var home = h("section", { class: "g-home g-intro", "aria-label": "이미지 가져오기" }, [
    h("div", { class: "g-mask", "aria-hidden": "true" }, [h("div", { class: "g-hole" })]),
    frame,
    h("div", { class: "g-hint" }, [h("span", { class: "g-pill", text: "그림을 틀에 맞춰 주세요" })]),
    h("nav", { class: "g-dock", "aria-label": "이미지 가져오기" }, [albumBtn, shutterBtn, histBtn]),
    h("p", { class: "g-note", text: DISCLAIMER }),
  ]);

  var logoBtn = h("button", { type: "button", class: "g-logo", "data-testid": "g-logo" }, [icon("logo")]);

  var segBtns = SEGS.map(function (s) {
    return h(
      "button",
      { type: "button", class: "g-seg", "data-go": s[0], "data-testid": "g-nav-" + s[0] },
      [
        h("span", { class: "g-seg-bar", "aria-hidden": "true" }, [h("span")]),
        h("span", { class: "g-seg-label", text: s[1] }),
      ]
    );
  });
  var nav = h("nav", { class: "g-nav", "aria-label": "결과 단계" }, segBtns);

  var handle = h("div", { class: "g-handle", "aria-hidden": "true", "data-testid": "g-handle" }, [
    h("span"),
  ]);
  var pane = h("div", { class: "g-pane" });
  var sheet = h("section", { class: "g-sheet", "aria-label": "분석" }, [handle, pane]);
  var toastEl = h("div", { class: "g-toast", role: "alert", "data-testid": "g-toast" });

  // 명화 페이지의 시트 위쪽(머리말·두 그림·유사도 배지). 명화 단계에서만 보인다 (FR8.2).
  var cmpTop = h("div", { class: "g-cmp-top", "aria-hidden": "true", "data-testid": "g-cmp-top" });

  // 기록을 지운 뒤 4초 동안 보이는 되돌리기 (FR9.3)
  var undoText = h("span");
  var undoBtn = h("button", { type: "button", class: "g-undo-btn", "data-testid": "g-hist-undo", text: "되돌리기" });
  var undoEl = h("div", { class: "g-undo", role: "status", "data-testid": "g-undo" }, [undoText, undoBtn]);

  // 모두 지우기 확인 창 (FR9.5)
  var dlgBody = h("p", { id: "g-dlg-body", class: "g-dlg-body" });
  var dlgCancel = h("button", { type: "button", class: "g-dlg-btn", "data-testid": "g-hist-cancel", text: "취소" });
  var dlgOk = h("button", { type: "button", class: "g-dlg-btn g-dlg-danger", "data-testid": "g-hist-confirm", text: "지우기" });
  var dlg = h("div", { class: "g-dlg", role: "dialog", "aria-modal": "true", "aria-labelledby": "g-dlg-title", "aria-describedby": "g-dlg-body" }, [
    h("h2", { id: "g-dlg-title", class: "g-dlg-title", text: "기록을 모두 지울까요?" }),
    dlgBody,
    h("div", { class: "g-dlg-actions" }, [dlgCancel, dlgOk]),
  ]);
  var dlgBack = h("div", { class: "g-dlg-back", hidden: true, "data-testid": "g-hist-dialog" }, [dlg]);

  var app = h("div", { class: "g-app", "data-step": "home", "data-bg": "none" }, [
    bg,
    h("div", { class: "g-shade", "aria-hidden": "true" }),
    h("div", { class: "g-topfade", "aria-hidden": "true" }),
    home,
    cmpTop,
    logoBtn,
    nav,
    sheet,
    undoEl,
    toastEl,
    dlgBack,
    fileInput,
  ]);
  root.appendChild(h("div", { class: "g-stage" }, [app]));

  // --- 배경: 카메라·사진 -------------------------------------------------------

  function setBg(kind) {
    app.setAttribute("data-bg", kind);
  }

  function canUseCamera() {
    return !!(
      window.isSecureContext &&
      navigator.mediaDevices &&
      typeof navigator.mediaDevices.getUserMedia === "function"
    );
  }

  function stopTracks(stream) {
    try {
      stream.getTracks().forEach(function (t) {
        t.stop();
      });
    } catch (e) {
      /* 이미 멈춘 스트림 */
    }
  }

  // 보안 주소이고 권한이 있으면 실시간 미리보기. 안 되면(권한 거부·카메라 없음) 어두운 배경 그대로.
  function startCamera() {
    if (st.stream || st.camFailed || !canUseCamera() || st.step !== "home") return;
    if (document.visibilityState === "hidden") return;
    var token = ++st.camToken;
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false })
      .then(function (stream) {
        if (token !== st.camToken || st.step !== "home") {
          stopTracks(stream);
          return;
        }
        st.stream = stream;
        video.srcObject = stream;
        var p = video.play();
        if (p && p.catch) p.catch(function () {});
        setBg("camera");
      })
      .catch(function (err) {
        // 다시 묻지 않도록 한 번 실패하면 이번 화면에서는 선택 창만 쓴다.
        st.camFailed = true;
        console.info("[g] 카메라 미리보기를 쓰지 않습니다:", err && err.name);
      });
  }

  function stopCamera() {
    st.camToken++;
    if (st.stream) stopTracks(st.stream);
    st.stream = null;
    video.srcObject = null;
    if (app.getAttribute("data-bg") === "camera") setBg("none");
  }

  function cameraReady() {
    return !!(st.stream && video.readyState >= 2 && video.videoWidth > 0);
  }

  function setPhoto(file) {
    clearPhoto();
    try {
      st.photoUrl = URL.createObjectURL(file);
      photo.src = st.photoUrl;
      setBg("photo");
    } catch (e) {
      setBg("none");
    }
  }

  function clearPhoto() {
    if (st.photoUrl) URL.revokeObjectURL(st.photoUrl);
    st.photoUrl = null;
    photo.removeAttribute("src");
    if (app.getAttribute("data-bg") === "photo") setBg("none");
  }

  // 지금 카메라 화면에서 4:5 틀 안쪽을 잘라 JPEG File로 만든다.
  function capture() {
    var vw = video.videoWidth;
    var vh = video.videoHeight;
    var vr = video.getBoundingClientRect();
    var fr = frame.getBoundingClientRect();
    var scale = Math.max(vr.width / vw, vr.height / vh);
    var ox = vr.left + (vr.width - vw * scale) / 2;
    var oy = vr.top + (vr.height - vh * scale) / 2;
    var sx = Math.max(0, (fr.left - ox) / scale);
    var sy = Math.max(0, (fr.top - oy) / scale);
    var sw = Math.min(fr.width / scale, vw - sx);
    var sh = Math.min(fr.height / scale, vh - sy);
    if (!(sw >= 16 && sh >= 16)) {
      sx = 0;
      sy = 0;
      sw = vw;
      sh = vh;
    }
    var canvas = document.createElement("canvas");
    canvas.width = Math.round(sw);
    canvas.height = Math.round(sh);
    canvas.getContext("2d").drawImage(video, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(
      function (blob) {
        if (!blob) {
          toast("사진을 찍지 못했어요. 앨범에서 골라 주세요.");
          return;
        }
        startAnalysis(new File([blob], "camera.jpg", { type: "image/jpeg" }));
      },
      "image/jpeg",
      0.92
    );
  }

  // --- 알림 -----------------------------------------------------------------

  function toast(msg) {
    toastEl.textContent = str(msg) || "문제가 생겼어요. 다시 해 보세요.";
    toastEl.setAttribute("data-show", "");
    clearTimeout(st.toastT);
    st.toastT = setTimeout(function () {
      toastEl.removeAttribute("data-show");
    }, 3200);
  }

  // --- 화면 전환 ---------------------------------------------------------------

  // 지금 화면 데이터에 명화 비교가 있는지. 없으면 명화 페이지와 진행 막대의 "명화"를 숨긴다 (FR8.9).
  function hasCompare(v) {
    v = v || st.view;
    return !!(v && v.compare && Array.isArray(v.compare.works) && v.compare.works.length);
  }

  function selWork() {
    if (!hasCompare()) return null;
    var works = st.view.compare.works;
    var w = works[Math.max(0, Math.min(works.length - 1, st.cmpSel))];
    return w && typeof w === "object" ? w : null;
  }

  // 색·선 레이더의 명화 탭 이름. 명화 페이지 제목과 맞춘다: 첫 명화가 1위 화가 작품이면 "가장 닮은",
  // 화가와 상관없이 고른 첫 명화면 "가장 비슷한", "다른 명화와 비교"에서 2·3번째를 골랐으면 "고른".
  function workTabLabel(w) {
    var first = !st.cmpSel;
    if (first && w && w.top1_work) return "가장 닮은 명화와";
    if (first) return "가장 비슷한 명화와";
    return "고른 명화와";
  }

  // 새 화면 데이터(분석 결과·기록)를 받을 때 명화 선택·레이더 탭을 처음 상태로.
  function resetViewState() {
    st.cmpSel = 0;
    st.whyMode = "avg";
    st.tabSeen = {};
  }

  function setStep(step) {
    st.step = step;
    app.setAttribute("data-step", step);
    logoBtn.setAttribute(
      "aria-label",
      step === "loading"
        ? "분석을 멈추고 처음 화면으로"
        : step === "history"
          ? "처음 화면으로"
          : "Art Style Mirror 처음 화면"
    );
    var cmpOn = hasCompare();
    nav.setAttribute("data-segs", cmpOn ? "4" : "3");
    segBtns[1].hidden = !cmpOn;
    cmpTop.setAttribute("aria-hidden", step === "compare" ? "false" : "true");
    var idx = ORDER.indexOf(step);
    segBtns.forEach(function (b, i) {
      if (i + 1 <= idx) b.setAttribute("data-fill", "");
      else b.removeAttribute("data-fill");
      if (i + 1 === idx) b.setAttribute("aria-current", "step");
      else b.removeAttribute("aria-current");
    });
  }

  function replayHomeIntro() {
    home.classList.remove("g-intro");
    void home.offsetWidth; // 애니메이션을 처음부터 다시
    home.classList.add("g-intro");
  }

  function setPane(kids, dir, extraClass) {
    var next = h("div", {
      class: "g-pane in-" + (dir || "next") + (extraClass ? " " + extraClass : ""),
    });
    append(next, kids);
    sheet.replaceChild(next, pane);
    pane = next;
    return next;
  }

  function go(step) {
    if (st.closing || step === st.step) return;
    if (step !== "loading" && !st.view) return;
    if (step === "compare" && !hasCompare()) return;
    var dir = ORDER.indexOf(step) >= ORDER.indexOf(st.step) ? "next" : "prev";
    clearAnims();
    setStep(step);
    if (step === "loading") paneLoading(dir);
    else if (step === "result") paneResult(st.view, dir);
    else if (step === "compare") paneCompare(st.view, dir);
    else if (step === "why") paneWhy(st.view, dir);
    else if (step === "more") paneMore(st.view, dir);
  }

  // 시트가 아래로 내려가며 첫 화면이 나타난다. 분석 중이면 서버 분석도 멈춘다(FR2.4, FR6.4, FR6.5).
  function goHome() {
    if (st.closing) return;
    if (st.step === "home") {
      replayHomeIntro();
      startCamera();
      return;
    }
    if (st.busy) trigger("stop");
    st.busy = false;
    st.runId++;
    st.view = null;
    clearAnims();
    hideUndo();
    closeConfirm(false);
    st.closing = true;
    app.setAttribute("data-closing", "");
    setTimeout(
      function () {
        st.closing = false;
        app.removeAttribute("data-closing");
        sheet.style.transform = "";
        setStep("home");
        setPane([], "next");
        clearPhoto();
        replayHomeIntro();
        startCamera();
      },
      reduced() ? 0 : HOME_DELAY_MS
    );
  }

  // --- 분석 시작·진행 ------------------------------------------------------------

  function startAnalysis(file) {
    if (st.step !== "home" || st.closing) return;
    if (file.type && file.type.indexOf("image/") !== 0) {
      toast("이미지 파일을 골라 주세요.");
      return;
    }
    var run = ++st.runId;
    stopCamera();
    setPhoto(file);
    st.view = null;
    st.busy = true;
    st.loadingStep = 0;
    go("loading");
    Promise.resolve()
      .then(function () {
        return upload(file);
      })
      .then(function (res) {
        if (run !== st.runId || st.step !== "loading") return;
        if (!res || !res.path) throw new Error("업로드 경로 없음");
        trigger("submit", { path: res.path });
      })
      .catch(function (err) {
        if (run !== st.runId) return;
        console.error("[g] 업로드 실패:", err);
        st.busy = false;
        toast("사진을 올리지 못했어요. 다시 해 보세요.");
        goHome();
      });
  }

  function openPicker() {
    fileInput.click();
  }

  // 숨긴 gr.JSON이 바뀔 때마다 불린다. 첫 화면으로 돌아간 뒤 늦게 온 값은 버린다.
  function update(v) {
    if (!v || typeof v !== "object" || st.step !== "loading" || !st.busy || st.closing) return;
    if (v.phase === "loading") {
      setLoadingStep(num(v.step));
    } else if (v.phase === "result" && v.view && typeof v.view === "object") {
      st.busy = false;
      st.view = v.view;
      resetViewState();
      saveHistory(v.view);
      finishLoading();
      later(reduced() ? 200 : 600, function () {
        if (st.step === "loading" && st.view) go("result");
      });
    } else if (v.phase === "error") {
      st.busy = false;
      toast(v.message);
      goHome();
    }
  }

  // --- 분석 중 (FR2) -----------------------------------------------------------

  var loadingRefs = null;

  function paneLoading(dir) {
    var items = STEPS.map(function (s) {
      var stateEl = h("span", { class: "g-step-state" });
      var li = h("li", { class: "g-step" }, [
        h("span", { class: "g-rail" }, [
          h("span", { class: "g-mk" }, [icon("check"), h("i")]),
          h("span", { class: "g-ln" }),
        ]),
        h("span", { class: "g-step-body" }, [
          h("span", { class: "g-step-top" }, [h("span", { class: "g-step-name", text: s[0] }), stateEl]),
          h("span", { class: "g-step-detail", text: s[1] }),
        ]),
      ]);
      return { li: li, state: stateEl };
    });
    var title = h("h1", { class: "g-title", text: "분석하고 있어요" });
    var sub = h("p", { class: "g-sub", text: "두 관점으로 따로 본 다음 하나로 합쳐요." });
    setPane(
      [
        title,
        sub,
        h(
          "ol",
          { class: "g-steps", "aria-live": "polite" },
          items.map(function (x) {
            return x.li;
          })
        ),
      ],
      dir
    );
    loadingRefs = { title: title, sub: sub, items: items };
    renderSteps(st.loadingStep);
  }

  function renderSteps(n) {
    if (!loadingRefs) return;
    loadingRefs.items.forEach(function (x, i) {
      var state = i < n ? "done" : i === n ? "now" : "wait";
      x.li.setAttribute("data-state", state);
      x.state.textContent = state === "done" ? "완료" : state === "now" ? "진행 중" : "대기";
    });
  }

  function setLoadingStep(n) {
    n = Math.max(0, Math.min(STEPS.length - 1, Math.floor(n)));
    if (n < st.loadingStep) return;
    st.loadingStep = n;
    renderSteps(n);
  }

  function finishLoading() {
    st.loadingStep = STEPS.length;
    renderSteps(STEPS.length);
    if (loadingRefs) {
      loadingRefs.title.textContent = "분석이 끝났어요";
      loadingRefs.sub.textContent = "결과를 보여 드릴게요.";
    }
  }

  // --- 공통 버튼 ---------------------------------------------------------------

  function actions(left, right) {
    return h("div", { class: "g-actions" }, [left, right]);
  }

  function ghostBtn(label, testid, onClick, iconName) {
    var kids = iconName ? [icon(iconName), label] : [label];
    return h("button", { type: "button", class: "g-btn g-btn-ghost", "data-testid": testid, on: { click: onClick } }, kids);
  }

  function mainBtn(label, testid, onClick, iconName, iconFirst) {
    var kids = iconFirst ? [icon(iconName), label] : [label, icon(iconName)];
    return h("button", { type: "button", class: "g-btn g-btn-main", "data-testid": testid, on: { click: onClick } }, kids);
  }

  function goWhy() {
    go("why");
  }
  function goMore() {
    go("more");
  }
  function goResult() {
    go("result");
  }

  // --- 결과 (FR3) --------------------------------------------------------------

  function levelChip(level) {
    var bars = Math.max(1, Math.min(3, num(level.bars)));
    var barEls = [1, 2, 3].map(function (i) {
      return h("i", { "data-on": i <= bars });
    });
    return h("span", { class: "g-chip", "data-level": str(level.label) }, [
      h("span", { class: "g-bars", "aria-hidden": "true" }, barEls),
      "신뢰 " + str(level.label),
    ]);
  }

  function rowsOf(list) {
    return (list || []).map(function (x) {
      return h("span", { class: "g-row" }, [
        h("span", { text: str(x.name) }),
        h("span", { text: num(x.pct) + "%" }),
      ]);
    });
  }

  function paneResult(v, dir) {
    var head = v.head || {};
    var level = v.level || {};
    var low = !!v.low;
    var kids = [
      h("p", { class: "g-eyebrow", text: head.intro }),
      h("h1", { class: "g-headline" + (low ? " g-low" : ""), text: head.title }),
      h("p", { class: "g-small g-mt2", text: head.sub }),
    ];

    var score = h("div", { class: "g-score" });
    if (!low) {
      var pct = Math.round(num(head.pct));
      var numText = document.createTextNode("0");
      score.appendChild(
        h("span", { class: "g-num" }, [
          numText,
          h("small", { text: "%" }),
        ])
      );
      score.appendChild(h("span", { class: "g-vr", "aria-hidden": "true" }));
      runAnim(450, 900, function (p) {
        numText.nodeValue = String(Math.round(p * pct));
      });
    }
    score.appendChild(
      h("span", { class: "g-level" }, [levelChip(level), h("span", { class: "g-level-note", text: level.note })])
    );
    kids.push(score);

    if (!low) {
      kids.push(
        h("p", {
          class: "g-small g-mt8",
          text: "%는 소재·분위기(CLIP)와 색·선(OpenCV)을 합친 확률이에요.",
        })
      );
      kids.push(
        h(
          "ol",
          { class: "g-top3", "aria-label": "닮은 화가 Top 3" },
          (v.top3 || []).map(function (t) {
            return h("li", null, [
              h("span", { class: "g-rank", text: num(t.rank) + "위 · " + num(t.pct) + "%" }),
              h("span", { class: "g-name", text: t.name, title: t.name_orig }),
            ]);
          })
        )
      );
      var views = v.views || {};
      if (views.same) {
        kids.push(
          h("div", { class: "g-box g-same" }, [
            icon("checkGreen"),
            h("span", null, [
              "두 관점 모두 ",
              h("strong", { text: views.clip }),
              josa(views.clip, "을", "를") + " 1위로 봤어요",
            ]),
          ])
        );
      } else {
        kids.push(
          h("div", { class: "g-box g-two" }, [
            h("span", null, [h("span", { class: "g-cap", text: "분위기 · CLIP" }), h("span", { class: "g-strong", text: views.clip })]),
            h("span", null, [h("span", { class: "g-cap", text: "색감·선 · OpenCV" }), h("span", { class: "g-strong", text: views.cv })]),
          ])
        );
      }
    } else {
      kids.push(
        h("div", { class: "g-lowcols" }, [
          h("div", { class: "g-lowcol" }, [h("b", { text: "소재·분위기 · CLIP" })].concat(rowsOf(v.low.clip))),
          h("div", { class: "g-lowcol" }, [h("b", { text: "색·선 · OpenCV" })].concat(rowsOf(v.low.cv))),
        ])
      );
      kids.push(
        h("p", {
          class: "g-tip",
          text: "그림이 화면을 꽉 채우게, 빛 반사 없이 다시 찍으면 더 뚜렷해질 수 있어요.",
        })
      );
    }

    kids.push(h("div", { class: "g-spacer" }));
    // 명화가 있으면 명화 페이지로 (FR3.7). 1위 화가 작품이 맨 앞일 때만 "가장 닮은".
    var next = hasCompare(v)
      ? mainBtn(
          v.compare.works[0] && v.compare.works[0].top1_work ? "가장 닮은 명화 보기" : "비슷한 명화 보기",
          "g-to-compare",
          goCompare,
          "next"
        )
      : mainBtn("색·선 비교 보기", "g-to-why", goWhy, "next");
    kids.push(actions(ghostBtn("다시 찍기", "g-retake", goHome, "camera"), next));
    setPane(kids, dir);
  }

  // --- 명화 (FR8) --------------------------------------------------------------

  var cmpRefs = null;

  // 명화 그림. 이미지가 없으면 화가 짧은 이름을 넣은 카드 (FR8.3).
  function workPic(w, cls) {
    var src = safeImg(w.image);
    if (src) return h("span", { class: cls + " g-has-img" }, [h("img", { src: src, alt: "" })]);
    return h("span", { class: cls + " g-noimg" }, [h("span", { text: w.short })]);
  }

  function swatches(list, label) {
    return h(
      "span",
      { class: "g-swatches", role: "img", "aria-label": label },
      (list || []).map(function (c) {
        var s = h("span");
        s.style.background = safeColor(c) || "#E2E4E9";
        return s;
      })
    );
  }

  function renderCmpTop(v, w) {
    var c = v.compare;
    var mineSrc = photo.getAttribute("src") || "";
    var badgeNum = h("b", { text: num(w.pct) + "%" });
    var badge = h("span", { class: "g-badge", "aria-hidden": "true", "data-testid": "g-badge" }, [
      badgeNum,
      h("span", { text: "유사도" }),
    ]);
    var mine = h(
      "span",
      { class: "g-cmp-pic" + (mineSrc ? " g-has-img" : " g-noimg"), role: "img", "aria-label": "내 사진" },
      [mineSrc ? h("img", { src: mineSrc, alt: "" }) : h("span", { text: "내 사진" })]
    );
    var art = workPic(w, "g-cmp-pic");
    art.setAttribute("role", "img");
    art.setAttribute("aria-label", str(w.label) + (safeImg(w.image) ? " 명화" : " (이미지 없음)"));
    cmpTop.replaceChildren(
      h("p", { class: "g-cmp-eyebrow", text: w.eyebrow }),
      h("h2", { class: "g-cmp-title", text: w.title }),
      h("div", { class: "g-cmp-pics" }, [mine, art, badge]),
      h("div", { class: "g-cmp-caps" }, [
        h("span", null, [h("b", { text: "내 사진" }), h("span", { text: c.kind_note })]),
        h("span", null, [h("b", { text: w.label }), h("span", { text: w.style })]),
      ])
    );
    return badge;
  }

  // 고른 명화로 위쪽 그림·유사도·대표색을 다시 그리고 유사도 올라가기를 다시 돌린다 (FR8.4, FR8.6).
  function showWork(i) {
    var v = st.view;
    var works = v.compare.works;
    st.cmpSel = Math.max(0, Math.min(works.length - 1, i));
    var w = works[st.cmpSel];
    var badge = renderCmpTop(v, w);
    cmpRefs.thumbs.forEach(function (b, k) {
      b.setAttribute("aria-pressed", k === st.cmpSel ? "true" : "false");
    });

    var mineP = v.compare.mine_palette;
    if (Array.isArray(w.palette) && Array.isArray(mineP)) {
      cmpRefs.pal.hidden = false;
      cmpRefs.pal.replaceChildren(
        h("b", { text: "대표색 비교" }),
        h("span", { class: "g-pal-row" }, [
          h("span", { class: "g-pal-name", text: "내 사진" }),
          swatches(mineP, "내 사진의 대표색 " + mineP.length + "개"),
        ]),
        h("span", { class: "g-pal-row" }, [
          h("span", { class: "g-pal-name", text: "이 명화" }),
          swatches(w.palette, "이 명화의 대표색 " + w.palette.length + "개"),
        ])
      );
    } else {
      cmpRefs.pal.hidden = true;
      cmpRefs.pal.replaceChildren();
    }

    var pct = Math.max(0, Math.min(100, num(w.pct)));
    runAnim(350, 900, function (p) {
      cmpRefs.num.textContent = Math.round(p * pct) + "%";
      cmpRefs.fill.style.width = (p * pct).toFixed(1) + "%";
      if (p >= 1) badge.setAttribute("data-show", "");
    });
  }

  function paneCompare(v, dir) {
    var works = v.compare.works;
    var simNum = h("span", { class: "g-sim-num", "data-testid": "g-sim" });
    var simFill = h("i");
    var pal = h("div", { class: "g-block g-pal", "data-testid": "g-palette" });
    var thumbs = works.map(function (w, i) {
      var pct = num(w.pct);
      return h(
        "button",
        {
          type: "button",
          class: "g-thumb",
          "data-testid": "g-work-" + i,
          "aria-label": str(w.label) + " 보기, 유사도 " + pct + "%",
          on: {
            click: function () {
              if (i === st.cmpSel) return;
              clearAnims();
              showWork(i);
            },
          },
        },
        [
          h("span", { class: "g-thumb-ring", "aria-hidden": "true" }, [workPic(w, "g-thumb-pic")]),
          h("span", { class: "g-thumb-cap", "aria-hidden": "true", text: str(w.short) + " · " + pct + "%" }),
        ]
      );
    });
    var kids = [
      h("div", { class: "g-sim" }, [
        h("span", { class: "g-sim-top" }, [h("b", { text: "CLIP 유사도" }), simNum]),
        h("span", { class: "g-track g-track-8", "aria-hidden": "true" }, [simFill]),
        h("span", { class: "g-small", text: "100%에 가까울수록 소재·분위기가 비슷해요." }),
      ]),
      pal,
    ];
    if (works.length > 1) {
      kids.push(
        h("div", { class: "g-block" }, [
          h("b", { text: "다른 명화와 비교" }),
          h("div", { class: "g-thumbs" }, thumbs),
        ])
      );
    }
    kids.push(h("div", { class: "g-spacer" }));
    kids.push(
      actions(
        ghostBtn("이전", "g-prev-result", goResult, "prev"),
        mainBtn("색·선 비교 보기", "g-to-why", goWhy, "next")
      )
    );
    setPane(kids, dir);
    cmpRefs = { num: simNum, fill: simFill, pal: pal, thumbs: thumbs };
    showWork(st.cmpSel);
  }

  function goCompare() {
    go("compare");
  }

  // --- 색·선 (FR4) -------------------------------------------------------------

  // 13px 축 이름의 대략적인 폭(굵게 표시될 때를 넉넉히 잡음). 한글 13.5, 공백 4, 그 밖의 문자 8.
  function labelWidth(text) {
    var w = 0;
    for (var i = 0; i < text.length; i++) {
      var ch = text.charCodeAt(i);
      w += ch === 32 ? 4 : ch < 128 ? 8 : 13.5;
    }
    return w;
  }

  // opt(선택): 비교 다각형을 바꿀 때 {cmp: [축별 값], near: [축 key], far: [축 key], name: 이름}.
  // 없으면 1위 평균(a.avg)과 a.near·a.far를 쓴다.
  function radarSvg(r, opt) {
    var axes = r.axes || [];
    opt = opt || null;
    var nearKeys = opt ? opt.near || [] : null;
    var farKeys = opt ? opt.far || [] : null;
    function isNear(a) {
      return nearKeys ? nearKeys.indexOf(a.key) >= 0 : !!a.near;
    }
    function isFar(a) {
      return farKeys ? farKeys.indexOf(a.key) >= 0 : !!a.far;
    }
    var n = axes.length;
    var cx = 156;
    var cy = 124;
    var R = 84;
    function theta(i) {
      return (i * 2 * Math.PI) / n;
    }
    function pt(i, val) {
      var t = theta(i);
      return [cx + R * val * Math.sin(t), cy - R * val * Math.cos(t)];
    }
    function pts(vals) {
      return vals
        .map(function (val, i) {
          var p = pt(i, Math.max(0, Math.min(1, num(val))));
          return p[0].toFixed(1) + "," + p[1].toFixed(1);
        })
        .join(" ");
    }
    function ring(k) {
      return axes.map(function () {
        return k;
      });
    }
    var mine = axes.map(function (a) {
      return a.mine;
    });
    var avg = opt && opt.cmp
      ? opt.cmp
      : axes.map(function (a) {
          return a.avg;
        });

    var kids = [
      sv("polygon", { points: pts(ring(1)), fill: "#14161C", "fill-opacity": "0.025", stroke: "#D9DCE2", "stroke-width": "1" }),
    ];
    [0.75, 0.5, 0.25].forEach(function (k) {
      kids.push(sv("polygon", { points: pts(ring(k)), fill: "none", stroke: "#E2E4E9", "stroke-width": "1" }));
    });
    kids.push(
      sv(
        "g",
        { stroke: "#E2E4E9", "stroke-width": "1" },
        axes.map(function (a, i) {
          var p = pt(i, 1);
          return sv("line", { x1: cx, y1: cy, x2: p[0].toFixed(1), y2: p[1].toFixed(1) });
        })
      )
    );
    kids.push(
      sv("polygon", {
        class: "cmp-poly",
        points: pts(avg),
        fill: "#1D4ED8",
        "fill-opacity": "0.08",
        stroke: "#1D4ED8",
        "stroke-width": "2",
        "stroke-dasharray": "5 4",
        "stroke-linejoin": "round",
      })
    );
    kids.push(
      sv("polygon", {
        class: "me-poly",
        pathLength: "1",
        points: pts(mine),
        fill: "#EA580C",
        "fill-opacity": "0.16",
        stroke: "#EA580C",
        "stroke-width": "2.2",
        "stroke-linejoin": "round",
      })
    );
    kids.push(
      sv(
        "g",
        { class: "me-dot", fill: "#EA580C", stroke: "#FFFFFF", "stroke-width": "1.5" },
        mine.map(function (val, i) {
          var p = pt(i, Math.max(0, Math.min(1, num(val))));
          return sv("circle", { cx: p[0].toFixed(1), cy: p[1].toFixed(1), r: "3.4" });
        })
      )
    );
    // 축 이름이 304 폭 밖으로 나가면(예: 스케치 5축의 "윤곽선 길이") 그만큼 viewBox를 넓힌다.
    var x0 = 0;
    var x1 = 304;
    kids.push(
      sv(
        "g",
        { "font-family": "Noto Sans KR, sans-serif", "font-size": "13" },
        axes.map(function (a, i) {
          var t = theta(i);
          var s = Math.sin(t);
          var c = Math.cos(t);
          var cls = isNear(a) ? "rl rl-near" : isFar(a) ? "rl rl-far" : "rl";
          var x = cx + 104 * s;
          var w = labelWidth(str(a.label));
          var anchor = Math.abs(s) < 0.01 ? "middle" : s > 0 ? "start" : "end";
          var left = anchor === "middle" ? x - w / 2 : anchor === "start" ? x : x - w;
          x0 = Math.min(x0, Math.floor(left - 4));
          x1 = Math.max(x1, Math.ceil(left + w + 4));
          return sv("text", {
            class: cls,
            x: x.toFixed(1),
            y: (cy - 104 * c + 5 * (1 - c)).toFixed(1),
            "text-anchor": anchor,
            text: a.label,
          });
        })
      )
    );
    return sv(
      "svg",
      {
        class: "g-radar",
        width: String(x1 - x0),
        height: "250",
        viewBox: x0 + " 0 " + (x1 - x0) + " 250",
        role: "img",
        "aria-label":
          "색·선 특징 " +
          n +
          "가지를 비교한 레이더 차트: 내 이미지와 " +
          (opt && opt.name ? str(opt.name) : str(r.artist) + " 평균"),
      },
      kids
    );
  }

  function joinOrNone(list) {
    return list && list.length ? list.map(str).join(" · ") : "해당 없음";
  }

  function paneWhy(v, dir) {
    var r = v.radar || {};
    var n = (r.axes || []).length;
    var artist = str(r.artist);
    var kids = [
      h("h1", { class: "g-title g-mt12", text: "왜 " + artist + "일까요?" }),
      h("p", {
        class: "g-sub",
        text: v.gray
          ? "스케치라서 색을 빼고 선 특징 " + n + "가지로 비교했어요."
          : "색과 선을 " + n + "가지로 재서 비교했어요.",
      }),
    ];
    // 고른 명화의 특징이 있으면 "○○ 평균과"·명화 탭(workTabLabel) (FR4.6). 없으면 탭을 숨긴다.
    var w = selWork();
    var canWork = !!(w && w.radar && typeof w.radar === "object" && n >= 3);
    if (!canWork) st.whyMode = "avg";
    var tabs = null;
    if (canWork) {
      tabs = {
        avg: h("button", {
          type: "button",
          class: "g-tab",
          role: "tab",
          "data-testid": "g-tab-avg",
          text: artist + " 평균과",
          on: {
            click: function () {
              setWhyMode("avg");
            },
          },
        }),
        work: h("button", {
          type: "button",
          class: "g-tab",
          role: "tab",
          "data-testid": "g-tab-work",
          text: workTabLabel(w),
          on: {
            click: function () {
              setWhyMode("work");
            },
          },
        }),
      };
      kids.push(h("div", { class: "g-tabs", role: "tablist", "aria-label": "비교 대상" }, [tabs.avg, tabs.work]));
    }
    var parts = whyParts(v);
    kids.push(parts.radar, parts.legend, parts.cards);
    kids.push(
      h("p", {
        class: "g-small g-mt10 g-after3",
        text: "바깥쪽일수록 값이 커요. 스케치는 색을 빼고 선 5가지만 비교해요.",
      })
    );
    kids.push(h("div", { class: "g-spacer g-after4" }));
    var back = hasCompare(v)
      ? ghostBtn("이전", "g-prev", goCompare, "prev")
      : ghostBtn("이전", "g-prev", goResult, "prev");
    var acts = actions(back, mainBtn("화풍 보기", "g-to-more", goMore, "next"));
    acts.classList.add("g-after4");
    kids.push(acts);
    // 레이더 그리기와 축 강조, 그 뒤 아래 정보 (FR4.3). 애니메이션 줄이기면 최종 상태만.
    setPane(kids, dir, reduced() ? "" : "g-why");
    whyRefs = { parts: parts, tabs: tabs };
    markTabs();
    st.tabSeen[whyKey()] = true;
    introRadar(parts.radar);
  }

  var whyRefs = null;

  function whyKey() {
    return st.whyMode === "work" ? "work:" + st.cmpSel : "avg";
  }

  function markTabs() {
    if (!whyRefs || !whyRefs.tabs) return;
    whyRefs.tabs.avg.setAttribute("aria-selected", st.whyMode === "avg" ? "true" : "false");
    whyRefs.tabs.work.setAttribute("aria-selected", st.whyMode === "work" ? "true" : "false");
  }

  function introRadar(radar) {
    if (!radar || reduced() || radar.tagName.toLowerCase() !== "svg") return;
    radar.classList.add("intro");
    later(2700, function () {
      radar.classList.remove("intro");
    });
  }

  // 레이더·범례·카드. 비교 대상(1위 평균 또는 고른 명화)에 맞춰 만든다.
  function whyParts(v) {
    var r = v.radar || {};
    var axes = r.axes || [];
    var artist = str(r.artist);
    var w = selWork();
    var useWork = st.whyMode === "work" && w && w.radar && typeof w.radar === "object";
    var opt = useWork
      ? {
          cmp: axes.map(function (a) {
            return num(w.radar[a.key]);
          }),
          near: Array.isArray(w.near_keys) ? w.near_keys : [],
          far: Array.isArray(w.far_keys) ? w.far_keys : [],
          name: str(w.label),
        }
      : null;
    var radar =
      axes.length >= 3
        ? radarSvg(r, opt)
        : h("p", { class: "g-small g-mt12", text: "비교할 수 있는 특징이 부족해 그래프를 그리지 않았어요." });
    var legend = h("div", { class: "g-legend g-after1" }, [
      h("span", null, [icon("legendMe"), "내 이미지"]),
      h("span", null, [icon("legendAvg"), useWork ? str(w.label) : artist + " 평균"]),
    ]);
    var cards = h("div", { class: "g-cards g-after2", "data-testid": "g-why-cards" }, [
      h("div", { class: "g-card near" }, [
        h("b", { text: useWork ? "이 명화와 비슷한 특징" : artist + " 평균에 가까운 특징" }),
        h("span", { text: joinOrNone(useWork ? w.near : r.near) }),
      ]),
      h("div", { class: "g-card far" }, [
        h("b", { text: useWork ? "이 명화와 다른 특징" : (str(r.artist2) || "2위") + " 쪽에 가까운 특징" }),
        h("span", { text: joinOrNone(useWork ? w.far : r.far) }),
      ]),
    ]);
    return { radar: radar, legend: legend, cards: cards };
  }

  // 탭 전환 (FR4.6, FR4.7). 처음 보는 탭이면 그리기 움직임 뒤 차례로, 이미 본 탭이면 바로.
  function setWhyMode(mode) {
    if (!whyRefs || st.step !== "why" || mode === st.whyMode) return;
    st.whyMode = mode;
    markTabs();
    var key = whyKey();
    var animate = !st.tabSeen[key] && !reduced();
    st.tabSeen[key] = true;
    clearAnims();
    var old = whyRefs.parts;
    var next = whyParts(st.view);
    ["radar", "legend", "cards"].forEach(function (k) {
      if (!animate) next[k].classList.add("g-now");
      if (old[k].parentNode) old[k].parentNode.replaceChild(next[k], old[k]);
    });
    whyRefs.parts = next;
    if (animate) introRadar(next.radar);
  }

  // --- 화풍 (FR5) --------------------------------------------------------------

  function paneMore(v, dir) {
    var fills = [];
    var styles = (v.styles || []).map(function (s) {
      var fill = h("i");
      fills.push([fill, Math.max(0, Math.min(100, num(s.pct)))]);
      return h("div", { class: "g-style" }, [
        h("span", { class: "g-style-top" }, [
          h("span", { text: s.name }),
          h("em", { text: s.name_orig }),
          h("span", { text: num(s.pct) + "%" }),
        ]),
        h("span", { class: "g-track", "aria-hidden": "true" }, [fill]),
      ]);
    });
    var kids = [
      h("h1", { class: "g-title g-mt12", text: "닮은 화풍과 표현" }),
      h("p", { class: "g-sub", text: "CLIP이 본 화풍과 이미지에서 읽은 표현이에요." }),
      h("div", { class: "g-styles" }, styles),
    ];
    var kws = v.keywords || [];
    if (kws.length) {
      kids.push(
        h("div", { class: "g-block" }, [
          h("b", { text: "이미지에서 읽은 표현" }),
          h(
            "div",
            { class: "g-chips" },
            kws.map(function (k) {
              return h("span", { text: k });
            })
          ),
        ])
      );
    }
    kids.push(
      h("div", { class: "g-block" }, [
        h("b", { text: "자세한 수치" }),
        h(
          "div",
          { class: "g-metrics" },
          (v.metrics || []).map(function (m) {
            return h("span", null, [
              h("span", { class: "g-m-label", text: m.label }),
              h("span", { class: "g-m-value", text: num(m.value).toFixed(2) }),
              h("span", { class: "g-m-note", text: m.note }),
            ]);
          })
        ),
      ])
    );
    kids.push(
      h("p", { class: "g-small g-mt14", text: str(v.disclaimer || DISCLAIMER) + " " + str(v.source) })
    );
    kids.push(h("div", { class: "g-spacer" }));
    kids.push(
      actions(
        ghostBtn("처음으로", "g-first", goResult),
        mainBtn("다른 이미지로 해 보기", "g-again", goHome, "camera", true)
      )
    );
    setPane(kids, dir);
    runAnim(450, 900, function (p) {
      fills.forEach(function (f) {
        f[0].style.width = (p * f[1]).toFixed(1) + "%";
      });
    });
  }

  // --- 기록 저장 (FR9.1, FR9.10, NFR6) ----------------------------------------------

  // 저장소를 쓸 수 없는 브라우저(차단·사생활 모드 등)에서는 null. 접근 자체가 예외를 낼 수 있다.
  function storage() {
    try {
      return window.localStorage || null;
    } catch (e) {
      return null;
    }
  }

  function validEntry(e) {
    return !!(
      e &&
      typeof e === "object" &&
      typeof e.id === "string" &&
      typeof e.t === "number" &&
      isFinite(e.t) &&
      e.view &&
      typeof e.view === "object" &&
      e.view.head &&
      typeof e.view.head === "object" &&
      e.view.level &&
      typeof e.view.level === "object"
    );
  }

  function writeHist(items) {
    var s = storage();
    if (!s) return false;
    try {
      s.setItem(HIST_KEY, JSON.stringify(items));
      return true;
    } catch (e) {
      console.warn("[g] 기록을 저장하지 못했습니다:", e && e.name);
      return false;
    }
  }

  // {ok: 저장소를 쓸 수 있는지, items: 최신 순 기록}. 깨진 기록은 버리고 나머지만 돌려준다.
  function readHist() {
    var s = storage();
    if (!s) return { ok: false, items: [] };
    var raw;
    try {
      raw = s.getItem(HIST_KEY);
    } catch (e) {
      return { ok: false, items: [] };
    }
    if (!raw) return { ok: true, items: [] };
    var arr;
    try {
      arr = JSON.parse(raw);
    } catch (e) {
      console.warn("[g] 읽을 수 없는 기록을 버립니다.");
      arr = null;
    }
    if (!Array.isArray(arr)) {
      writeHist([]);
      return { ok: true, items: [] };
    }
    var good = arr.filter(validEntry).slice(0, HIST_MAX);
    if (good.length !== arr.length) {
      console.warn("[g] 깨진 기록 " + (arr.length - good.length) + "개를 버립니다.");
      writeHist(good);
    }
    return { ok: true, items: good };
  }

  function loadImg(src) {
    return new Promise(function (resolve) {
      if (!src) {
        resolve(null);
        return;
      }
      var im = new Image();
      im.onload = function () {
        resolve(im.naturalWidth ? im : null);
      };
      im.onerror = function () {
        resolve(null);
      };
      im.src = src;
    });
  }

  // 이미지를 긴 변 side px 이하 JPEG data URL로 줄인다. 실패하면 "".
  function shrink(im, side, quality) {
    if (!im) return "";
    try {
      var w = im.naturalWidth;
      var hgt = im.naturalHeight;
      var k = Math.min(1, side / Math.max(w, hgt));
      var c = document.createElement("canvas");
      c.width = Math.max(1, Math.round(w * k));
      c.height = Math.max(1, Math.round(hgt * k));
      c.getContext("2d").drawImage(im, 0, 0, c.width, c.height);
      return safeImg(c.toDataURL("image/jpeg", quality));
    } catch (e) {
      return "";
    }
  }

  // 결과 화면 데이터를 기록용으로 복사한다. 명화 이미지는 긴 변 96px로 줄인다.
  function slimView(view) {
    var copy = JSON.parse(JSON.stringify(view));
    var works = hasCompare(copy) ? copy.compare.works : [];
    return Promise.all(
      works.map(function (w) {
        return loadImg(safeImg(w.image)).then(function (im) {
          w.image = shrink(im, HIST_WORK_PX, 0.72) || null;
        });
      })
    ).then(function () {
      return copy;
    });
  }

  function saveHistory(view) {
    var src = photo.getAttribute("src") || "";
    var head = view.head || {};
    var level = view.level || {};
    Promise.all([loadImg(src), slimView(view)])
      .then(function (res) {
        var entry = {
          id: Date.now().toString(36) + Math.random().toString(36).slice(2, 7),
          t: Date.now(),
          kind: KINDS.indexOf(view.kind) > 0 ? view.kind : "사진",
          name: str(view.history_name || head.name),
          pct: view.low ? null : Math.round(num(head.pct)),
          level: str(level.label),
          thumb: shrink(res[0], HIST_THUMB_PX, 0.78),
          view: res[1],
        };
        var cur = readHist();
        if (!cur.ok) {
          toast("이 브라우저에서는 기록을 저장할 수 없어요. 결과는 그대로 볼 수 있어요.");
          return;
        }
        if (!writeHist([entry].concat(cur.items).slice(0, HIST_MAX))) {
          toast("저장 공간이 부족해 기록을 저장하지 못했어요.");
        }
      })
      .catch(function (err) {
        console.warn("[g] 기록을 만들지 못했습니다:", err);
        toast("기록을 저장하지 못했어요. 결과는 그대로 볼 수 있어요.");
      });
  }

  // --- 기록 화면 (FR9.2–FR9.9) ---------------------------------------------------------

  function pad2(n) {
    return (n < 10 ? "0" : "") + n;
  }

  function dayLabel(t) {
    var d = new Date(t);
    var now = new Date();
    var start = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    if (t >= start) return "오늘";
    if (t >= start - 86400000) return "어제";
    var md = d.getMonth() + 1 + "월 " + d.getDate() + "일";
    return d.getFullYear() === now.getFullYear() ? md : d.getFullYear() + "년 " + md;
  }

  function timeLabel(t) {
    var d = new Date(t);
    var hr = d.getHours();
    return (hr < 12 ? "오전 " : "오후 ") + (hr % 12 || 12) + ":" + pad2(d.getMinutes());
  }

  function openHistory() {
    if (st.step !== "home" || st.closing) return;
    stopCamera();
    clearAnims();
    var r = readHist();
    st.hist = r.items;
    st.histFilter = "전체";
    setStep("history");
    paneHistory(true);
    if (!r.ok) toast("이 브라우저에서는 기록을 쓸 수 없어요.");
  }

  function paneHistory(intro) {
    var items = st.hist;
    var kids = [
      h("div", { class: "g-hhead" }, [
        h("h1", { class: "g-title", text: "지난 분석" }),
        h("span", { class: "g-hcount", "data-testid": "g-hist-count", text: items.length ? items.length + "개" : "" }),
      ]),
    ];
    if (!items.length) {
      kids.push(
        h("div", { class: "g-hempty", "data-testid": "g-hist-empty" }, [
          h("span", { class: "g-hempty-icon", "aria-hidden": "true" }, [icon("historyDark")]),
          h("b", { text: "아직 기록이 없어요" }),
          h("span", { text: "분석한 결과가 여기에 쌓여요." }),
        ])
      );
      kids.push(h("div", { class: "g-actions" }, [
        mainBtn("사진 찍으러 가기", "g-hist-empty-go", goHome, "camera", true),
      ]));
      setPane(kids, "none", "g-hist" + (intro ? "" : " g-static"));
      return;
    }
    var chips = KINDS.map(function (k, i) {
      return h("button", {
        type: "button",
        class: "g-hchip",
        role: "tab",
        "aria-selected": k === st.histFilter ? "true" : "false",
        "data-testid": "g-hist-chip-" + i,
        text: k,
        on: {
          click: function () {
            if (st.histFilter === k || st.removing) return;
            st.histFilter = k;
            paneHistory(false);
          },
        },
      });
    });
    kids.push(h("div", { class: "g-hchips", role: "tablist", "aria-label": "종류로 거르기" }, chips));

    var list = h("div", { class: "g-hlist", "data-testid": "g-hist-list" });
    var lastDay = null;
    items.forEach(function (e, idx) {
      if (st.histFilter !== "전체" && e.kind !== st.histFilter) return;
      var day = dayLabel(e.t);
      if (day !== lastDay) {
        list.appendChild(h("h2", { class: "g-hday", text: day }));
        lastDay = day;
      }
      list.appendChild(histRow(e, idx));
    });
    if (lastDay === null) {
      list.appendChild(h("p", { class: "g-small g-mt14", text: "이 종류의 기록이 없어요." }));
    }
    kids.push(list);
    kids.push(
      h("div", { class: "g-hfoot" }, [
        h("span", { class: "g-small", text: "기록은 이 브라우저에만 저장돼요." }),
        h("button", {
          type: "button",
          class: "g-hclear",
          "data-testid": "g-hist-clear",
          text: "모두 지우기",
          on: { click: openConfirm },
        }),
      ])
    );
    setPane(kids, "none", "g-hist" + (intro ? "" : " g-static"));
  }

  function histRow(e, idx) {
    var name = str(e.name);
    var kind = str(e.kind);
    var time = timeLabel(e.t);
    var pct = e.pct === null || e.pct === undefined ? "—" : Math.round(num(e.pct)) + "%";
    var level = str(e.level);
    var thumbSrc = safeImg(e.thumb);
    var item = h(
      "button",
      {
        type: "button",
        class: "g-hitem",
        "data-testid": "g-hist-row-" + idx,
        "aria-label": name + ", " + kind + " · " + time + ", " + pct + ", 신뢰 " + level + ". 결과 열기",
      },
      [
        h("span", { class: "g-hthumb", "aria-hidden": "true" }, thumbSrc ? [h("img", { src: thumbSrc, alt: "" })] : []),
        h("span", { class: "g-hbody", "aria-hidden": "true" }, [
          h("span", { class: "g-hname", text: name }),
          h("span", { class: "g-hmeta", text: kind + " · " + time }),
        ]),
        h("span", { class: "g-hside", "aria-hidden": "true" }, [
          h("span", { class: "g-hpct", text: pct }),
          h("span", { class: "g-hlevel", "data-level": level, text: "신뢰 " + level }),
        ]),
        icon("chevron"),
      ]
    );
    var del = h("span", { class: "g-hdel", "aria-hidden": "true" }, [icon("trash"), "삭제"]);
    var row = h("div", { class: "g-hrow" }, [
      del,
      item,
      h("button", {
        type: "button",
        class: "g-sr",
        "aria-label": name + " 기록 지우기",
        "data-testid": "g-hist-del-" + idx,
        text: "삭제",
        on: {
          click: function () {
            removeEntry(e.id, -1, row, item);
          },
        },
      }),
    ]);
    attachSwipe(row, item, e);
    return row;
  }

  // 행을 좌우로 110px 넘게 밀어 놓으면 지우고, 덜 밀면 제자리 (FR9.3). 마우스도 같다.
  function attachSwipe(row, item, e) {
    var d = null;
    var moved = false;
    item.addEventListener("pointerdown", function (ev) {
      if (st.removing) return;
      if (ev.pointerType === "mouse" && ev.button !== 0) return;
      d = { x0: ev.clientX, y0: ev.clientY, dx: 0, active: false, pid: ev.pointerId };
      moved = false;
    });
    item.addEventListener("pointermove", function (ev) {
      if (!d) return;
      var dx = ev.clientX - d.x0;
      var dy = ev.clientY - d.y0;
      if (!d.active) {
        if (Math.abs(dx) < 8 || Math.abs(dx) < Math.abs(dy)) return;
        d.active = true;
        try {
          item.setPointerCapture(d.pid);
        } catch (err) {
          /* 캡처를 못 해도 밀기는 된다 */
        }
        row.setAttribute("data-dragging", "");
      }
      d.dx = dx;
      item.style.transform = "translateX(" + dx + "px)";
      row.setAttribute("data-dir", dx > 0 ? "right" : "left");
      if (Math.abs(dx) > SWIPE_PX) row.setAttribute("data-armed", "");
      else row.removeAttribute("data-armed");
    });
    function end(cancel) {
      var x = d;
      d = null;
      if (!x || !x.active) return;
      moved = true;
      row.removeAttribute("data-dragging");
      if (!cancel && Math.abs(x.dx) > SWIPE_PX) {
        removeEntry(e.id, x.dx > 0 ? 1 : -1, row, item);
      } else {
        item.style.transform = "";
        row.removeAttribute("data-armed");
      }
    }
    item.addEventListener("pointerup", function () {
      end(false);
    });
    item.addEventListener("pointercancel", function () {
      end(true);
    });
    item.addEventListener("click", function (ev) {
      if (moved) {
        moved = false;
        ev.preventDefault();
        return;
      }
      openEntry(e);
    });
  }

  function removeEntry(id, dir, row, item) {
    if (st.removing || st.step !== "history") return;
    st.removing = true;
    row.setAttribute("data-dir", dir > 0 ? "right" : "left");
    row.setAttribute("data-armed", "");
    row.setAttribute("data-removing", "");
    item.style.transform = "translateX(" + (dir > 0 ? 110 : -110) + "%)";
    setTimeout(
      function () {
        st.removing = false;
        if (st.step !== "history") return;
        var idx = -1;
        st.hist.forEach(function (x, i) {
          if (x.id === id) idx = i;
        });
        if (idx < 0) return;
        var entry = st.hist.splice(idx, 1)[0];
        if (!writeHist(st.hist)) toast("브라우저 저장소에 반영하지 못했어요.");
        paneHistory(false);
        showUndo(entry, idx);
      },
      reduced() ? 0 : 480
    );
  }

  function showUndo(entry, idx) {
    st.undo = { entry: entry, idx: idx };
    undoText.textContent = "기록을 지웠어요";
    undoEl.setAttribute("data-show", "");
    clearTimeout(st.undoT);
    st.undoT = setTimeout(hideUndo, UNDO_MS);
  }

  function hideUndo() {
    clearTimeout(st.undoT);
    st.undo = null;
    undoEl.removeAttribute("data-show");
    undoText.textContent = "";
  }

  undoBtn.addEventListener("click", function () {
    var u = st.undo;
    if (!u || st.step !== "history") return;
    hideUndo();
    st.hist.splice(Math.min(u.idx, st.hist.length), 0, u.entry);
    if (!writeHist(st.hist)) toast("브라우저 저장소에 반영하지 못했어요.");
    paneHistory(false);
  });

  // 모두 지우기 확인 창 (FR9.5). 지우기를 눌렀을 때만 지운다.
  function openConfirm() {
    if (st.step !== "history" || !st.hist.length) return;
    dlgBody.textContent = "기록 " + st.hist.length + "개가 모두 사라지고, 지운 기록은 되돌릴 수 없어요.";
    dlgBack.hidden = false;
    dlgCancel.focus();
  }

  function closeConfirm(restoreFocus) {
    if (dlgBack.hidden) return;
    dlgBack.hidden = true;
    if (restoreFocus) {
      var b = pane.querySelector("[data-testid=g-hist-clear]");
      if (b) b.focus();
    }
  }

  dlgCancel.addEventListener("click", function () {
    closeConfirm(true);
  });
  dlgOk.addEventListener("click", function () {
    closeConfirm(false);
    hideUndo();
    st.hist = [];
    var s = storage();
    var ok = false;
    try {
      if (s) {
        s.removeItem(HIST_KEY);
        ok = true;
      }
    } catch (e) {
      ok = false;
    }
    if (!ok) toast("브라우저 저장소에 반영하지 못했어요.");
    paneHistory(false);
  });
  dlgBack.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape") {
      ev.preventDefault();
      closeConfirm(true);
    } else if (ev.key === "Tab") {
      // 창 안의 두 버튼 사이에서만 움직인다.
      ev.preventDefault();
      (document.activeElement === dlgCancel ? dlgOk : dlgCancel).focus();
    }
  });
  dlgBack.addEventListener("click", function (ev) {
    if (ev.target === dlgBack) closeConfirm(true);
  });

  // 저장된 화면 데이터로 결과 페이지를 연다. 분석을 다시 하지 않는다 (FR9.6).
  function openEntry(e) {
    if (st.closing || st.removing || st.step !== "history") return;
    if (!e.view || typeof e.view !== "object") return;
    hideUndo();
    closeConfirm(false);
    clearPhoto();
    var src = safeImg(e.thumb);
    if (src) {
      photo.src = src;
      setBg("photo");
    }
    st.view = e.view;
    resetViewState();
    go("result");
  }

  // --- 사용자 입력 연결 -----------------------------------------------------------

  shutterBtn.addEventListener("click", function () {
    if (cameraReady()) capture();
    else openPicker();
  });
  albumBtn.addEventListener("click", openPicker);
  histBtn.addEventListener("click", openHistory);
  fileInput.addEventListener("change", function () {
    var f = fileInput.files && fileInput.files[0];
    fileInput.value = ""; // 같은 파일을 다시 골라도 change가 오게
    if (f) startAnalysis(f);
  });
  logoBtn.addEventListener("click", goHome);
  segBtns.forEach(function (b) {
    b.addEventListener("click", function () {
      go(b.getAttribute("data-go"));
    });
  });

  // 시트 손잡이를 120px 넘게 끌어 놓으면 첫 화면, 덜 끌면 제자리 (FR6.4)
  handle.addEventListener("pointerdown", function (e) {
    if (st.closing || st.step === "home") return;
    st.drag = { y0: e.clientY, dy: 0 };
    try {
      handle.setPointerCapture(e.pointerId);
    } catch (err) {
      /* 포인터 캡처를 못 해도 끌기는 된다 */
    }
    sheet.classList.add("g-dragging");
  });
  handle.addEventListener("pointermove", function (e) {
    if (!st.drag) return;
    st.drag.dy = Math.max(0, e.clientY - st.drag.y0);
    sheet.style.transform = "translateY(" + st.drag.dy + "px)";
  });
  function endDrag() {
    var d = st.drag;
    st.drag = null;
    if (!d) return;
    sheet.classList.remove("g-dragging");
    sheet.style.transform = "";
    if (d.dy > DRAG_CLOSE_PX) goHome();
  }
  handle.addEventListener("pointerup", endDrag);
  handle.addEventListener("pointercancel", endDrag);

  // 다른 탭으로 가면 카메라를 끄고, 돌아오면 첫 화면에서만 다시 켠다.
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") stopCamera();
    else if (st.step === "home") startCamera();
  });

  window.gApp = { update: update };
  setStep("home");
  startCamera();
})();
