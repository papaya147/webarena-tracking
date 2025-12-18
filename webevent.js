const BATCH_INTERVAL_MS = 500;
const MAX_BATCH_SIZE = 50;

const EVENT_CONFIG = {
  mousemove: { capture: true },
  scroll: { capture: true },
  resize: { capture: true },
  click: { capture: true },
  keydown: { capture: true },
  input: { capture: true },
  change: { capture: true },
  submit: { capture: true },
  paste: { capture: true },
};

let eventBuffer = [];
let batchTimer = null;

window.recordEvent = (data) => {
  if (window.log_event_py) {
    window.log_event_py(data);
  }
};

const flushBuffer = () => {
  if (eventBuffer.length === 0) return;

  window.recordEvent([...eventBuffer]);

  eventBuffer = [];
  clearTimeout(batchTimer);
  batchTimer = null;
};

const queueEvent = (eventData) => {
  eventBuffer.push(eventData);

  if (eventBuffer.length >= MAX_BATCH_SIZE) {
    flushBuffer();
  } else if (!batchTimer) {
    batchTimer = setTimeout(flushBuffer, BATCH_INTERVAL_MS);
  }
};

const getXPath = (element) => {
  if (!element || element.nodeType !== 1) return "";
  if (element.id) return `//*[@id="${element.id}"]`;

  const parts = [];
  while (element && element.nodeType === 1) {
    let index = 0;
    let sibling = element.previousSibling;
    while (sibling) {
      if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
        index++;
      }
      sibling = sibling.previousSibling;
    }
    const tagName = element.tagName.toLowerCase();
    const pathIndex = index > 0 ? `[${index + 1}]` : "";
    parts.unshift(`${tagName}${pathIndex}`);
    element = element.parentNode;
  }
  return parts.length ? "/" + parts.join("/") : "";
};

Object.keys(EVENT_CONFIG).forEach((eventType) => {
  const config = EVENT_CONFIG[eventType];

  window.addEventListener(
    eventType,
    (e) => {
      const path = e.composedPath ? e.composedPath() : [];
      const trueTarget = path[0] || e.target;
      const targetElement =
        trueTarget instanceof Element ? trueTarget : trueTarget.parentElement;

      let cursor = "auto";
      if (targetElement) {
        try {
          cursor = window.getComputedStyle(targetElement).cursor;
        } catch (err) {}
      }

      const baseData = {
        type: eventType,
        url: window.location.href,
        title: document.title,
        client_timestamp: Date.now(),
        cursor: cursor,
        target_tag: targetElement ? targetElement.tagName : "",
        target_id: targetElement ? targetElement.id : "",
        target_xpath: getXPath(targetElement),
      };

      let extraData = {};
      if (e.type === "click" || e.type === "mousemove") {
        extraData = { x: e.clientX, y: e.clientY };
      } else if (e.type === "scroll") {
        extraData = { scroll_x: window.scrollX, scroll_y: window.scrollY };
      } else if (e.type === "keydown") {
        extraData = {
          key: e.key,
          code: e.code,
          modifiers: {
            ctrl: e.ctrlKey,
            alt: e.altKey,
            shift: e.shiftKey,
            meta: e.metaKey,
          },
        };
      } else if (["input", "change", "paste"].includes(e.type)) {
        extraData.value = e.target.value;
        extraData.input_type = e.target.type;

        if (e.target.type === "checkbox" || e.target.type === "radio") {
          extraData.checked = e.target.checked;
        }

        if (e.target.tagName === "SELECT") {
          const idx = e.target.selectedIndex;
          if (idx !== -1) {
            extraData.selected_text = e.target.options[idx].text;
          }
          if (e.target.type === "select-multiple") {
            extraData.selected_values = Array.from(
              e.target.selectedOptions
            ).map((o) => o.value);
            extraData.selected_texts = Array.from(e.target.selectedOptions).map(
              (o) => o.text
            );
          }
        }
      }

      queueEvent({ ...baseData, ...extraData });
    },
    { capture: config.capture }
  );
});

window.addEventListener("beforeunload", flushBuffer);
