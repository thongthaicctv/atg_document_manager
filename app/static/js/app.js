document.addEventListener("submit", function (event) {
  const form = event.target;
  const message = form.getAttribute("data-confirm");
  if (message && !window.confirm(message)) {
    event.preventDefault();
  }
});

function formatFileSize(bytes) {
  if (!Number.isFinite(bytes)) {
    return "";
  }
  if (bytes < 1024) {
    return bytes + " B";
  }
  if (bytes < 1024 * 1024) {
    return (bytes / 1024).toFixed(1) + " KB";
  }
  return (bytes / 1024 / 1024).toFixed(1) + " MB";
}

function renderCaptureList(container, files) {
  const count = container.querySelector("[data-capture-count]");
  const list = container.querySelector("[data-capture-list]");
  const clearButton = container.querySelector("[data-capture-clear]");
  const unit = container.getAttribute("data-capture-unit") || "ảnh";
  const emptyText = container.getAttribute("data-capture-empty") || "Chưa có ảnh nào";

  if (count) {
    count.textContent = files.length ? files.length + " " + unit + " đã chọn" : emptyText;
  }
  if (clearButton) {
    clearButton.disabled = files.length === 0;
  }
  if (!list) {
    return;
  }

  list.replaceChildren();
  files.forEach(function (file, index) {
    const item = document.createElement("div");
    item.className = "captured-file-item";

    const name = document.createElement("span");
    name.className = "captured-file-name";
    name.textContent = index + 1 + ". " + file.name;

    const size = document.createElement("span");
    size.className = "captured-file-size";
    size.textContent = formatFileSize(file.size);

    item.append(name, size);
    list.append(item);
  });
}

function getCapturedFiles(container) {
  const holder = container.querySelector("[data-capture-holder]");
  if (!holder) {
    return [];
  }

  return Array.from(holder.querySelectorAll("input[type='file']")).flatMap(function (input) {
    return Array.from(input.files || []);
  });
}

function createCaptureInput() {
  const input = document.createElement("input");
  input.className = "form-control capture-camera-input";
  input.type = "file";
  input.accept = "image/*";
  input.setAttribute("capture", "environment");
  input.multiple = true;
  input.setAttribute("data-capture-input", "");
  return input;
}

function wireCaptureInput(container, picker) {
  picker.addEventListener("change", function () {
    const selectedFiles = Array.from(picker.files || []);
    if (selectedFiles.length === 0) {
      return;
    }

    const holder = container.querySelector("[data-capture-holder]");
    const actions = container.querySelector(".capture-actions");
    if (!holder || !actions) {
      return;
    }

    picker.name = container.getAttribute("data-capture-field-name") || "files";
    picker.removeAttribute("data-capture-input");
    picker.className = "visually-hidden";
    holder.appendChild(picker);

    const nextPicker = createCaptureInput();
    actions.insertBefore(nextPicker, actions.firstElementChild);
    wireCaptureInput(container, nextPicker);
    renderCaptureList(container, getCapturedFiles(container));
  });
}

function initMultiCapture(container) {
  const picker = container.querySelector("[data-capture-input]");
  const holder = container.querySelector("[data-capture-holder]");
  const clearButton = container.querySelector("[data-capture-clear]");
  if (!picker || !holder) {
    return;
  }

  wireCaptureInput(container, picker);

  if (clearButton) {
    clearButton.addEventListener("click", function () {
      holder.replaceChildren();
      renderCaptureList(container, []);
    });
  }

  renderCaptureList(container, []);
}

document.querySelectorAll("[data-multi-capture]").forEach(initMultiCapture);
