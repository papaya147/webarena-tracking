window.recordEvent = (data) => {
  if (window.log_event_py) {
    data = {
      ...data,
      url: window.location.href,
      title: document.title,
      viewport: { w: window.innerWidth, h: window.innerHeight },
    };
    window.log_event_py(data);
  }
};

const getModifiers = (e) => ({
  ctrl: e.ctrlKey,
  alt: e.altKey,
  shift: e.shiftKey,
  cmd: e.metaKey,
});

window.addEventListener(
  "keydown",
  (e) => {
    if (["Control", "Shift", "Alt", "Meta"].includes(e.key)) return;

    let parts = [];
    if (e.ctrlKey) parts.push("Ctrl");
    if (e.altKey) parts.push("Alt");
    if (e.shiftKey) parts.push("Shift");
    if (e.metaKey) parts.push("Cmd");

    parts.push(e.key.length === 1 ? e.key.toUpperCase() : e.key);

    window.recordEvent({
      type: "keydown",
      key: e.key,
      code: e.code,
      combo: parts.join("+"),
      modifiers: getModifiers(e),
    });
  },
  { capture: true }
);

window.addEventListener(
  "click",
  (e) => {
    window.recordEvent({
      type: "click",
      x: e.clientX,
      y: e.clientY,
      pageX: e.pageX,
      pageY: e.pageY,
      scrollX: window.scrollX,
      scrollY: window.scrollY,
      modifiers: getModifiers(e),
      target_tag: e.target.tagName,
      target_id: e.target.id,
      target_text: e.target.innerText
        ? e.target.innerText.substring(0, 50)
        : "",
    });
  },
  { capture: true }
);

let scrollBuffer = [];

let lastX = window.scrollX;
let lastY = window.scrollY;

function trackScroll() {
  const currX = window.scrollX;
  const currY = window.scrollY;

  if (currX !== lastX || currY !== lastY) {
    scrollBuffer.push({
      t: Date.now(),
      x: currX,
      y: currY,
    });
    lastX = currX;
    lastY = currY;
  }
  requestAnimationFrame(trackScroll);
}
requestAnimationFrame(trackScroll);

setInterval(() => {
  if (scrollBuffer.length > 0) {
    window.recordEvent({
      type: "scroll_batch",
      samples: scrollBuffer,
    });
    scrollBuffer = [];
  }
}, 50);

let hoverTimer;
window.addEventListener(
  "mouseover",
  (e) => {
    const t = e.target;
    clearTimeout(hoverTimer);
    hoverTimer = setTimeout(() => {
      window.recordEvent({
        type: "hover",
        x: e.clientX,
        y: e.clientY,
        target_tag: t.tagName,
        target_text: t.innerText ? t.innerText.substring(0, 30) : "",
      });
    }, 500);
  },
  { capture: true }
);

window.addEventListener("mouseout", () => clearTimeout(hoverTimer), {
  capture: true,
});

window.addEventListener("focus", () => {
  window.recordEvent({ type: "tab_focus" });
});
